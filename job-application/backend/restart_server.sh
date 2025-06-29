#!/bin/bash

echo "🚀 Restarting Graph RAG Enhanced Job Application Server..."

# Kill any existing uvicorn processes
echo "🛑 Stopping existing servers..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true
sleep 2

# Check if the app imports correctly
echo "🧪 Testing app imports..."
python3 -c "from app.main import app; print('✅ App imports successfully')" || {
    echo "❌ App import failed! Check for errors."
    exit 1
}

# Start the server
echo "🎯 Starting server on http://localhost:8000..."
echo "📊 Graph RAG endpoints available at:"
echo "   • GET  /api/demo/graph-rag-status"
echo "   • POST /api/demo/graph-rag-search"
echo "   • POST /api/demo/personalized-advice"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="

python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 