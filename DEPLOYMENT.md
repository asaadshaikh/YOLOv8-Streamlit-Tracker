# Deployment Guide

## Prerequisites

- Docker and Docker Compose installed
- At least 8GB RAM
- GPU support (optional, for faster inference)
- Domain name and SSL certificates (for production)

## Quick Start (Development)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd visiontrack-ai
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - UI: http://localhost:8501
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Production Deployment

### 1. Environment Configuration

Create a `.env` file with production settings:

```env
# Database
POSTGRES_DB=visiontrack
POSTGRES_USER=visiontrack
POSTGRES_PASSWORD=<strong-password>

# Security
SECRET_KEY=<generate-strong-secret-key>
DEBUG=False

# Redis
REDIS_URL=redis://redis:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
```

### 2. Build and Deploy

```bash
# Build production images
docker-compose -f docker-compose.production.yml build

# Start all services
docker-compose -f docker-compose.production.yml up -d

# Check logs
docker-compose -f docker-compose.production.yml logs -f
```

### 3. SSL/TLS Setup

1. Obtain SSL certificates (Let's Encrypt recommended)
2. Place certificates in `./ssl/` directory
3. Update `nginx.conf` with SSL configuration
4. Restart Nginx container

### 4. Database Migration

```bash
# Initialize database
docker-compose -f docker-compose.production.yml exec api python -c "from database import init_db; init_db()"
```

### 5. Create Admin User

```bash
# Via API
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "secure-password"
  }'
```

## Scaling

### Horizontal Scaling

1. **API Servers**
   ```bash
   # Scale API instances
   docker-compose -f docker-compose.production.yml up -d --scale api=4
   ```

2. **Celery Workers**
   ```bash
   # Scale workers
   docker-compose -f docker-compose.production.yml up -d --scale celery-worker=8
   ```

### Vertical Scaling

- Increase worker concurrency in `docker-compose.production.yml`
- Adjust Redis memory limits
- Configure PostgreSQL connection pool

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/api/v1/metrics
```

### Logs

```bash
# View all logs
docker-compose -f docker-compose.production.yml logs -f

# View specific service
docker-compose -f docker-compose.production.yml logs -f api
```

## Backup & Recovery

### Database Backup

```bash
# Backup
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U visiontrack visiontrack > backup.sql

# Restore
docker-compose -f docker-compose.production.yml exec -T postgres psql -U visiontrack visiontrack < backup.sql
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v visiontrack_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   - Change ports in `docker-compose.production.yml`

2. **Out of memory**
   - Reduce worker concurrency
   - Increase Docker memory limit

3. **Database connection errors**
   - Check PostgreSQL is running
   - Verify connection string in `.env`

4. **Model not loading**
   - Ensure `yolov8n.pt` is in project root
   - Check file permissions

## Kubernetes Deployment

See `k8s/` directory for Kubernetes manifests.

## Performance Tuning

1. **Enable GPU** (if available)
   - Install NVIDIA Docker runtime
   - Update Docker Compose to use GPU

2. **Database Optimization**
   - Add indexes for frequently queried columns
   - Configure connection pooling

3. **Caching**
   - Enable Redis caching for model results
   - Configure cache TTL

4. **CDN**
   - Use CDN for static assets
   - Cache output images/videos

