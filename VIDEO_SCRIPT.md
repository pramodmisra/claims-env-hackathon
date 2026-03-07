# InsureClaim AI - 1 Minute Demo Video Script

## OpenEnv Hackathon | Statement 3.1 + Scaler AI Labs

---

## VIDEO SCRIPT (60 seconds)

### [0:00-0:10] HOOK
**SHOW:** Terminal with training running
**SAY:**
> "Insurance claims processing costs $40 billion annually. Today's LLMs rush to approve or deny without investigating. We built an RL environment that teaches them to think like expert adjusters."

---

### [0:10-0:25] THE ENVIRONMENT
**SHOW:** HuggingFace Space health check + architecture diagram
**SAY:**
> "InsureClaim AI is a 10-action RL environment with partial observability. The agent must query policy databases, run fraud detection, and verify transactions through real Plaid APIs before making decisions."

**SHOW:** Quick scroll of valid actions:
- query_policy, check_fraud, verify_purchase, approve, deny, escalate

---

### [0:25-0:45] LIVE DEMO - FRAUD DETECTION
**SHOW:** Terminal running demo_training.py or WebSocket test
**SAY:**
> "Watch the agent catch fraud in real-time."

**SHOW:**
```
Claim: CLM-2024-006 (Auto Theft) - $35,000

Step 1: query_policy    → Coverage active ✓
Step 2: check_fraud     → Risk: 0.80 HIGH ⚠️
Step 3: verify_purchase → DISCREPANCY! Paid $22K, claimed $35K
Step 4: deny            → Reward: +17.4 🎯

Agent caught $13,000 inflated claim!
```

**SAY:**
> "The agent detected a $13,000 inflated claim that a naive LLM would have approved. That's +17 reward for catching fraud."

---

### [0:45-0:55] TRAINING RESULTS
**SHOW:** reward_curves.png
**SAY:**
> "After 50 episodes, our agent improved from -5 to +12 average reward. It learned to investigate efficiently - just 3 steps instead of 12 - while catching fraud cases."

**SHOW:** Key metrics:
- Start: -5.5 reward
- End: +11.75 reward
- Improvement: +17.25
- Fraud detection: +17.4 max reward

---

### [0:55-1:00] CLOSE
**SHOW:** Links on screen
**SAY:**
> "InsureClaim AI - teaching LLMs to investigate before they decide. Links in description."

**SHOW:**
- Live: https://pramodmisra-claims-env.hf.space
- GitHub: https://github.com/pramodmisra/claims-env-hackathon

---

## RECORDING TIPS

1. **Screen recording**: Use QuickTime or OBS
2. **Resolution**: 1920x1080
3. **Terminal font**: Large (18-20pt) for readability
4. **Pace**: Speak clearly, not rushed
5. **Background**: Clean desktop, dark terminal theme

## WHAT TO RECORD

1. **Terminal 1**: Run `python training/demo_training.py`
2. **Terminal 2**: Show WebSocket test catching fraud
3. **Browser**: HuggingFace Space health check
4. **Image**: reward_curves.png full screen

## BACKUP COMMANDS

```bash
# Test HF Space
curl https://pramodmisra-claims-env.hf.space/health

# Run training demo
python training/demo_training.py

# Quick fraud detection demo
python demo_claims.py
```

---

## KEY TALKING POINTS FOR JUDGES

1. **Real APIs**: Plaid transaction verification (not mocks in production vision)
2. **Enterprise complexity**: 8 scenarios, coverage limits, exclusions, escalation
3. **Meaningful rewards**: +10 correct, +5 fraud caught, -10 fraud missed
4. **Efficiency learning**: Agent optimizes for fewer steps
5. **Partial observability**: Agent must query to reveal information
