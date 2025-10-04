# ResumeRAG - Quick Commands

## Setup and Run

### Docker Compose (Recommended)
```powershell
# Start all services
cd infra
docker-compose up -d

# Run migrations
docker exec resumerag_api alembic upgrade head

# Seed database
docker exec resumerag_api python scripts/seed_data.py

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Local Development
```powershell
# Backend
cd api
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
cd ..
python scripts\seed_data.py
cd api
uvicorn app.main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

## Testing

```powershell
# Run all tests
cd tests
pytest test_api.py -v

# Run specific test
pytest test_api.py::test_upload_idempotency -v
```

## Database

```powershell
# Create migration
cd api
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View current version
alembic current
```

## API Testing

```powershell
# Health check
curl http://localhost:8000/api/health

# Upload resume
curl -X POST http://localhost:8000/api/resumes `
  -H "Idempotency-Key: test-123" `
  -F "file=@resume.pdf" `
  -F "visibility=public"

# Search resumes
curl -X POST http://localhost:8000/api/ask `
  -H "Content-Type: application/json" `
  -d '{"query":"React developer","k":5}'

# Create job
curl -X POST http://localhost:8000/api/jobs `
  -H "Content-Type: application/json" `
  -H "Idempotency-Key: job-123" `
  -d '{"title":"Backend Dev","description":"Python, Django, REST"}'

# Match candidates
curl -X POST http://localhost:8000/api/jobs/job_abc/match `
  -H "Content-Type: application/json" `
  -d '{"top_n":10}'
```

## Useful Docker Commands

```powershell
# View running containers
docker ps

# View logs
docker logs resumerag_api -f

# Execute command in container
docker exec -it resumerag_api bash

# Restart container
docker restart resumerag_api

# View PostgreSQL logs
docker logs resumerag_postgres

# Connect to PostgreSQL
docker exec -it resumerag_postgres psql -U postgres -d resumerag

# Connect to Redis
docker exec -it resumerag_redis redis-cli
```

## Generate OpenAPI Spec

```powershell
cd scripts
python generate_openapi.py
# Output: docs/openapi.yaml and docs/openapi.json
```

## Cleanup

```powershell
# Remove Docker containers and volumes
cd infra
docker-compose down -v

# Clean Python cache
cd api
Get-ChildItem -Path . -Filter "__pycache__" -Recurse | Remove-Item -Recurse -Force

# Clean uploads
Remove-Item uploads\* -Force

# Reset database (local)
psql -U postgres -c "DROP DATABASE IF EXISTS resumerag;"
psql -U postgres -c "CREATE DATABASE resumerag;"
psql -U postgres -d resumerag -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## Environment Variables

Create `.env` file in root:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/resumerag
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
CORS_ALLOWED_ORIGINS=*
PGVECTOR_DIM=1536
```

## Troubleshooting

### Port already in use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

### Database connection error
```powershell
# Check PostgreSQL is running
# Verify DATABASE_URL in .env
# Ensure pgvector extension is installed
```

### Redis connection error
```powershell
# Check Redis is running
docker ps | Select-String redis
# Or start Redis manually
```

### Import errors
```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```
