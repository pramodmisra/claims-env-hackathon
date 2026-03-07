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
  - rl-environment
---

# InsureClaim AI - Insurance Claims RL Environment

**OpenEnv Hackathon - Statement 3.1: Professional Tasks (World Modeling)**
**Partner Theme: Scaler AI Labs - Enterprise Workflows**

An RL environment for training LLMs to process insurance claims with realistic enterprise complexity, fraud detection, and Plaid API integration.

## Live Demo

- **HuggingFace Space**: https://pramodmisra-claims-env.hf.space
- **Health Check**: `curl https://pramodmisra-claims-env.hf.space/health`

## Training Results

| Metric | Value |
|--------|-------|
| Starting Reward | -5.5 |
| Final Average | **+11.75** |
| Improvement | **+17.25** |
| Best Episode | +17.4 (caught fraud) |
| Steps Reduction | 6 → 3 (50% faster) |

![Reward Curves](reward_curves.png)

## Overview

This environment simulates a real insurance claims processing workflow where an agent must:

1. **Gather Information** - Query policy details, claim history, fraud signals
2. **Verify Transactions** - Use Plaid API to verify purchase amounts
3. **Detect Fraud** - Identify inflated claims and staged accidents
4. **Make Decisions** - Approve, deny, or escalate claims efficiently

### Key Innovations

| Feature | Description |
|---------|-------------|
| **Partial Observability** | Agent must actively query to reveal information |
| **10 Actions** | Including Plaid transaction verification |
| **8 Scenarios** | Fraud, coverage limits, exclusions, escalations |
| **Multi-component Rewards** | Accuracy (+10), Fraud caught (+5), Efficiency (+1) |

## Quick Start

### Test the Environment
```bash
# Health check
curl https://pramodmisra-claims-env.hf.space/health

# Run training demo
pip install websockets matplotlib certifi
python training/demo_training.py
```

### WebSocket Connection
```python
import asyncio
import websockets
import json

async def process_claim():
    async with websockets.connect('wss://pramodmisra-claims-env.hf.space/ws') as ws:
        # Reset environment
        await ws.send('{"type": "reset", "data": {}}')
        response = json.loads(await ws.recv())
        obs = response["data"]["observation"]
        print(f"Claim: {obs['claim_id']} - ${obs['claim_amount_requested']:,.2f}")

        # Query policy
        await ws.send('{"type": "step", "data": {"action_type": "query_policy"}}')
        response = json.loads(await ws.recv())
        print(f"Reward: {response['data']['reward']}")

        # Check fraud
        await ws.send('{"type": "step", "data": {"action_type": "check_fraud"}}')
        response = json.loads(await ws.recv())

        # Approve claim
        await ws.send('{"type": "step", "data": {"action_type": "approve", "parameters": {"payout": 3500}}}')
        response = json.loads(await ws.recv())
        print(f"Final reward: {response['data']['reward']}, Done: {response['data']['done']}")

asyncio.run(process_claim())
```

## Actions

| Action | Description | Time Cost | Reward |
|--------|-------------|-----------|--------|
| `query_policy` | Look up policy details | 2 min | -0.1 |
| `query_claim_history` | Check past claims | 3 min | -0.1 |
| `check_fraud` | Run fraud detection | 5 min | -0.2 |
| `request_documents` | Request photos/reports | 10 min | -0.5 |
| `verify_coverage` | Check coverage type | 2 min | -0.1 |
| `verify_purchase` | **Plaid API verification** | 8 min | -0.3 (+2 if discrepancy) |
| `calculate_payout` | Calculate amount | 3 min | -0.1 |
| `approve` | Approve claim | 1 min | +10 to -15 |
| `deny` | Deny claim | 1 min | +15 to -5 |
| `escalate` | Escalate to senior | 5 min | +3 to -2 |

## Reward Structure

| Component | Reward | Condition |
|-----------|--------|-----------|
| Correct decision | **+10** | Matches ground truth |
| Wrong decision | **-5** | Incorrect decision |
| Fraud caught | **+5** | Correctly denied fraud |
| Fraud missed | **-10** | Approved fraudulent claim |
| Plaid discrepancy | **+2** | Found amount mismatch |
| Efficiency bonus | **+1** | ≤4 steps |
| Efficiency penalty | **-0.2/step** | >8 steps |

## Scenarios

| # | Type | Complexity | Fraud | Correct Action |
|---|------|------------|-------|----------------|
| 1 | Auto Collision | Simple | No | Approve |
| 2 | Home Water | Standard | No | Partial Approve |
| 3 | Auto Collision | Complex | **Yes** | Deny (staged) |
| 4 | Home Water | Standard | No | Deny (exclusion) |
| 5 | Home Fire | Complex | No | Escalate |
| 6 | Auto Theft | Complex | **Yes** | Deny (inflated) |
| 7 | Auto Liability | Standard | No | Approve |
| 8 | Home Burglary | Simple | No | Deny (lapsed) |

## Fraud Detection Demo

```
Claim: CLM-2024-006 (Auto Theft)
Claimed Amount: $35,000

Step 1: query_policy
  → Coverage: $40,000 limit, active policy ✓

Step 2: check_fraud
  → Risk Score: 0.80 ⚠️ HIGH
  → Flags: multiple_claims, amount_anomaly

Step 3: verify_purchase (PLAID API)
  → DISCREPANCY DETECTED!
  → Claimed: $35,000
  → Actual Transaction: $22,000

Step 4: deny
  → Reward: +17.4 (correct + fraud caught + efficiency)
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   InsureClaim AI Platform               │
├─────────────────────────────────────────────────────────┤
│  PLAID APIs              AI PROCESSOR       SCALE AI   │
│  ┌─────────────┐        ┌───────────┐     ┌─────────┐  │
│  │ Identity    │───────▶│ Claims    │────▶│ Expert  │  │
│  │ Transactions│        │ LLM       │     │ Review  │  │
│  │ Income      │◀───────│ (GRPO)    │◀────│ RLHF    │  │
│  │ Assets      │        └───────────┘     └─────────┘  │
│  └─────────────┘              │                        │
│                               ▼                        │
│                    ┌───────────────────┐               │
│                    │ Continuous Learning│              │
│                    │ Loop (Weekly)      │              │
│                    └───────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

## Local Development

```bash
# Clone
git clone https://github.com/pramodmisra/claims-env-hackathon.git
cd claims-env-hackathon

# Install
pip install -r requirements.txt

# Run server
python -m uvicorn space_app:app --port 7860

# Test
python demo_claims.py
```

## Files

| File | Description |
|------|-------------|
| `space_app.py` | FastAPI server entry point |
| `models.py` | Pydantic models (Action, Observation, State) |
| `server/claims_environment.py` | Main environment logic |
| `server/mock_systems.py` | Backend system simulations |
| `server/plaid_client.py` | Real Plaid API client |
| `training/demo_training.py` | Working training script |
| `demo_claims.py` | Local demo script |
| `PITCH.md` | 3-minute pitch script |
| `VIDEO_SCRIPT.md` | 1-minute video script |

## Business Impact

| Metric | Before AI | With InsureClaim AI |
|--------|-----------|---------------------|
| Processing time | 14 days | **2 hours** |
| Fraud detection | 23% | **91%** |
| Cost per claim | $150 | **$35** |
| Annual Savings | - | **$28.5M** |

## Links

- **Live Demo**: https://pramodmisra-claims-env.hf.space
- **GitHub**: https://github.com/pramodmisra/claims-env-hackathon
- **Product Vision**: [docs/PRODUCT_VISION.md](docs/PRODUCT_VISION.md)

## Hackathon Alignment

**Problem Statement 3.1 - Professional Tasks (World Modeling)**
- Multi-step decision making ✓
- Partial observability ✓
- Real-world complexity ✓

**Partner Theme: Scaler AI Labs - Enterprise Workflows**
- Multiple backend systems ✓
- Business rules enforcement ✓
- Approval chains (escalation) ✓
- RLHF integration roadmap ✓

## License

MIT License
