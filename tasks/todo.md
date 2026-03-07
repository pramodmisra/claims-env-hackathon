# OpenEnv Hackathon - Insurance Claims RL Environment

## Status: Local Testing Complete, HF Space Deploying

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

### In Progress
- [ ] HF Space: https://huggingface.co/spaces/pramodmisra/claims-env (STATUS: APP_STARTING)

### Pending (User Action Required)
- [ ] Run training notebook on Colab Pro (requires GPU)
- [ ] Save reward_curves.png from training
- [ ] Record 1-minute YouTube demo video
- [ ] Submit to hackathon portal: https://openenv-hackathon.devpost.com
- [ ] Deadline: Sunday 1PM Pacific

## Key Finding: OpenEnv Session Management

**Important**: OpenEnv's REST endpoints (`/reset`, `/step`) are **stateless** - each request creates a new environment instance.

For stateful multi-step episodes, use **WebSocket** connection to `/ws`:
```python
async with websockets.connect("wss://your-space.hf.space/ws") as ws:
    await ws.send('{"type": "reset", "data": {}}')
    response = await ws.recv()
    # ... process claim ...
    await ws.send('{"type": "step", "data": {"action_type": "query_policy"}}')
```

## Test Commands

### Local Server
```bash
cd /Users/pramodmisra/Claude/openenv-hackathon/claims_env
python3 -m uvicorn space_app:app --port 7860 --host 127.0.0.1

# In another terminal:
python3 demo_claims.py
```

### HF Space (when ready)
```bash
# Test via WebSocket
python3 -c "
import asyncio, websockets, json
async def test():
    async with websockets.connect('wss://pramodmisra-claims-env.hf.space/ws') as ws:
        await ws.send(json.dumps({'type': 'reset', 'data': {}}))
        print(await ws.recv())
asyncio.run(test())
"
```

## Links
- **GitHub**: https://github.com/pramodmisra/claims-env-hackathon
- **HF Space**: https://huggingface.co/spaces/pramodmisra/claims-env
- **Problem Statement**: 3.1 Professional Tasks + Scaler AI Labs
