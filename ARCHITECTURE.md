# Architecture Overview

## System Flow

```
┌─────────────┐
│   Client    │
│  (Browser/  │
│   Python)   │
└──────┬──────┘
       │
       │ 1. POST /execute
       │    {source_code, stdin_data, ...}
       ▼
┌─────────────────────────────────────────┐
│         FastAPI Server (main.py)        │
│                                         │
│  • Generate submission_id (UUID)        │
│  • Store PENDING status in Redis        │
│  • Queue task to Celery                 │
│  • Return submission_id immediately     │
└──────┬──────────────────────┬───────────┘
       │                      │
       │ 2. Return            │ 3. Queue task
       │    submission_id     │
       │                      ▼
       │              ┌───────────────┐
       │              │  Redis Queue  │
       │              │   (Celery     │
       │              │    Broker)    │
       │              └───────┬───────┘
       │                      │
       │                      │ 4. Pick task
       │                      ▼
       │              ┌─────────────────────┐
       │              │  Celery Worker      │
       │              │   (tasks.py)        │
       │              │                     │
       │              │  • Update status to │
       │              │    PROCESSING       │
       │              │  • Execute code in  │
       │              │    Docker sandbox   │
       │              │  • Store result     │
       │              └──────────┬──────────┘
       │                         │
       │                         │ 5. Store result
       │                         ▼
       │              ┌─────────────────────┐
       │              │   Redis Storage     │
       │              │                     │
       │              │  submission:{id} ─► │
       │              │  {status, stdout,   │
       │              │   stderr, time,...} │
       │              └─────────────────────┘
       │                         ▲
       │ 6. GET /result/{id}     │
       │                         │
       └─────────────────────────┘
```

## Components

### 1. **FastAPI Server** (`main.py`)
- Handles HTTP requests
- Generates unique submission IDs
- Queues tasks to Celery
- Returns results from Redis

### 2. **Celery Worker** (`tasks.py`)
- Processes execution tasks asynchronously
- Runs code in Docker sandbox
- Updates status in Redis
- Handles errors and timeouts

### 3. **Redis**
- **Queue**: Celery task queue (broker)
- **Storage**: Execution results with 1-hour TTL
- **Cache**: Fast access to submission status

### 4. **Docker Sandbox** (`executor.py`)
- Isolated execution environment
- Resource limits (CPU, Memory, Time)
- Network disabled for security
- Auto-cleanup after execution

## Data Models

### CodeSubmission (Input)
```json
{
  "source_code": "string",
  "stdin_data": "string",
  "time_limit_sec": 2.0,
  "memory_limit_mb": 256,
  "cpu_cores": 1.0
}
```

### SubmissionResponse (Immediate)
```json
{
  "submission_id": "uuid",
  "status": "PENDING"
}
```

### ExecutionResult (Final)
```json
{
  "submission_id": "uuid",
  "status": "OK|TLE|RE|INTERNAL_ERROR",
  "stdout": "string|null",
  "stderr": "string|null",
  "exit_code": "int|null",
  "time_sec": "float|null"
}
```

## Status Flow

```
PENDING ──► PROCESSING ──► OK
                      ├──► TLE (Time Limit Exceeded)
                      ├──► RE (Runtime Error)
                      └──► INTERNAL_ERROR
```

## Scaling Strategies

### Horizontal Scaling
- Add more Celery workers
- Use Redis Cluster for high availability
- Load balance FastAPI with nginx

### Optimization
- Implement connection pooling
- Use result caching
- Add rate limiting per user
- Implement batch execution

### Monitoring
- Celery Flower for task monitoring
- Redis monitoring with RedisInsight
- FastAPI metrics with Prometheus
- Logging with ELK stack
