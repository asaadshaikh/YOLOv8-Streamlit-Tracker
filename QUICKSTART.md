# Quick Start Guide

Get VisionTrack AI up and running in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- 8GB+ RAM recommended
- Python 3.10+ (for local development)

## Option 1: Docker (Recommended)

### Step 1: Clone and Setup

```bash
git clone <your-repo-url>
cd visiontrack-ai
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings (optional for development)
# For production, update SECRET_KEY and database credentials
```

### Step 3: Start Services

```bash
# Development mode
docker-compose up -d

# Or use the helper script
chmod +x scripts/start_dev.sh
./scripts/start_dev.sh
```

### Step 4: Access the Application

- **UI**: http://localhost:8501
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Option 2: Local Development

### Step 1: Setup Python Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Initialize Database

```bash
python scripts/init_db.py
```

### Step 3: Start Services

```bash
# Terminal 1: Start Redis (if not using Docker)
docker run -d -p 6379:6379 redis:7-alpine

# Terminal 2: Start API
uvicorn api.main:app --reload --port 8000

# Terminal 3: Start Streamlit UI
streamlit run streamlit_app.py --server.port 8501

# Terminal 4: Start Celery Worker (optional, for background jobs)
celery -A services.job_service worker --loglevel=info
```

## First Steps

### 1. Create an Admin User

```bash
python scripts/create_admin.py admin admin@example.com yourpassword
```

### 2. Get API Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=yourpassword"
```

Save the `access_token` from the response.

### 3. Test Image Detection

```bash
curl -X POST "http://localhost:8000/api/v1/detect/image" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@path/to/image.jpg" \
  -F "confidence=0.3"
```

### 4. Explore API Documentation

Visit http://localhost:8000/docs for interactive API documentation.

## Common Tasks

### View Logs

```bash
# Docker Compose
docker-compose logs -f

# Specific service
docker-compose logs -f api
```

### Stop Services

```bash
# Development
docker-compose down

# Production
docker-compose -f docker-compose.production.yml down
```

### Reset Database

```bash
# Remove database file (SQLite)
rm visiontrack.db

# Reinitialize
python scripts/init_db.py
```

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=. --cov-report=html
```

## Troubleshooting

### Port Already in Use

Change ports in `docker-compose.yml` or `.env`:

```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

### Model Not Loading

Ensure `yolov8n.pt` is in the project root:

```bash
# Download if missing
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

### Database Connection Error

Check database URL in `.env`:

```env
DATABASE_URL=sqlite:///./visiontrack.db
```

For PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/visiontrack
```

### Redis Connection Error

Ensure Redis is running:

```bash
# Check Redis
docker ps | grep redis

# Start Redis
docker run -d -p 6379:6379 redis:7-alpine
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- Review [PROJECT_UPGRADE_SUMMARY.md](PROJECT_UPGRADE_SUMMARY.md) for features

## Getting Help

- Check logs: `docker-compose logs -f`
- Review API docs: http://localhost:8000/docs
- Open an issue on GitHub

---

**Happy coding! 🚀**

