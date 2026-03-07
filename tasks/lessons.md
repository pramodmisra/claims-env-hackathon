# Lessons Learned - OpenEnv Hackathon

## OpenEnv Framework

### 1. Session Management (Critical)
OpenEnv REST endpoints (`/reset`, `/step`) are **stateless** - each request creates a new environment instance. For multi-step RL episodes, you MUST use WebSocket (`/ws`).

### 2. Observation Serialization
When creating custom `Observation` subclasses:
- OpenEnv's `serialize_observation()` extracts `observation.reward` and `observation.done`
- Your observation MUST have these fields set, not just custom fields like `is_terminal`
- The base `Observation` class already defines `reward` and `done` fields
- After `step()`, explicitly set: `observation.reward = reward` and `observation.done = is_terminal`

### 3. Environment Factory Pattern
`create_fastapi_app()` expects an environment **class**, not an instance:
```python
# WRONG
env = ClaimsEnvironment()
app = create_fastapi_app(env, ...)

# RIGHT
app = create_fastapi_app(ClaimsEnvironment, ...)
```

## HuggingFace Spaces

### 1. Docker Cache Busting
When code changes aren't being picked up:
- Check runtime SHA: `curl -s "https://huggingface.co/api/spaces/{space}/runtime"`
- Force rebuild by modifying `requirements.txt` (add comment with timestamp)
- Factory restart: `curl -X POST ".../{space}/restart?factory=true"`

### 2. Build Times
Docker builds on HF Spaces can take 2-3 minutes. Always verify runtime SHA matches your commit SHA before testing.

## Colab/Jupyter

### 1. Event Loop Issues
Use `nest_asyncio` for async code in Jupyter:
```python
import nest_asyncio
nest_asyncio.apply()
```

### 2. SSL for WebSockets
Colab needs explicit SSL context for WSS connections:
```python
import ssl, certifi
ssl_context = ssl.create_default_context(cafile=certifi.where())
async with websockets.connect(url, ssl=ssl_context) as ws:
    ...
```

## Pydantic Models

### 1. Type Inheritance
When subclassing Pydantic models:
- Child class can narrow types (e.g., `float` instead of `float | None`)
- But be careful with `extra="forbid"` - all fields must be defined
- Use `validate_assignment=True` to allow setting fields after creation
