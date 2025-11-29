# Online Judge - Async Code Execution System

An asynchronous code execution system using FastAPI, Celery, and Redis.

## Architecture

1. **Client submits code** → POST `/execute`
2. **API returns submission ID** immediately
3. **Task queued in Redis** (Celery broker)
4. **Worker picks up task** and executes code in sandbox
5. **Result stored in Redis** with TTL (1 hour)
6. **Client polls for result** → GET `/result/{submission_id}`

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Redis

Using Docker:
```bash
sudo apt install redis
redis-sever &
```

### 3. Build Docker Image for Code Execution

```bash
cd python-oj
docker build -t oj-python-runner .
cd ..
```

### 4. Start the FastAPI Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start the Celery Worker

In a new terminal:
```bash
celery -A celery_app worker --loglevel=info
```

## API Endpoints

### Submit Code for Execution

**POST** `/execute`

Request body:
```json
{
  "source_code": "print('Hello, World!')",
  "stdin_data": "",
  "time_limit_sec": 2.0,
  "memory_limit_mb": 256,
  "cpu_cores": 1.0
}
```

Response:
```json
{
  "submission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "PENDING"
}
```

### Get Execution Result

**GET** `/result/{submission_id}`

Response:
```json
{
  "submission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "OK",
  "stdout": "Hello, World!\n",
  "stderr": null,
  "exit_code": 0,
  "time_sec": 0.123
}
```

Status values:
- `PENDING`: Queued, waiting for worker
- `PROCESSING`: Currently being executed
- `OK`: Executed successfully
- `TLE`: Time Limit Exceeded
- `RE`: Runtime Error
- `INTERNAL_ERROR`: System error

### Delete Result

**DELETE** `/result/{submission_id}`

## Example Usage

### Using cURL

```bash
# Submit code
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "n = int(input())\nprint(n * 2)",
    "stdin_data": "5\n"
  }'

# Get result (use the submission_id from above)
curl http://localhost:8000/result/{submission_id}
```

### Using Python

```python
import requests
import time

# Submit code
response = requests.post(
    "http://localhost:8000/execute",
    json={
        "source_code": "n = int(input())\nprint(n * 2)",
        "stdin_data": "5\n"
    }
)
submission_id = response.json()["submission_id"]
print(f"Submission ID: {submission_id}")

# Poll for result
while True:
    result = requests.get(f"http://localhost:8000/result/{submission_id}").json()
    print(f"Status: {result['status']}")
    
    if result["status"] not in ["PENDING", "PROCESSING"]:
        print(f"Result: {result}")
        break
    
    time.sleep(0.5)
```

## Monitoring

### Check Celery Workers
```bash
celery -A tasks inspect active
celery -A tasks inspect stats
```

### Check Redis
```bash
redis-cli
> KEYS submission:*
> GET submission:{submission_id}
```

## Environment Variables

Create a `.env` file:
```
REDIS_URL=redis://localhost:6379/0
```

## Production Considerations

1. **Persistence**: Consider using PostgreSQL/MongoDB for long-term storage
2. **Scaling**: Add more Celery workers for concurrent execution
3. **Monitoring**: Add Flower for Celery monitoring
4. **Rate Limiting**: Implement rate limiting on submission endpoint
5. **Authentication**: Add JWT/API key authentication
6. **Result Retention**: Implement cleanup job for old results
