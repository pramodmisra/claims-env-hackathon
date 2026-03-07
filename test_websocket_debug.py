#!/usr/bin/env python3
"""Debug WebSocket test - shows raw responses."""

import asyncio
import json
import websockets

ENV_URL = "ws://127.0.0.1:7860/ws"

async def test_debug():
    print("Connecting to WebSocket...")

    async with websockets.connect(ENV_URL) as ws:
        # Reset
        reset_msg = {"type": "reset", "data": {}}
        await ws.send(json.dumps(reset_msg))
        response = await ws.recv()

        print("\n=== RAW RESET RESPONSE ===")
        print(response)
        print("\n=== PARSED ===")
        parsed = json.loads(response)
        print(json.dumps(parsed, indent=2))

        # Step
        step_msg = {"type": "step", "data": {"action_type": "query_policy", "parameters": {}}}
        await ws.send(json.dumps(step_msg))
        response = await ws.recv()

        print("\n=== RAW STEP RESPONSE ===")
        print(response)
        print("\n=== PARSED ===")
        parsed = json.loads(response)
        print(json.dumps(parsed, indent=2))

if __name__ == "__main__":
    asyncio.run(test_debug())
