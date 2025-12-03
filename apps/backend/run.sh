#!/bin/bash

# WAVY.ai Backend Startup Script

echo "🌊 Starting WAVY.ai Backend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration (especially OPENAI_API_KEY)"
    echo "   Then run this script again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt --quiet

# Run the server
echo "🚀 Starting server on http://localhost:8080"
echo "📖 API Documentation: http://localhost:8080/docs"
echo ""
python -m uvicorn main:app --reload --port 8080
