#!/bin/bash
# Production startup script

echo "🚀 Starting VisionTrack AI in production mode..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it with production settings."
    exit 1
fi

# Check for required environment variables
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-secret-key-change-in-production" ]; then
    echo "⚠️  WARNING: SECRET_KEY not set or using default value!"
    echo "   Please set a strong SECRET_KEY in your .env file"
fi

# Build and start services
echo "🐳 Building and starting production containers..."
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d

echo "✅ Production services started!"
echo ""
echo "📍 Access points:"
echo "   - UI: http://localhost:8501"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📊 View logs: docker-compose -f docker-compose.production.yml logs -f"
echo "🛑 Stop services: docker-compose -f docker-compose.production.yml down"

