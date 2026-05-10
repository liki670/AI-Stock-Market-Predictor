@echo off
echo ============================================================
echo  AI Stock Market Predictor - Setup Script
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python is not installed or not on PATH.
    echo.
    echo Please download and install Python 3.10+ from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During installation, check the box:
    echo   "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version

echo.
echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install tensorflow flask flask-cors streamlit yfinance scikit-learn textblob requests python-dotenv plotly pandas numpy

echo.
echo ============================================================
echo  Setup complete! 
echo ============================================================
echo.
echo Next steps:
echo  1. Edit .env and add your NewsData.io API key (optional)
echo  2. Run START.bat to launch the application
echo.
pause
