from tasks.celery_app import celery_application
from app.services.executor import PySandboxExecutor, CppSandboxExecutor
import redis
import json
import os

# Redis client for storing results
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL)

@celery_application.task(name="tasks.execute_code")
def execute_code(submission_id: str, source_code: str, stdin_data: str, 
                 time_limit_sec: float, memory_limit_mb: int, cpu_cores: float, lang: str):
    """
    Background task to execute user code in sandbox
    """
    try:
        # Update status to PROCESSING
        redis_client.setex(
            f"submission:{submission_id}",
            3600,  # 1 hour TTL
            json.dumps({
                "submission_id": submission_id,
                "status": "PROCESSING",
                "stdout": None,
                "stderr": None,
                "exit_code": None,
                "time_sec": None,
            })
        )
        
        # Execute code
        print("Executing code for lang:", lang)
        if lang == "python":
            executor = PySandboxExecutor(
                image="oj-python-runner",
                time_limit_sec=time_limit_sec,
                memory_limit_mb=memory_limit_mb,
                cpu_cores=cpu_cores,
            )
        else:
            executor = CppSandboxExecutor(
                image="oj-cpp-runner",
                time_limit_sec=time_limit_sec,
                memory_limit_mb=memory_limit_mb,
                cpu_cores=cpu_cores,
            )
        print("Running code execution task for submission:", submission_id)
        result = executor.run(source_code=source_code, stdin_data=stdin_data)
        print("Result: ", result)
        # Store result in Redis
        execution_result = {
            "submission_id": submission_id,
            "status": result["status"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "exit_code": result["exit_code"],
            "time_sec": result["time_sec"],
        }
        
        redis_client.setex(
            f"submission:{submission_id}",
            3600,  # 1 hour TTL
            json.dumps(execution_result)
        )
        
        return execution_result
        
    except Exception as e:
        # Store error in Redis
        error_result = {
            "submission_id": submission_id,
            "status": "INTERNAL_ERROR",
            "stdout": None,
            "stderr": str(e),
            "exit_code": None,
            "time_sec": None,
        }
        
        redis_client.setex(
            f"submission:{submission_id}",
            3600,
            json.dumps(error_result)
        )
        
        return error_result
