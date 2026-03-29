# Fix: Missing Redis Module

## Error Summary

```
ModuleNotFoundError: No module named 'redis'
```

## Root Cause

The `redis` Python package is imported in [`app/services/redisService.py:1`](app/services/redisService.py:1) but is **not listed** in [`requirements.txt`](requirements.txt:1).

## Import Chain

```
app/api/dependencies.py:24
  └─> from app.services.tokenBlacklistService import TokenBlacklistService
        └─> from app.services.redisService import redis_service
              └─> import redis  ← FAILS
```

## Evidence

| File | Status |
|------|--------|
| `requirements.txt` | ❌ Missing `redis` |
| `docker-compose.yml` | ❌ No Redis service |
| `app/core/config.py:25-30` | ✅ Redis config exists (host: localhost, port: 6379) |

---

## Fix Options

### Option A: Minimal Fix
Add `redis` to `requirements.txt` only.
- **Pros**: Simple, one-line change
- **Cons**: Requires manual Redis server setup

### Option B: Full Stack Fix
1. Add `redis` to `requirements.txt`
2. Add Redis container to `docker-compose.yml`
3. Configure `.env` with `REDIS_HOST=redis`

- **Pros**: Complete solution with Docker
- **Cons**: More changes

### Option C: Disable Redis
Set `REDIS_ENABLED=false` in `.env`
- **Pros**: App works without Redis
- **Cons**: Token blacklist features disabled

---

## Recommended: Option A (Minimal)

Add to `requirements.txt`:
```
redis
```

Then install: `pip install redis`

---

## Verification

After fix, restart the server:
```bash
uvicorn main:app --reload
```

The error should be resolved. If Redis server is not running, you'll see:
```
⚠️ Redis is disabled
```
or connection errors in logs, but the app will start.
