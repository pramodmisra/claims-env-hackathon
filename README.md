---
title: Insurance Claims RL Environment
emoji: 📋
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
tags:
  - openenv
  - reinforcement-learning
  - insurance
  - enterprise-workflows
  - hackathon
---

# Insurance Claims Processing Environment

**OpenEnv Hackathon - Statement 3.1: Professional Tasks**
**Partner Theme: Scaler AI Labs - Enterprise Workflows**

An RL environment for training LLMs to process insurance claims with realistic enterprise complexity.

## Overview

This environment simulates a real insurance claims processing workflow where an agent must:

1. **Gather Information** - Query policy details, claim history, fraud signals
2. **Verify Coverage** - Check if damage types are covered, exclusions apply
3. **Calculate Payouts** - Apply deductibles, coverage limits
4. **Make Decisions** - Approve, deny, or escalate claims
5. **Detect Fraud** - Identify suspicious patterns and staged claims

### Key Features

- **Partial Observability**: Agent must actively query systems to reveal information
- **Business Rule Nuances**: Coverage limits, deductibles, exclusions, escalation rules
- **Fraud Detection**: Some claims are fraudulent - agent must learn to identify them
- **Efficiency Trade-offs**: Queries cost time, but rushing leads to wrong decisions

## Quick Start

```python
from claims_env import ClaimsEnv, ClaimsAction

# Connect to HF Space
with ClaimsEnv(base_url="https://YOUR-USERNAME-claims-env.hf.space").sync() as env:
    # Reset to get a new claim
    obs = env.reset()
    print(f"New claim: {obs.claim_id} - {obs.claim_type}")
    print(f"Amount requested: ${obs.claim_amount_requested:,.2f}")
    print(f"Description: {obs.description}")

    # Query policy details
    result = env.step(ClaimsAction(action_type="query_policy"))
    print(f"Policy info: {result.observation.system_response}")

    # Check for fraud signals
    result = env.step(ClaimsAction(action_type="check_fraud"))
    print(f"Fraud check: {result.observation.system_response}")

    # Make decision
    result = env.step(ClaimsAction(
        action_type="approve",
        parameters={"payout": 3000.0, "reason": "Valid claim, coverage confirmed"}
    ))
    print(f"Final reward: {result.reward}")
```

## Actions

| Action | Description | Time Cost | Reward Cost |
|--------|-------------|-----------|-------------|
| `query_policy` | Look up policy details | 2 min | -0.1 |
| `query_claim_history` | Check claimant's past claims | 3 min | -0.1 |
| `check_fraud` | Run fraud detection analysis | 5 min | -0.2 |
| `request_documents` | Request photos, reports, etc. | 10 min | -0.5 |
| `verify_coverage` | Check if damage type is covered | 2 min | -0.1 |
| `calculate_payout` | Calculate payout amount | 3 min | -0.1 |
| `approve` | Approve claim (terminal) | 1 min | varies |
| `deny` | Deny claim (terminal) | 1 min | varies |
| `escalate` | Escalate to senior adjuster (terminal) | 5 min | varies |

## Reward Structure

| Component | Reward | Condition |
|-----------|--------|-----------|
| Correct decision | +10 | Agent's decision matches ground truth |
| Wrong decision | -5 | Agent's decision is incorrect |
| Fraud caught | +5 | Denied a fraudulent claim |
| Fraud missed | -10 | Approved a fraudulent claim |
| Efficiency bonus | +1 | Completed in 4 or fewer steps |
| Efficiency penalty | -0.2/step | Each step over 8 |
| Query costs | -0.1 to -0.5 | Per information-gathering action |

## Scenarios

The environment includes 8 diverse scenarios:

1. **Simple Auto Claim** - Straightforward approval
2. **Home Water Damage** - Partial approval (over limit)
3. **Staged Accident Fraud** - Must deny
4. **Coverage Exclusion** - External flood not covered
5. **Large Fire Claim** - Requires escalation
6. **Inflated Claim Fraud** - Must deny
7. **Liability Claim** - No deductible applies
8. **Lapsed Policy** - Must deny (inactive policy)

## Training with Unsloth

```python
# See training/train_grpo.py for full example
from unsloth import FastLanguageModel
from claims_env import ClaimsEnv, ClaimsAction

# Load model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Llama-3.2-1B-Instruct",
    max_seq_length=2048,
    load_in_4bit=True,
)

# Connect to environment
env = ClaimsEnv(base_url="https://your-space.hf.space").sync()

# Training loop
for episode in range(100):
    obs = env.reset()
    done = False
    episode_reward = 0

    while not done:
        # Your policy here
        action = model_predict(obs)
        result = env.step(action)
        episode_reward += result.reward
        done = result.done
        obs = result.observation

    print(f"Episode {episode}: Reward = {episode_reward:.2f}")
```

## Deployment to HF Spaces

```bash
# Login to Hugging Face
huggingface-cli login

# Deploy
openenv push --repo-id YOUR-USERNAME/claims-env
```

## Local Development

```bash
# Install
pip install -e ".[dev,server]"

# Run server
uvicorn claims_env.server.app:app --reload

# Test
pytest tests/ -v
```

## Enterprise Workflow Complexity (Scaler AI Labs Theme)

This environment demonstrates real enterprise workflow nuances:

1. **Multi-System Integration**: Agent queries multiple backend systems
2. **Business Rules**: Coverage limits, deductibles, exclusions
3. **Approval Chains**: Large claims require escalation
4. **Fraud Detection**: ML-based signals with false positives
5. **Documentation Requirements**: Some claims need specific documents
6. **Time Pressure**: Efficiency matters but rushing causes errors

## License

MIT License
