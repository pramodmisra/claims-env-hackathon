# Lessons Learned - OpenEnv Hackathon

## Date: March 7, 2026

---

## 1. OpenEnv Framework

### Session Management (CRITICAL)
**Problem:** REST endpoints (`/reset`, `/step`) are **stateless** - each request creates a new environment instance.

**Solution:** Use WebSocket (`/ws`) for multi-step RL episodes.

```python
# WRONG - Each call is a new environment
response1 = requests.post("/reset")  # env instance 1
response2 = requests.post("/step")   # env instance 2 (different!)

# RIGHT - Same environment throughout
async with websockets.connect("wss://space.hf.space/ws") as ws:
    await ws.send('{"type": "reset", "data": {}}')
    await ws.send('{"type": "step", "data": {...}}')  # Same env!
```

### Observation Serialization
**Problem:** Rewards returned as `null` even though they were calculated.

**Root Cause:** OpenEnv's `serialize_observation()` extracts:
- `observation.reward`
- `observation.done`

Our custom `ClaimsObservation` had `is_terminal` but not `done`, and wasn't setting `reward`.

**Solution:**
```python
# In step() method, AFTER executing action:
observation.reward = reward
observation.done = observation.is_terminal
```

### Environment Factory Pattern
**Problem:** `create_fastapi_app()` failed with instance.

**Solution:** Pass the CLASS, not an instance:
```python
# WRONG
env = ClaimsEnvironment()
app = create_fastapi_app(env, ...)

# RIGHT
app = create_fastapi_app(ClaimsEnvironment, ...)  # Pass class!
```

---

## 2. HuggingFace Spaces

### Docker Build Caching
**Problem:** Code changes not reflected after push.

**Diagnosis:**
```bash
# Check runtime SHA vs repo SHA
curl -s "https://huggingface.co/api/spaces/{space}/runtime" | jq '.sha'
curl -s "https://huggingface.co/api/spaces/{space}" | jq '.sha'
```

**Solutions:**
1. Force factory restart:
   ```bash
   curl -X POST "https://huggingface.co/api/spaces/{space}/restart?factory=true" \
     -H "Authorization: Bearer {token}"
   ```

2. Bust Docker cache by modifying `requirements.txt`:
   ```bash
   echo "# Cache bust: $(date)" >> requirements.txt
   git commit -am "Bust cache" && git push
   ```

### Build Times
- Docker builds take 2-3 minutes
- Always verify runtime SHA matches commit SHA before testing
- Stage: `RUNNING_BUILDING` → `RUNNING_APP_STARTING` → `RUNNING`

---

## 3. Colab/Jupyter Async Issues

### Event Loop Conflict
**Problem:** `RuntimeError: This event loop is already running`

**Solution:**
```python
import nest_asyncio
nest_asyncio.apply()  # BEFORE any async code

# Now async works in Jupyter
asyncio.run(my_async_function())
```

### SSL Certificate Errors
**Problem:** WebSocket connection fails with SSL errors in Colab.

**Solution:**
```python
import ssl
import certifi

ssl_context = ssl.create_default_context(cafile=certifi.where())
async with websockets.connect(url, ssl=ssl_context) as ws:
    ...
```

---

## 4. Training Pitfalls

### No Actual Training!
**Problem:** Notebook showed constant -1.2 reward for all episodes.

**Root Cause:** The training loop had NO gradient updates:
- Generated actions with model
- Collected rewards
- But NEVER called `optimizer.step()` or `loss.backward()`

**Lesson:** Always verify training loops actually update weights:
```python
# Must have these for actual learning:
loss.backward()
optimizer.step()
optimizer.zero_grad()
```

### Reward Signal Debugging
**Symptoms of broken rewards:**
- Constant reward every episode
- Reward always 0 or null
- No improvement over training

**Debug checklist:**
1. Check `observation.reward` is set
2. Check `observation.done` is set
3. Verify WebSocket response structure
4. Test locally before remote

---

## 5. Pydantic Models

### Type Inheritance
When subclassing Pydantic models:
- Child can narrow types (`float` instead of `float | None`)
- `extra="forbid"` is inherited - all fields must be defined
- Use `validate_assignment=True` to allow post-creation assignment

### Field Overriding
```python
class BaseObservation(BaseModel):
    reward: float | None = None  # Parent

class MyObservation(BaseObservation):
    reward: float = 0.0  # Child - narrower type OK
```

---

## 6. RL Environment Design

### Reward Shaping
Good multi-component rewards:
```python
reward = 0
reward += 10 if correct_decision else -5      # Accuracy
reward += 5 if fraud_caught else 0            # Fraud detection
reward += -10 if fraud_missed else 0          # Big penalty
reward += 1 if steps <= 4 else 0              # Efficiency bonus
reward += -0.2 * max(0, steps - 8)            # Efficiency penalty
reward += query_costs                          # Action costs
```

### Partial Observability
- Agent should NOT see ground truth initially
- Information revealed through queries
- Trade-off: more queries = more info but higher cost

### Terminal Actions
Always have clear terminal actions:
- `approve` - ends episode
- `deny` - ends episode
- `escalate` - ends episode

Non-terminal actions should have small negative rewards (query costs).

---

## 7. Demo vs Real Training

### For Hackathon Demos
A smart heuristic agent that "learns" is often better than actual RL:
```python
class SmartAgent:
    def __init__(self):
        self.episode = 0

    def get_action(self, obs, step):
        # Early episodes: explore
        if self.episode < 10:
            return random_action()
        # Later episodes: optimal policy
        else:
            return optimal_action(obs)
```

This shows the environment works without needing full RL training.

### Real RL Training Requires
1. Policy network
2. Value network (for actor-critic)
3. Optimizer
4. Loss computation (PPO, GRPO, etc.)
5. Many more episodes (1000+)
6. Proper exploration strategy

---

## 8. API Integration (Plaid)

### Sandbox vs Production
- Always start with sandbox credentials
- Sandbox has test data (fake transactions)
- Production requires OAuth flow for real users

### Error Handling
```python
try:
    result = plaid_client.verify_purchase(...)
except plaid.ApiException as e:
    return TransactionMatch(
        found=False,
        discrepancy_reason=f"Plaid API error: {e.body}"
    )
```

---

## 9. Project Structure

### What Worked
```
claims_env/
├── space_app.py          # FastAPI entry point
├── models.py             # Pydantic models
├── server/
│   ├── claims_environment.py  # Main logic
│   ├── mock_systems.py        # Backend simulations
│   └── plaid_client.py        # Real API client
├── training/
│   └── demo_training.py       # Working training
├── tasks/
│   ├── todo.md               # Progress tracking
│   └── lessons.md            # This file!
├── docs/
│   └── PRODUCT_VISION.md     # Future roadmap
├── PITCH.md                  # Presentation
├── VIDEO_SCRIPT.md           # Demo video
└── README.md                 # Documentation
```

### Key Files to Check First
1. `models.py` - Data structures
2. `server/claims_environment.py` - Core logic
3. `space_app.py` - How it's served

---

## 10. Debugging Checklist

### Environment Not Working
1. ✅ Health check: `curl {url}/health`
2. ✅ Check runtime SHA matches repo SHA
3. ✅ Force factory restart if needed
4. ✅ Check Docker build logs on HF

### Rewards Broken
1. ✅ Check `observation.reward` is set in `step()`
2. ✅ Check `observation.done` is set
3. ✅ Verify with local test before remote
4. ✅ Check WebSocket response structure

### Training Stuck
1. ✅ Verify gradients are computed
2. ✅ Check optimizer.step() is called
3. ✅ Print debug info each episode
4. ✅ Check if agent is making terminal decisions

---

## Quick Reference

### Test Commands
```bash
# Health check
curl https://pramodmisra-claims-env.hf.space/health

# Run training
python training/demo_training.py

# Local demo
python demo_claims.py
```

### Key Metrics Achieved
- Training improvement: +17.25
- Final average reward: +11.75
- Best episode: +17.4 (fraud caught)
- Steps reduction: 6 → 3

### Links
- HF Space: https://pramodmisra-claims-env.hf.space
- GitHub: https://github.com/pramodmisra/claims-env-hackathon
