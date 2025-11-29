#!/bin/bash
# filepath: /home/tanishq/Tanishq/OnlineJudge/start_worker.sh

echo "⚙️  Starting Celery Worker..."
echo ""
echo "Make sure Redis is running: redis-server &"
echo ""

celery -A celery_app worker --loglevel=info
