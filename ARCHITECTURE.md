# VisionTrack AI - Architecture Documentation

## System Overview

VisionTrack AI is a production-ready object detection and tracking system built with modern microservices architecture principles.

## Architecture Diagram

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │
       │ HTTP/WebSocket
       │
┌──────▼─────────────────────────────────────┐
│              Nginx (Reverse Proxy)          │
└──────┬─────────────────────────────────────┘
       │
       ├──────────────┬──────────────┐
       │              │              │
┌──────▼──────┐  ┌────▼──────┐  ┌────▼──────┐
│  Streamlit  │  │   FastAPI │  │  WebSocket│
│     UI      │  │    API    │  │  Server   │
└──────┬──────┘  └─────┬─────┘  └───────────┘
       │              │
       │              ├──────────────┐
       │              │              │
┌──────▼──────┐  ┌────▼──────┐  ┌────▼──────┐
│  Detection  │  │  Celery   │  │  Redis    │
│  Service    │  │  Workers  │  │  (Queue)  │
└──────┬──────┘  └─────┬─────┘  └───────────┘
       │              │
       │              │
┌──────▼──────────────▼──────┐
│      PostgreSQL Database    │
└─────────────────────────────┘
```

## Components

### 1. Frontend (Streamlit UI)
- **Technology**: Streamlit
- **Purpose**: Interactive web interface for users
- **Features**:
  - Image upload and detection
  - Video upload and tracking
  - Live webcam feed
  - Analytics dashboard
  - Real-time metrics visualization

### 2. REST API (FastAPI)
- **Technology**: FastAPI, Uvicorn
- **Purpose**: Programmatic access to detection services
- **Features**:
  - JWT authentication
  - Rate limiting
  - Batch processing
  - Session management
  - Export capabilities
  - OpenAPI documentation

### 3. WebSocket Server
- **Technology**: FastAPI WebSocket
- **Purpose**: Real-time updates for background jobs
- **Features**:
  - Job status updates
  - Live progress tracking
  - Connection management

### 4. Background Job Processing (Celery)
- **Technology**: Celery, Redis
- **Purpose**: Async video processing
- **Features**:
  - Task queue management
  - Progress tracking
  - Error handling
  - Scalable workers

### 5. Detection Service
- **Technology**: YOLOv8, DeepSORT, PyTorch
- **Purpose**: Core ML inference
- **Features**:
  - Object detection
  - Object tracking
  - Model management
  - Performance optimization

### 6. Database (PostgreSQL)
- **Technology**: PostgreSQL, SQLAlchemy
- **Purpose**: Data persistence
- **Schema**:
  - Detection sessions
  - Detection records
  - User management
  - Analytics data

### 7. Cache & Queue (Redis)
- **Technology**: Redis
- **Purpose**: 
  - Celery message broker
  - Result backend
  - Caching layer
  - Rate limiting storage

## Data Flow

### Image Detection Flow
1. User uploads image via UI or API
2. Request authenticated (if required)
3. Rate limit checked
4. Image decoded and validated
5. Detection service processes image
6. Results stored in database
7. Annotated image saved
8. Response returned to client
9. Metrics recorded

### Video Processing Flow (Async)
1. User uploads video
2. Video saved to temporary storage
3. Background job created in Celery queue
4. Job ID returned immediately
5. Celery worker picks up job
6. Video processed frame by frame
7. Progress updates sent via WebSocket
8. Results stored in database
9. Output video saved
10. Job status updated
11. Client notified via WebSocket

## Security

### Authentication
- JWT-based authentication
- Password hashing with bcrypt
- Token expiration
- User session management

### Rate Limiting
- Token bucket algorithm
- Per-IP limiting
- Configurable thresholds
- Rate limit headers

### API Security
- CORS configuration
- Input validation
- File type checking
- Size limits
- SQL injection prevention (ORM)

## Scalability

### Horizontal Scaling
- Stateless API servers
- Multiple Celery workers
- Load balancing with Nginx
- Database connection pooling

### Performance Optimization
- Model caching
- Result caching (Redis)
- Async processing
- Batch operations
- Database indexing

## Monitoring & Observability

### Metrics
- Prometheus-compatible metrics
- Request counts
- Response times
- Error rates
- System health

### Logging
- Structured logging
- Log levels (DEBUG, INFO, WARNING, ERROR)
- File and console output
- Request tracing

### Health Checks
- API health endpoint
- Database connectivity
- Model loading status
- Service dependencies

## Deployment

### Development
- Docker Compose
- SQLite database
- Single worker

### Production
- Kubernetes-ready
- PostgreSQL database
- Multiple workers
- Nginx reverse proxy
- SSL/TLS support
- Health checks
- Auto-restart policies

## Technology Stack

- **Backend**: Python 3.10
- **Web Framework**: FastAPI, Streamlit
- **ML Framework**: PyTorch, Ultralytics YOLOv8
- **Tracking**: DeepSORT
- **Database**: PostgreSQL, SQLAlchemy
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **Containerization**: Docker
- **Reverse Proxy**: Nginx
- **CI/CD**: GitHub Actions

