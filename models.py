from pydantic import BaseModel
from typing import Optional, Literal

class CodeSubmission(BaseModel):
    source_code: str
    stdin_data: str = ""
    time_limit_sec: float = 2.0
    memory_limit_mb: int = 256
    cpu_cores: float = 1.0

class SubmissionResponse(BaseModel):
    submission_id: str
    status: str = "PENDING"

class ExecutionResult(BaseModel):
    submission_id: str
    status: Literal["PENDING", "PROCESSING", "OK", "TLE", "RE", "INTERNAL_ERROR"]
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    time_sec: Optional[float] = None
