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

### Option B: Full Stack Fix (CHOSEN)
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

## Implementation: Option B

### Step 1: Add `redis` to `requirements.txt`
```
redis
```

### Step 2: Add Redis service to `docker-compose.yml`
```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: customer-feedback-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

### Step 3: Update `docker-compose.yml` app service to depends_on redis
```yaml
services:
  app:
    depends_on:
      - redis
```

### Step 4: Update `.env`
```
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_ENABLED=true
```

### Step 5: Rebuild and start
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Redis Host Configuration

| Environment | `REDIS_HOST` value |
|-------------|-------------------|
| **Docker (containerized)** | `redis` (service name in docker-compose) |
| **Local machine** | `localhost` |

Choose based on where Redis runs:
- **Docker**: App inside container talks to `redis://redis:6379`
- **Local**: App inside container talks to `host.docker.internal:6379` or `localhost` (if port exposed)
