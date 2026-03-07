# OpenEnv Hackathon - Insurance Claims RL Environment

## Status: READY FOR TRAINING AND SUBMISSION

### Completed
- [x] Environment design (10 actions, 8 scenarios, partial observability)
- [x] Pydantic models (ClaimsAction, ClaimsObservation, ClaimsState)
- [x] Mock systems (PolicyDB, ClaimsHistoryDB, FraudAPI, DocumentSystem, PayoutCalculator)
- [x] Plaid integration for transaction verification
- [x] Multi-component reward function (+10 correct, +5 fraud caught, -10 fraud missed)
- [x] Local server testing via WebSocket (WORKING)
- [x] GitHub repo: https://github.com/pramodmisra/claims-env-hackathon
- [x] Training notebook updated with WebSocket protocol
- [x] Demo script created (demo_claims.py)
- [x] PITCH.md prepared with 3-minute script
- [x] HF Space DEPLOYED & WORKING: https://pramodmisra-claims-env.hf.space
- [x] **Reward serialization fixed** - rewards now correctly returned via WebSocket
- [x] Real Plaid client integrated (server/plaid_client.py)
- [x] Product vision document (docs/PRODUCT_VISION.md)

### Ready for User
- [ ] Run training notebook on Colab Pro (requires GPU)
- [ ] Save reward_curves.png from training
- [ ] Record 1-minute YouTube demo video
- [ ] Submit to hackathon portal: https://openenv-hackathon.devpost.com
- [ ] **Deadline: Sunday 1PM Pacific**

## Verified Working (March 7, 2026)

### HF Space Test Results
```
RESET: reward=0.0, done=False
query_policy: reward=-0.1, done=False
approve: reward=11.07, done=True
```

### Local Test Results
```
Fraud case (+17.40 total reward):
  - query_policy: -0.10
  - check_fraud: -0.20
  - verify_purchase: +1.70 (found discrepancy!)
  - deny: +16.00 (correct + fraud caught + efficiency)

Normal case (+13.20 total reward):
  - query_policy: -0.10
  - check_fraud: -0.20
  - approve: +13.50 (correct + accuracy)
```

## Quick Start

### Run Training on Colab
1. Open `training/OpenEnv_Claims_Training.ipynb` in Google Colab
2. Enable GPU runtime
3. Run all cells
4. Save `reward_curves.png` when training completes

### Local Demo
```bash
cd /Users/pramodmisra/Claude/openenv-hackathon/claims_env
python3 demo_claims.py
```

### Test HF Space
```bash
curl -s https://pramodmisra-claims-env.hf.space/health
# {"status":"healthy","environment":"claims_env"}
```

## Links
- **HF Space**: https://pramodmisra-claims-env.hf.space
- **GitHub**: https://github.com/pramodmisra/claims-env-hackathon
- **Problem Statement**: 3.1 Professional Tasks + Scaler AI Labs

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
