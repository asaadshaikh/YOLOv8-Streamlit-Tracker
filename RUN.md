# 🚀 How to Run VisionTrack AI

## Quick Start (Easiest Method)

### Step 1: Make sure Docker is running
- Open Docker Desktop (if on Windows/Mac)
- Or ensure Docker daemon is running (Linux)

### Step 2: Open terminal in project folder
```bash
cd "D:\Projects\VisionTrack AI"
```

### Step 3: Start the application
```bash
docker-compose up --build
```

**Note**: First time will take 5-10 minutes to download and build everything.

### Step 4: Wait for services to start
You'll see logs like:
```
visiontrack-api  | INFO:     Uvicorn running on http://0.0.0.0:8000
visiontrack-ui   | You can now view your Streamlit app in your browser.
```

### Step 5: Open in browser
- **UI (Streamlit)**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## What You'll See

### 1. Streamlit UI (http://localhost:8501)
- Beautiful web interface
- Upload images/videos
- Live webcam tracking
- Analytics dashboard

### 2. API Documentation (http://localhost:8000/docs)
- Interactive API explorer
- Try endpoints directly
- See request/response examples

### 3. API Endpoints
- Health check: http://localhost:8000/health
- Model info: http://localhost:8000/api/v1/model/info
- Metrics: http://localhost:8000/api/v1/metrics

## Testing the Features

### Test 1: Check API Health
Open in browser: http://localhost:8000/health
Should show: `{"status": "healthy", "model_loaded": true, ...}`

### Test 2: View API Documentation
Open in browser: http://localhost:8000/docs
- Explore all endpoints
- Try the authentication endpoints
- Test image detection

### Test 3: Use the UI
1. Go to http://localhost:8501
2. Click "Image Upload" tab
3. Upload an image
4. Click "Detect Objects"
5. See the results!

### Test 4: Test Authentication (via API Docs)
1. Go to http://localhost:8000/docs
2. Find `/api/v1/auth/register`
3. Click "Try it out"
4. Enter:
   ```json
   {
     "username": "testuser",
     "email": "test@example.com",
     "password": "testpass123"
   }
   ```
5. Click "Execute"
6. Then try `/api/v1/auth/login` with the same credentials

## Running in Background

To run in background (detached mode):
```bash
docker-compose up -d
```

To view logs:
```bash
docker-compose logs -f
```

To stop:
```bash
docker-compose down
```

## Alternative: Run Without Docker

If you prefer to run locally:

### Step 1: Install Python dependencies
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
```

### Step 2: Initialize database
```bash
python scripts/init_db.py
```

### Step 3: Start API (Terminal 1)
```bash
uvicorn api.main:app --reload --port 8000
```

### Step 4: Start UI (Terminal 2)
```bash
streamlit run streamlit_app.py --server.port 8501
```

## Troubleshooting

### Port already in use?
Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001
  - "8502:8501"  # Change 8501 to 8502
```

### Docker build fails?
```bash
# Clean and rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Model not found?
The `yolov8n.pt` file should be in the project root. If missing, it will download automatically on first run.

### Can't access localhost?
- Windows: Use `http://127.0.0.1:8501` instead
- Check firewall settings
- Ensure Docker Desktop is running

## What to Explore

1. **UI Features**:
   - Image detection
   - Video tracking
   - Live webcam
   - Analytics dashboard

2. **API Features**:
   - Authentication system
   - Image detection endpoint
   - Batch processing
   - WebSocket support
   - Metrics endpoint

3. **Code Structure**:
   - `api/routers/` - API endpoints
   - `services/` - Business logic
   - `utils/` - Utilities
   - `tests/` - Test suite

## Next Steps

Once it's running:
1. Try uploading an image in the UI
2. Explore the API docs
3. Test authentication
4. Check the analytics dashboard
5. Review the code structure

Enjoy exploring your upgraded project! 🎉

