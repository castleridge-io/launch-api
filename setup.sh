#!/bin/bash
# Setup script for Launch API

set -e

echo "🚀 Launch API Setup"
echo "==================="
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create venv
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "✅ Dependencies installed"

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   nano .env"
fi

# Create logs directory
mkdir -p logs

echo
echo "✅ Setup complete!"
echo
echo "Next steps:"
echo "1. Edit .env with your API keys"
echo "   nano .env"
echo
echo "2. Start the API server"
echo "   python server.py"
echo
echo "3. In another terminal, test with dry run"
echo "   source venv/bin/activate"
echo "   python launch-hybrid.py --dry-run"
echo
echo "📖 Read README.md for detailed configuration"
