#!/usr/bin/env python3
"""
Demo: Insurance Claims RL Environment
Shows the agent processing a claim step by step.
"""

import asyncio
import json
import websockets

ENV_URL = "ws://127.0.0.1:7860/ws"

async def demo_claims_processing():
    """Demonstrate claims processing with all features."""
    print("=" * 70)
    print("DEMO: Insurance Claims RL Environment")
    print("OpenEnv Hackathon - Statement 3.1 Professional Tasks")
    print("=" * 70)

    async with websockets.connect(ENV_URL) as ws:
        # Reset and get initial observation
        await ws.send(json.dumps({"type": "reset", "data": {}}))
        response = json.loads(await ws.recv())
        obs = response["data"]["observation"]

        print(f"\n{'='*70}")
        print("NEW CLAIM RECEIVED")
        print(f"{'='*70}")
        print(f"  Claim ID:     {obs['claim_id']}")
        print(f"  Type:         {obs['claim_type']}")
        print(f"  Amount:       ${obs['claim_amount_requested']:,.2f}")
        print(f"  Claimant:     {obs['claimant_name']}")
        print(f"  Date:         {obs['incident_date']}")
        print(f"  Description:  {obs['description']}")

        claim_amount = obs['claim_amount_requested']
        total_reward = 0

        # Step 1: Query Policy
        print(f"\n{'─'*70}")
        print("Step 1: QUERY_POLICY")
        print(f"{'─'*70}")
        await ws.send(json.dumps({"type": "step", "data": {"action_type": "query_policy", "parameters": {}}}))
        response = json.loads(await ws.recv())
        obs = response["data"]["observation"]
        policy = obs["revealed_info"].get("policy", {})
        print(f"  → Coverage: ${policy.get('coverage_limit', 0):,.2f}")
        print(f"  → Deductible: ${policy.get('deductible', 0):,.2f}")
        print(f"  → Status: {policy.get('policy_status', 'unknown')}")

        # Step 2: Check Fraud
        print(f"\n{'─'*70}")
        print("Step 2: CHECK_FRAUD")
        print(f"{'─'*70}")
        await ws.send(json.dumps({"type": "step", "data": {"action_type": "check_fraud", "parameters": {}}}))
        response = json.loads(await ws.recv())
        obs = response["data"]["observation"]
        fraud = obs["revealed_info"].get("fraud_analysis", {})
        risk_score = fraud.get("risk_score", 0)
        flags = fraud.get("flags", [])
        print(f"  → Risk Score: {risk_score:.2f} {'⚠️ HIGH RISK' if risk_score > 0.5 else '✓ LOW RISK'}")
        if flags:
            print(f"  → Flags: {', '.join(flags)}")

        # Step 3: Verify Purchase (Plaid Integration)
        print(f"\n{'─'*70}")
        print("Step 3: VERIFY_PURCHASE (Plaid API)")
        print(f"{'─'*70}")
        await ws.send(json.dumps({"type": "step", "data": {"action_type": "verify_purchase", "parameters": {}}}))
        response = json.loads(await ws.recv())
        obs = response["data"]["observation"]
        plaid = obs["revealed_info"].get("purchase_verification", {})
        if plaid.get("match_found"):
            actual_amount = plaid.get("actual_amount", 0)
            print(f"  → Transaction Found: ${actual_amount:,.2f}")
            if actual_amount < claim_amount * 0.9:
                print(f"  → DISCREPANCY: Claimed ${claim_amount:,.2f} but transaction shows ${actual_amount:,.2f}")
        else:
            print(f"  → No matching transaction found")

        # Step 4: Calculate Payout
        print(f"\n{'─'*70}")
        print("Step 4: CALCULATE_PAYOUT")
        print(f"{'─'*70}")
        await ws.send(json.dumps({"type": "step", "data": {"action_type": "calculate_payout", "parameters": {}}}))
        response = json.loads(await ws.recv())
        obs = response["data"]["observation"]
        payout_info = obs["revealed_info"].get("payout_calculation", {})
        recommended = payout_info.get("recommended_payout", 0)
        print(f"  → Recommended Payout: ${recommended:,.2f}")

        # Step 5: Make Decision
        print(f"\n{'─'*70}")
        print("Step 5: FINAL DECISION")
        print(f"{'─'*70}")

        # Decision logic based on gathered evidence
        is_fraud = risk_score > 0.5
        has_discrepancy = plaid.get("match_found") and plaid.get("actual_amount", claim_amount) < claim_amount * 0.9

        if is_fraud or has_discrepancy:
            action = {"action_type": "deny", "parameters": {"reason": "Fraud indicators detected" if is_fraud else "Amount discrepancy"}}
            decision = "DENY"
        elif recommended > 0:
            action = {"action_type": "approve", "parameters": {"payout": recommended}}
            decision = f"APPROVE (${recommended:,.2f})"
        else:
            action = {"action_type": "approve", "parameters": {"payout": claim_amount}}
            decision = f"APPROVE (${claim_amount:,.2f})"

        await ws.send(json.dumps({"type": "step", "data": action}))
        response = json.loads(await ws.recv())
        obs = response["data"]["observation"]
        reward = response["data"].get("reward", 0)

        print(f"  → Decision: {decision}")
        print(f"  → Reason: {obs['terminal_reason']}")
        print(f"  → Reward: {reward:+.2f}" if reward else "  → Reward: (pending)")

        # Summary
        print(f"\n{'='*70}")
        print("PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"  Steps taken: {obs['queries_made'] + 1}")
        print(f"  Time elapsed: {obs['time_elapsed_minutes']} minutes")
        print(f"  Terminal: {obs['is_terminal']}")

        # Close session
        await ws.send(json.dumps({"type": "close", "data": {}}))

    print("\n✓ Demo completed successfully\n")

if __name__ == "__main__":
    asyncio.run(demo_claims_processing())
