#!/bin/bash
# Script to run the Flask web application

echo "🚀 Starting Crypto Prediction Web App..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install requirements
echo "📚 Installing requirements..."
pip install -r requirements.txt

# Run the Flask app
echo "🌐 Starting Flask server..."
python app.py
