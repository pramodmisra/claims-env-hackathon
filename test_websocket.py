#!/usr/bin/env python3
"""WebSocket test client for Claims Environment."""

import asyncio
import json
import websockets

ENV_URL = "ws://127.0.0.1:7860/ws"

async def test_claims_environment():
    """Test the claims environment via WebSocket."""
    print("=" * 60)
    print("Claims Environment WebSocket Test")
    print("=" * 60)

    async with websockets.connect(ENV_URL) as ws:
        # 1. Reset the environment
        print("\n[1] Sending reset...")
        reset_msg = {"type": "reset", "data": {}}
        await ws.send(json.dumps(reset_msg))

        response = await ws.recv()
        obs = json.loads(response)

        if obs.get("type") == "error":
            print(f"ERROR: {obs['data']}")
            return

        obs_data = obs.get("data", {})
        print(f"Claim ID: {obs_data.get('claim_id')}")
        print(f"Type: {obs_data.get('claim_type')}")
        print(f"Amount: ${obs_data.get('claim_amount_requested', 0):,.2f}")
        print(f"Description: {obs_data.get('description', '')[:80]}...")

        # Store claim amount for later
        claim_amount = obs_data.get('claim_amount_requested', 0)

        # 2. Query policy
        print("\n[2] Querying policy...")
        step_msg = {
            "type": "step",
            "data": {
                "action_type": "query_policy",
                "parameters": {}
            }
        }
        await ws.send(json.dumps(step_msg))
        response = await ws.recv()
        obs = json.loads(response)
        obs_data = obs.get("data", {})
        print(f"Response: {obs_data.get('system_response', '')[:100]}...")

        # 3. Check fraud
        print("\n[3] Checking fraud signals...")
        step_msg = {
            "type": "step",
            "data": {
                "action_type": "check_fraud",
                "parameters": {}
            }
        }
        await ws.send(json.dumps(step_msg))
        response = await ws.recv()
        obs = json.loads(response)
        obs_data = obs.get("data", {})
        print(f"Response: {obs_data.get('system_response', '')[:150]}...")

        # 4. Verify purchase via Plaid
        print("\n[4] Verifying purchase (Plaid)...")
        step_msg = {
            "type": "step",
            "data": {
                "action_type": "verify_purchase",
                "parameters": {}
            }
        }
        await ws.send(json.dumps(step_msg))
        response = await ws.recv()
        obs = json.loads(response)
        obs_data = obs.get("data", {})
        print(f"Response: {obs_data.get('system_response', '')[:200]}...")

        # 5. Make decision (approve or deny based on fraud)
        revealed = obs_data.get('revealed_info', {})
        fraud_info = revealed.get('fraud_analysis', {})
        fraud_score = fraud_info.get('risk_score', 0) if isinstance(fraud_info, dict) else 0

        print(f"\n[5] Making decision (fraud_score={fraud_score})...")

        if fraud_score > 0.5:
            step_msg = {
                "type": "step",
                "data": {
                    "action_type": "deny",
                    "parameters": {"reason": "High fraud risk detected"}
                }
            }
            print("Decision: DENY (high fraud risk)")
        else:
            step_msg = {
                "type": "step",
                "data": {
                    "action_type": "approve",
                    "parameters": {"payout": claim_amount * 0.9}  # 90% payout
                }
            }
            print(f"Decision: APPROVE (payout: ${claim_amount * 0.9:,.2f})")

        await ws.send(json.dumps(step_msg))
        response = await ws.recv()
        obs = json.loads(response)
        obs_data = obs.get("data", {})

        print(f"\nFinal Response: {obs_data.get('system_response', '')}")
        print(f"Terminal: {obs_data.get('is_terminal', False)}")
        print(f"Reward: {obs_data.get('reward', 'N/A')}")

        # 6. Close session
        close_msg = {"type": "close", "data": {}}
        await ws.send(json.dumps(close_msg))

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_claims_environment())
