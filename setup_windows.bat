@echo off
echo Installing backend dependencies...
py -3.12 -m pip install -r requirements.txt
if errorlevel 1 pause & exit /b 1

echo.
echo Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 pause & exit /b 1
cd ..

echo.
echo Setup complete.
echo Run run_backend.bat and run_frontend.bat in two separate terminals.
pause
