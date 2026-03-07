# Insurance Claims RL Environment - Pitch Script

## 3-Minute Demo Script for Judges

---

### SLIDE 1: THE PROBLEM (30 seconds)

**SAY:**
> "Insurance claims processing costs the industry $40 billion annually. Today's LLMs rush to conclusions - they see a claim and immediately say 'approve' or 'deny' without gathering evidence."
>
> "Real claims adjusters must query multiple systems, detect fraud, apply business rules. Current benchmarks don't teach these skills."

**SHOW:** Initial claim observation

---

### SLIDE 2: OUR SOLUTION (60 seconds)

**SAY:**
> "We built an RL environment that teaches LLMs to think like expert adjusters."
>
> "Key innovations:
> 1. **Partial observability** - Agent must actively query to reveal information
> 2. **10 actions** including Plaid transaction verification
> 3. **8 diverse scenarios** - fraud, coverage limits, exclusions
> 4. **Multi-component rewards** - accuracy, fraud detection, efficiency"

**SHOW:** Action list and reward structure

**SAY:**
> "The agent learns that rushing costs rewards - but so does over-investigating."

---

### SLIDE 3: LIVE DEMO (60 seconds)

**SAY:**
> "Let's watch the agent process a claim."

**DO:** Run demo cell showing agent processing claim step by step

**SAY (as it runs):**
> "First, it queries the policy... checks fraud signals...
> Look - it's using Plaid to verify the transaction...
> The agent caught the discrepancy! The claimed $35K doesn't match the $22K transaction.
> It denies the claim. Total reward: +17."

---

### SLIDE 4: TRAINING RESULTS (30 seconds)

**SHOW:** Reward curves from notebook

**SAY:**
> "After 50 episodes, the agent's average reward climbs from -2 to +12.
> Estimated accuracy reaches 78%."

---

### SLIDE 5: SCALER AI ALIGNMENT (20 seconds)

**SAY:**
> "This directly addresses Scaler's 'Enterprise Workflows' theme:
> - Multiple backend systems
> - Business rules (deductibles, coverage limits)
> - Approval chains for large claims
> - Real-world fraud detection patterns"

---

### CLOSING (20 seconds)

**SAY:**
> "Insurance Claims Environment - teaching LLMs to think before they decide."

**SHOW LINKS:**
- HF Space: https://huggingface.co/spaces/pramodmisra/claims-env
- GitHub: https://github.com/pramodmisra/claims-env-hackathon
- Training Notebook: In GitHub repo

---

## Quick Stats for Q&A

| Metric | Value |
|--------|-------|
| Actions | 10 (including Plaid) |
| Scenarios | 8 |
| Fraud cases | 2 (25%) |
| Correct decision reward | +10 |
| Fraud caught reward | +5 |
| Fraud missed penalty | -10 |
| Avg training reward improvement | +14 points |

## Potential Questions

**Q: Why insurance?**
> "Real enterprise complexity. Multiple systems, business rules, fraud detection - exactly what LLMs struggle with today."

**Q: Why Plaid?**
> "Transaction verification catches inflated claims that fraud scores miss. It's a real enterprise integration pattern."

**Q: How does partial observability help?**
> "Forces the agent to learn WHEN to query. Rushing = wrong decisions. Over-investigating = wasted time. The reward function balances both."

**Q: What makes this different from other environments?**
> "Domain expertise. We modeled real insurance workflows - coverage limits, deductibles, exclusions, escalation rules. Most hackathon envs are generic."

---

## Demo Flow (Backup - If Live Demo Fails)

```
Claim: CLM-2024-006 (Inflated Auto Theft)
Amount: $35,000
True Transaction: $22,000

Step 1: query_policy
  -> Coverage: $40,000 limit, $1,000 deductible

Step 2: check_fraud
  -> Risk score: 0.80, Flags: multiple_claims, claim_amount_anomaly

Step 3: verify_purchase (Plaid)
  -> DISCREPANCY: Claims $35K but transaction shows $22K

Step 4: deny
  -> Reason: Inflated claim detected

Total Reward: +17.4
```
