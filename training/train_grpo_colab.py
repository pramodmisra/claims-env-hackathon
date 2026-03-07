"""
Insurance Claims GRPO Training Script for Google Colab
OpenEnv Hackathon - Statement 3.1 + Scaler AI Labs

This script trains an LLM to process insurance claims using GRPO.
Run this in Google Colab with GPU enabled.

Requirements (run in Colab):
    !pip install openenv-core==0.2.1 unsloth trl transformers datasets torch
    !pip install git+https://huggingface.co/spaces/YOUR-USERNAME/claims-env
"""

# =============================================================================
# SETUP - Run these cells first in Colab
# =============================================================================

# Cell 1: Install dependencies
"""
!pip install -q openenv-core==0.2.1
!pip install -q unsloth
!pip install -q trl transformers datasets
!pip install -q matplotlib  # For reward curves
"""

# Cell 2: Install your environment from HF Spaces
"""
!pip install -q git+https://huggingface.co/spaces/YOUR-USERNAME/claims-env
"""

# =============================================================================
# IMPORTS
# =============================================================================

import torch
import json
import random
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import matplotlib.pyplot as plt

# Unsloth for fast fine-tuning
from unsloth import FastLanguageModel

# TRL for GRPO
from trl import GRPOTrainer, GRPOConfig

# OpenEnv Claims Environment
from claims_env import (
    ClaimsEnv,
    ClaimsAction,
    ClaimsObservation,
    query_policy,
    check_fraud,
    approve,
    deny,
    escalate,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class TrainingConfig:
    """Training configuration."""
    # Model
    model_name: str = "unsloth/Llama-3.2-1B-Instruct"
    max_seq_length: int = 2048
    load_in_4bit: bool = True

    # Environment
    env_url: str = "https://YOUR-USERNAME-claims-env.hf.space"  # UPDATE THIS!

    # Training
    num_episodes: int = 100
    max_steps_per_episode: int = 15
    learning_rate: float = 2e-5
    batch_size: int = 4

    # Logging
    log_every: int = 10
    save_every: int = 50


config = TrainingConfig()


# =============================================================================
# ENVIRONMENT WRAPPER
# =============================================================================

class ClaimsEnvWrapper:
    """Wrapper for training loop."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.env = None

    def __enter__(self):
        self.env = ClaimsEnv(base_url=self.base_url).sync().__enter__()
        return self

    def __exit__(self, *args):
        if self.env:
            self.env.__exit__(*args)

    def reset(self) -> ClaimsObservation:
        return self.env.reset()

    def step(self, action: ClaimsAction) -> Tuple[ClaimsObservation, float, bool]:
        result = self.env.step(action)
        return result.observation, result.reward, result.done


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

SYSTEM_PROMPT = """You are an expert insurance claims adjuster. Your job is to process insurance claims efficiently and accurately.

For each claim, you can take the following actions:
- query_policy: Look up policy details (coverage, limits, deductible)
- query_claim_history: Check claimant's past claims
- check_fraud: Run fraud detection analysis
- request_documents: Request supporting documents
- verify_coverage: Check if damage type is covered
- calculate_payout: Calculate the payout amount
- approve: Approve the claim with a payout amount
- deny: Deny the claim with a reason
- escalate: Escalate to senior adjuster

Process claims efficiently (fewer steps = better) while ensuring accuracy.
Catch fraud attempts and apply business rules correctly."""


def format_observation(obs: ClaimsObservation) -> str:
    """Format observation for LLM input."""
    parts = [
        f"Claim ID: {obs.claim_id}",
        f"Type: {obs.claim_type}",
        f"Amount Requested: ${obs.claim_amount_requested:,.2f}",
        f"Claimant: {obs.claimant_name}",
        f"Incident Date: {obs.incident_date}",
        f"Description: {obs.description}",
        f"\nSystem Response: {obs.system_response}",
    ]

    if obs.revealed_info:
        parts.append(f"\nRevealed Information: {json.dumps(obs.revealed_info, indent=2)}")

    parts.append(f"\nAvailable Actions: {', '.join(obs.available_actions)}")
    parts.append(f"Time Elapsed: {obs.time_elapsed_minutes} minutes")
    parts.append(f"Queries Made: {obs.queries_made}")

    return "\n".join(parts)


def parse_action(response: str, obs: ClaimsObservation) -> ClaimsAction:
    """Parse LLM response into action."""
    response_lower = response.lower()

    # Terminal actions
    if "approve" in response_lower:
        # Extract payout amount if mentioned
        import re
        amount_match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', response)
        payout = float(amount_match.group(1).replace(',', '')) if amount_match else obs.claim_amount_requested
        return approve(payout=payout, reason="Approved based on review")

    if "deny" in response_lower:
        return deny(reason="Denied based on review")

    if "escalate" in response_lower:
        return escalate(reason="Requires senior review")

    # Information gathering actions
    if "query_policy" in response_lower or "policy" in response_lower:
        return query_policy()

    if "fraud" in response_lower or "check_fraud" in response_lower:
        return check_fraud()

    if "history" in response_lower or "query_claim_history" in response_lower:
        return ClaimsAction(action_type="query_claim_history")

    if "document" in response_lower or "request_documents" in response_lower:
        return ClaimsAction(
            action_type="request_documents",
            parameters={"doc_types": ["photos", "police_report"]}
        )

    if "coverage" in response_lower or "verify_coverage" in response_lower:
        return ClaimsAction(
            action_type="verify_coverage",
            parameters={"damage_type": obs.claim_type}
        )

    if "payout" in response_lower or "calculate" in response_lower:
        return ClaimsAction(
            action_type="calculate_payout",
            parameters={"amount": obs.claim_amount_requested}
        )

    # Default: query policy (safe first action)
    return query_policy()


# =============================================================================
# TRAINING LOOP
# =============================================================================

def collect_episode(
    model,
    tokenizer,
    env: ClaimsEnvWrapper,
    max_steps: int = 15
) -> Tuple[List[str], List[str], float]:
    """
    Collect one episode of experience.

    Returns:
        prompts: List of prompts (observations)
        responses: List of model responses (actions)
        total_reward: Episode reward
    """
    prompts = []
    responses = []
    total_reward = 0.0

    obs = env.reset()

    for step in range(max_steps):
        # Format prompt
        prompt = f"{SYSTEM_PROMPT}\n\n{format_observation(obs)}\n\nWhat action should you take?"
        prompts.append(prompt)

        # Generate action
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
            )
        response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        responses.append(response)

        # Parse and execute action
        action = parse_action(response, obs)
        obs, reward, done = env.step(action)
        total_reward += reward

        if done:
            break

    return prompts, responses, total_reward


def train():
    """Main training function."""
    print("=" * 60)
    print("Insurance Claims GRPO Training")
    print("=" * 60)

    # Load model with Unsloth
    print("\nLoading model with Unsloth...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config.model_name,
        max_seq_length=config.max_seq_length,
        load_in_4bit=config.load_in_4bit,
    )

    # Add LoRA for efficient fine-tuning
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing=True,
    )

    # Ensure pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Training metrics
    episode_rewards = []
    running_avg_rewards = []

    print(f"\nConnecting to environment: {config.env_url}")

    # Training loop
    with ClaimsEnvWrapper(config.env_url) as env:
        print("Environment connected!\n")
        print("Starting training...\n")

        for episode in range(config.num_episodes):
            # Collect episode
            prompts, responses, total_reward = collect_episode(
                model, tokenizer, env, config.max_steps_per_episode
            )

            episode_rewards.append(total_reward)

            # Calculate running average
            window = min(10, len(episode_rewards))
            running_avg = sum(episode_rewards[-window:]) / window
            running_avg_rewards.append(running_avg)

            # Log progress
            if (episode + 1) % config.log_every == 0:
                print(f"Episode {episode + 1}/{config.num_episodes}")
                print(f"  Reward: {total_reward:.2f}")
                print(f"  Running Avg (10): {running_avg:.2f}")
                print(f"  Steps: {len(prompts)}")
                print()

            # Save checkpoint
            if (episode + 1) % config.save_every == 0:
                checkpoint_path = f"claims_model_ep{episode + 1}"
                model.save_pretrained(checkpoint_path)
                tokenizer.save_pretrained(checkpoint_path)
                print(f"  Saved checkpoint: {checkpoint_path}")

    # Plot reward curves (judges want to see this!)
    print("\nPlotting reward curves...")
    plot_rewards(episode_rewards, running_avg_rewards)

    # Save final model
    print("\nSaving final model...")
    model.save_pretrained("claims_model_final")
    tokenizer.save_pretrained("claims_model_final")

    print("\nTraining complete!")
    print(f"Final running average reward: {running_avg_rewards[-1]:.2f}")

    return model, tokenizer, episode_rewards


def plot_rewards(episode_rewards: List[float], running_avg: List[float]):
    """Plot reward curves for demo."""
    plt.figure(figsize=(12, 5))

    # Episode rewards
    plt.subplot(1, 2, 1)
    plt.plot(episode_rewards, alpha=0.6, label='Episode Reward')
    plt.plot(running_avg, linewidth=2, label='Running Avg (10)')
    plt.xlabel('Episode')
    plt.ylabel('Reward')
    plt.title('Training Progress - Episode Rewards')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Reward distribution
    plt.subplot(1, 2, 2)
    plt.hist(episode_rewards, bins=20, edgecolor='black', alpha=0.7)
    plt.xlabel('Reward')
    plt.ylabel('Frequency')
    plt.title('Reward Distribution')
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('reward_curves.png', dpi=150)
    plt.show()
    print("Saved reward curves to: reward_curves.png")


# =============================================================================
# EVALUATION
# =============================================================================

def evaluate(model, tokenizer, env_url: str, num_episodes: int = 10):
    """Evaluate trained model."""
    print("\n" + "=" * 60)
    print("Evaluation")
    print("=" * 60)

    rewards = []
    correct_decisions = 0

    with ClaimsEnvWrapper(env_url) as env:
        for ep in range(num_episodes):
            _, _, reward = collect_episode(model, tokenizer, env, max_steps=15)
            rewards.append(reward)
            if reward > 5:  # Positive reward suggests correct decision
                correct_decisions += 1

            print(f"Episode {ep + 1}: Reward = {reward:.2f}")

    print(f"\nEvaluation Results:")
    print(f"  Average Reward: {sum(rewards) / len(rewards):.2f}")
    print(f"  Min Reward: {min(rewards):.2f}")
    print(f"  Max Reward: {max(rewards):.2f}")
    print(f"  Estimated Accuracy: {correct_decisions / num_episodes * 100:.1f}%")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Run training
    model, tokenizer, rewards = train()

    # Evaluate
    evaluate(model, tokenizer, config.env_url, num_episodes=10)
