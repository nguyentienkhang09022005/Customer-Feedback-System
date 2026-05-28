# How to Self Test

Tài liệu này hướng dẫn bạn tự chạy test cho repo `Customer-Feedback-System` theo các mức: nhanh, theo tầng test, theo file cụ thể, gần production với PostgreSQL, và coverage.

## 1. Điều kiện trước khi chạy

Ưu tiên dùng Python trong virtualenv của repo:

```bash
.venv/bin/python -m pytest --version
```

Nếu lệnh trên chạy được, bạn có thể dùng toàn bộ các lệnh bên dưới.

## 2. Smoke test nhanh

Nếu bạn chỉ muốn kiểm tra nhanh những phần đã được thêm/chỉnh gần đây:

```bash
.venv/bin/python -m pytest tests/test_evaluate.py tests/test_load_balancer.py tests/test_system_e2e.py -q --disable-warnings
```

Sau đó chạy thêm integration file mới:

```bash
.venv/bin/python -m pytest tests/test_integration_critical_flows.py -q
```

## 3. Chạy toàn bộ test

```bash
.venv/bin/python -m pytest tests/ -q --tb=short
```

Nếu muốn xem chi tiết hơn:

```bash
.venv/bin/python -m pytest tests/ -v --tb=short
```

## 4. Chạy theo marker

Repo hiện đã có marker trong `pytest.ini`.

### Unit test

```bash
.venv/bin/python -m pytest tests/ -m "unit" -q
```

### Integration test

```bash
.venv/bin/python -m pytest tests/ -m "integration" -q
```

### System / E2E test

```bash
.venv/bin/python -m pytest tests/ -m "system" -q
```

### Test chậm

```bash
.venv/bin/python -m pytest tests/ -m "slow" -q
```

### Unit test nhưng bỏ slow

```bash
.venv/bin/python -m pytest tests/ -m "unit and not slow" -q
```

## 5. Chạy theo file cụ thể

### Unit-related

```bash
.venv/bin/python -m pytest tests/test_evaluate.py tests/test_load_balancer.py -q
```

### Integration mới

```bash
.venv/bin/python -m pytest tests/test_integration_critical_flows.py -q
```

### System / E2E mới

```bash
.venv/bin/python -m pytest tests/test_system_e2e.py -q -rs
```

`-rs` sẽ hiện lý do các test bị skip.

## 6. Chạy giống các layer trong CI

### Layer 1 - Unit

```bash
.venv/bin/python -m pytest tests/ \
  --ignore=tests/test_api_integration.py \
  --ignore=tests/test_integration_critical_flows.py \
  --ignore=tests/test_system_e2e.py \
  -q --tb=short
```

### Layer 2 - Integration

```bash
.venv/bin/python -m pytest \
  tests/test_api_integration.py \
  tests/test_integration_critical_flows.py \
  -q --tb=short
```

### Layer 3 - System / E2E

```bash
.venv/bin/python -m pytest tests/test_system_e2e.py -q --tb=short
```

## 7. Chạy với PostgreSQL

Nếu bạn muốn test gần production hơn:

### Bật PostgreSQL test container

```bash
docker compose -f docker-compose.test.yml up -d
```

### Chạy test với Postgres

```bash
TEST_DATABASE_URL="postgresql://testuser:testpass@localhost:5433/testdb" \
.venv/bin/python -m pytest tests/ -q --tb=short
```

### Tắt PostgreSQL khi xong

```bash
docker compose -f docker-compose.test.yml down
```

## 8. Chạy coverage

```bash
.venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=xml -q
```

Nếu muốn tạo HTML report:

```bash
.venv/bin/coverage html
```

Mở file:

```bash
htmlcov/index.html
```

## 9. Thứ tự chạy được khuyên dùng

Nếu bạn muốn chạy từ nhẹ đến nặng:

### Bước 1: smoke test

```bash
.venv/bin/python -m pytest tests/test_evaluate.py tests/test_load_balancer.py tests/test_system_e2e.py -q --disable-warnings
```

### Bước 2: integration mới

```bash
.venv/bin/python -m pytest tests/test_integration_critical_flows.py -q
```

### Bước 3: full suite

```bash
.venv/bin/python -m pytest tests/ -q --tb=short
```

### Bước 4: PostgreSQL mode nếu cần

```bash
TEST_DATABASE_URL="postgresql://testuser:testpass@localhost:5433/testdb" \
.venv/bin/python -m pytest tests/ -q --tb=short
```

## 10. Nếu gặp lỗi thường gặp

### Không tìm thấy pytest

Hãy dùng đúng Python trong `.venv`:

```bash
.venv/bin/python -m pytest ...
```

### Có test bị skip

Chạy với `-rs` để xem lý do:

```bash
.venv/bin/python -m pytest tests/test_system_e2e.py -q -rs
```

### Muốn chỉ kiểm tra marker có hoạt động không

```bash
.venv/bin/python -m pytest tests/ -m "system" --collect-only -q
.venv/bin/python -m pytest tests/ -m "integration" --collect-only -q
.venv/bin/python -m pytest tests/ -m "unit" --collect-only -q
```
