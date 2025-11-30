from celery import Celery
import os

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
print("Celery Redis URL:", REDIS_URL)

# Create Celery app
celery_application = Celery(
    "online_judge",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks"]  # Auto-discover tasks from tasks.py
)

celery_application.conf.update(
    imports=['tasks.tasks'],
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30,  # Hard limit
    task_soft_time_limit=25,  # Soft limit
)
