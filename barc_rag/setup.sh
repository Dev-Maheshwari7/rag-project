#!/bin/bash
# Quick setup script for BARC RAG system

set -e

echo "🚀 BARC RAG System - Quick Setup"
echo "================================"
echo ""

# Check Docker
echo "✓ Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "✗ Docker not found. Please install Docker first."
    exit 1
fi
if ! command -v docker-compose &> /dev/null; then
    echo "✗ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi
echo "✓ Docker OK"
echo ""

# Check Python
echo "✓ Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found. Please install Python 3.9+ first."
    exit 1
fi
python_version=$(python3 --version | awk '{print $2}')
echo "✓ Python $python_version OK"
echo ""

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d
echo "✓ Docker services started"
echo "  - Qdrant: http://localhost:6333"
echo "  - PostgreSQL: localhost:5432"
echo ""

# Wait for services
echo "⏳ Waiting for services to be ready (15 seconds)..."
sleep 15
echo "✓ Services ready"
echo ""

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your xAI API key"
echo "2. Place documents in the ./documents folder"
echo "3. Run: streamlit run app/main.py"
echo ""
