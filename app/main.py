import json
import uuid
import os
from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import redis
from app.api.routes import api_router
from app.models import CodeSubmission, SubmissionResponse, ExecutionResult
from tasks.tasks import execute_code

app = FastAPI(title="Online Judge API", version="1.0.0")

app.include_router(api_router)
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis client
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL)


@app.get("/")
def read_root():
    return {"message": "Online Judge API", "version": "1.0.0"}


@app.post("/execute", response_model=SubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_code(submission: CodeSubmission):
    """
    Submit code for execution. Returns a submission ID immediately.
    The code will be executed asynchronously by a worker.
    """
    # Generate unique submission ID
    submission_id = str(uuid.uuid4())
    
    # Store initial status in Redis
    initial_result = {
        "submission_id": submission_id,
        "lang": submission.lang,
        "status": "PENDING",
        "stdout": None,
        "stderr": None,
        "exit_code": None,
        "time_sec": None,
    }
    
    redis_client.setex(
        f"submission:{submission_id}",
        3600,  # 1 hour TTL
        json.dumps(initial_result)
    )
    
    # Queue the task for background execution
    execute_code.delay(
        submission_id=submission_id,
        source_code=submission.source_code,
        stdin_data=submission.stdin_data,
        time_limit_sec=submission.time_limit_sec,
        memory_limit_mb=submission.memory_limit_mb,
        cpu_cores=submission.cpu_cores,
        lang=submission.lang
    )
    
    return SubmissionResponse(
        submission_id=submission_id,
        status="PENDING"
    )


@app.get("/result/{submission_id}", response_model=ExecutionResult)
def get_result(submission_id: str):
    """
    Get the execution result for a submission ID.
    """
    result_json = redis_client.get(f"submission:{submission_id}")
    
    if not result_json:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found or expired"
        )
    
    result = json.loads(result_json)
    return ExecutionResult(**result)


@app.delete("/result/{submission_id}")
def delete_result(submission_id: str):
    """
    Delete a submission result from cache.
    """
    deleted = redis_client.delete(f"submission:{submission_id}")
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found"
        )
    
    return {"message": f"Submission {submission_id} deleted successfully"}

