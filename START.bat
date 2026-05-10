@echo off
echo ============================================================
echo  AI Stock Market Predictor (3D) - Starting...
echo ============================================================
echo.

REM Start Flask backend (which serves the 3D frontend)
echo Starting Backend and 3D UI on http://localhost:5000 ...
start "AI Quant Backend" cmd /k "python app.py"

REM Wait 10 seconds for Flask to initialize (TensorFlow takes a few seconds)
timeout /t 10 /nobreak >nul

echo.
echo Server is running at: http://localhost:5000
echo.
echo Opening browser...
start http://localhost:5000
echo.
echo Close the terminal window to stop the app.
echo.
pause
