@echo off
echo Starting VyaparMind Scalable API Provider...
echo mode: PRODUCTION
echo workers: 8

:: Set environment variables if needed
:: set REDIS_URL=redis://localhost:6379

:: Start Uvicorn with 8 workers for high concurrency
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 8
