@echo off
REM Script to run the Flask web application on Windows

echo 🚀 Starting Crypto Prediction Web App...

REM Check if virtual environment exists
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install requirements
echo 📚 Installing requirements...
pip install -r requirements.txt

REM Run the Flask app
echo 🌐 Starting Flask server...
python app.py

pause
