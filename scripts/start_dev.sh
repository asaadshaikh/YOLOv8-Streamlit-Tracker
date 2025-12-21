#!/bin/bash
# Development startup script

echo "🚀 Starting VisionTrack AI in development mode..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please update it with your configuration."
    else
        echo "❌ .env.example not found. Please create .env manually."
        exit 1
    fi
fi

# Initialize database
echo "📦 Initializing database..."
python scripts/init_db.py

# Start services
echo "🐳 Starting Docker containers..."
docker-compose up -d

echo "✅ Services started!"
echo ""
echo "📍 Access points:"
echo "   - UI: http://localhost:8501"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📊 View logs: docker-compose logs -f"
echo "🛑 Stop services: docker-compose down"

