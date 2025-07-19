@echo off
echo Starting NCC Text Extraction Application...
echo.
echo Choose an option:
echo 1. Start both servers (recommended)
echo 2. Test PDF server only
echo 3. Start PDF server only
echo 4. Start Streamlit app only
echo.
set /p choice=Enter your choice (1-4): 

if "%choice%"=="1" (
    echo Starting both Streamlit app and PDF server...
    python run_servers.py
) else if "%choice%"=="2" (
    echo Testing PDF server...
    python test_pdf_server.py
) else if "%choice%"=="3" (
    echo Starting PDF server only...
    python pdf_server.py
) else if "%choice%"=="4" (
    echo Starting Streamlit app only...
    streamlit run app.py
) else (
    echo Invalid choice. Starting both servers...
    python run_servers.py
)
pause 