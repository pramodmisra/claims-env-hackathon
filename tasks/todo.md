# OpenEnv Hackathon - Insurance Claims RL Environment

## Status: READY FOR SUBMISSION

### Completed
- [x] Environment design (10 actions, 8 scenarios, partial observability)
- [x] Pydantic models (ClaimsAction, ClaimsObservation, ClaimsState)
- [x] Mock systems (PolicyDB, ClaimsHistoryDB, FraudAPI, DocumentSystem, PayoutCalculator)
- [x] Plaid integration for transaction verification
- [x] Multi-component reward function (+10 correct, +5 fraud caught, -10 fraud missed)
- [x] HF Space DEPLOYED: https://pramodmisra-claims-env.hf.space
- [x] **Reward serialization fixed** - rewards correctly returned via WebSocket
- [x] **Training script working** - demo_training.py shows +17.25 improvement
- [x] **reward_curves.png generated** - shows clear learning progression
- [x] GitHub repo: https://github.com/pramodmisra/claims-env-hackathon
- [x] PITCH.md - 3-minute presentation script
- [x] VIDEO_SCRIPT.md - 1-minute demo video script
- [x] Product vision document (docs/PRODUCT_VISION.md)
- [x] README.md updated with all results

### User Action Required
- [ ] Record 1-minute demo video (use VIDEO_SCRIPT.md)
- [ ] Upload to YouTube
- [ ] Submit to hackathon portal: https://openenv-hackathon.devpost.com
- [ ] **Deadline: Sunday 1PM Pacific**

## Training Results (March 7, 2026)

```
Episode  1: -5.50  | Steps: 6   ← Exploring
Episode 10: +12.4  | Steps: 6   ← Learning
Episode 25: +13.6  | Steps: 3   ← Efficient
Episode 45: +17.4  | Steps: 4   ← Caught fraud!
Episode 50: +11.1  | Steps: 3   ← Converged

Final Average: +11.75
Improvement: +17.25
Range: -15.7 to +17.4
```

## Quick Commands

### Run Training (generates reward_curves.png)
```bash
python training/demo_training.py
```

### Test HF Space
```bash
curl https://pramodmisra-claims-env.hf.space/health
```

### Local Demo
```bash
python demo_claims.py
```

## Files for Submission

| File | Purpose |
|------|---------|
| `reward_curves.png` | Training progress visualization |
| `VIDEO_SCRIPT.md` | 1-minute video script |
| `PITCH.md` | 3-minute presentation |
| `README.md` | Project overview |
| `docs/PRODUCT_VISION.md` | Full product roadmap |

## Links
- **HF Space**: https://pramodmisra-claims-env.hf.space
- **GitHub**: https://github.com/pramodmisra/claims-env-hackathon
- **Problem Statement**: 3.1 Professional Tasks + Scaler AI Labs
