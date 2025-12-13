#!/bin/bash

echo "⚙️  Starting Celery Worker..."
echo ""
echo "Make sure Redis is running: redis-server &"
echo ""

celery -A tasks.celery_app worker --loglevel=info
