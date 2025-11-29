# Quick Start Guide

## 🚀 Setup in 5 Steps

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Redis
```bash
docker-compose up -d
```

Or if you have Redis installed locally:
```bash
redis-server
```

### 3. Build the Sandbox Docker Image
```bash
cd python-oj
docker build -t oj-python-runner .
cd ..
```

### 4. Start the FastAPI Server (Terminal 1)
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start the Celery Worker (Terminal 2)
```bash
celery -A celery_app worker --loglevel=info
```

## 🧪 Test the System

### Option 1: Using the Client Example
```bash
python client_example.py
```

### Option 2: Using the API Docs
Open http://localhost:8000/docs in your browser

### Option 3: Using cURL
```bash
# Submit code
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"source_code": "print(\"Hello World\")", "stdin_data": ""}'

# Get result (replace {id} with the submission_id from above)
curl http://localhost:8000/result/{id}
```

## 📊 API Endpoints

- `POST /execute` - Submit code for execution
- `GET /result/{submission_id}` - Get execution result
- `DELETE /result/{submission_id}` - Delete result from cache
- `GET /docs` - Interactive API documentation

## 🔍 Monitoring

### Check Celery Workers
```bash
celery -A tasks inspect active
celery -A tasks inspect stats
```

### Check Redis Data
```bash
redis-cli
> KEYS submission:*
> GET submission:{id}
```

### Check FastAPI Logs
The server logs will show all incoming requests

## 🛠️ Troubleshooting

### Redis Connection Error
Make sure Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### Celery Worker Not Processing
Check if worker is running:
```bash
celery -A tasks inspect active
```

### Docker Permission Error
Add your user to docker group:
```bash
sudo usermod -aG docker $USER
# Then logout and login again
```

### Container Not Found Error
Build the Docker image:
```bash
cd python-oj
docker build -t oj-python-runner .
```
