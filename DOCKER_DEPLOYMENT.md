# 🐳 Docker Deployment Guide

This guide explains how to run ResumeRAG using Docker containers.

## 📋 Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+
- At least 4GB of available RAM
- 10GB of free disk space

## 🚀 Quick Start

### Option 1: Using the Startup Script (Windows)

```powershell
.\start-docker.ps1
```

This will:
- Build all containers
- Start all services
- Display service status and URLs

### Option 2: Manual Docker Compose

```bash
cd infra
docker-compose up --build -d
```

## 📦 Services

The Docker setup includes:

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | React UI with Nginx |
| Backend API | 8000 | FastAPI application |
| PostgreSQL | 5432 | Database with pgvector |
| Redis | 6379 | Caching & rate limiting |
| MinIO | 9000/9001 | Object storage (optional) |

## 🌐 Access URLs

Once running, access:

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/api/health
- **MinIO Console**: http://localhost:9001

## 🔧 Configuration

### Environment Variables

Edit `infra/docker-compose.yml` to customize:

```yaml
environment:
  DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/resumerag
  REDIS_URL: redis://redis:6379/0
  SECRET_KEY: your-secret-key-here
  CORS_ALLOWED_ORIGINS: "*"
```

### Production Considerations

For production, update:
- `SECRET_KEY` to a strong random value
- `CORS_ALLOWED_ORIGINS` to specific domains
- Database credentials
- Add SSL/TLS certificates
- Use managed database services

## 📊 Management Commands

### View Logs

```bash
# All services
docker-compose -f infra/docker-compose.yml logs -f

# Specific service
docker-compose -f infra/docker-compose.yml logs -f frontend
docker-compose -f infra/docker-compose.yml logs -f api
```

### Check Status

```bash
docker-compose -f infra/docker-compose.yml ps
```

### Restart Services

```bash
# All services
docker-compose -f infra/docker-compose.yml restart

# Specific service
docker-compose -f infra/docker-compose.yml restart frontend
```

### Stop Services

```bash
# Using script (Windows)
.\stop-docker.ps1

# Or manually
docker-compose -f infra/docker-compose.yml down
```

### Stop and Remove Volumes (⚠️ Deletes all data)

```bash
docker-compose -f infra/docker-compose.yml down -v
```

## 🔍 Troubleshooting

### Frontend can't connect to API

1. Check if API is healthy:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. Check API logs:
   ```bash
   docker-compose -f infra/docker-compose.yml logs api
   ```

3. Verify network connectivity:
   ```bash
   docker network inspect infra_resumerag-network
   ```

### Database connection issues

1. Check PostgreSQL is running:
   ```bash
   docker-compose -f infra/docker-compose.yml ps postgres
   ```

2. Check database logs:
   ```bash
   docker-compose -f infra/docker-compose.yml logs postgres
   ```

3. Test connection:
   ```bash
   docker exec resumerag_postgres pg_isready -U postgres
   ```

### Out of memory errors

Increase Docker Desktop memory allocation:
- Windows/Mac: Docker Desktop → Settings → Resources → Memory
- Recommended: 4GB minimum, 8GB ideal

### Port already in use

If ports are occupied, change them in `docker-compose.yml`:

```yaml
ports:
  - "3001:80"  # Change 3000 to 3001
```

## 🔄 Rebuild After Code Changes

### Frontend changes:
```bash
docker-compose -f infra/docker-compose.yml up --build -d frontend
```

### Backend changes:
```bash
docker-compose -f infra/docker-compose.yml up --build -d api
```

### All services:
```bash
docker-compose -f infra/docker-compose.yml up --build -d
```

## 🧹 Cleanup

### Remove stopped containers:
```bash
docker container prune
```

### Remove unused images:
```bash
docker image prune -a
```

### Full cleanup (⚠️ removes everything):
```bash
docker system prune -a --volumes
```

## 📈 Performance Tips

1. **Use volumes for development**: Mounted volumes allow hot-reload
2. **Multi-stage builds**: Frontend uses multi-stage build for optimization
3. **Health checks**: All services have health checks for reliability
4. **Network optimization**: Services use bridge network for fast communication
5. **Gzip compression**: Nginx enables gzip for faster frontend loading

## 🔐 Security Notes

- Change default passwords before production
- Use environment files (.env) for secrets
- Enable HTTPS with reverse proxy (Nginx/Traefik)
- Restrict CORS origins
- Use Docker secrets for sensitive data
- Regularly update base images

## 📝 Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ :3000
┌──────▼──────────┐
│  Frontend       │
│  (Nginx)        │
└──────┬──────────┘
       │ /api → :8000
┌──────▼──────────┐      ┌──────────────┐
│  Backend API    │─────▶│  PostgreSQL  │
│  (FastAPI)      │      │  (pgvector)  │
└──────┬──────────┘      └──────────────┘
       │
┌──────▼──────────┐
│     Redis       │
│   (Cache)       │
└─────────────────┘
```

## 🆘 Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify Docker is running: `docker info`
3. Check disk space: `docker system df`
4. Review GitHub Issues: [ResumeRAG Issues](https://github.com/ChetanAnandaReddyKukutla/ResumeRAG/issues)

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Nginx Configuration](https://nginx.org/en/docs/)
