@echo off
echo Checking dependencies...

REM Check all dependencies in one go
python -c "import bs4, curl_cffi, nuitka" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing dependencies...
    pip install beautifulsoup4>=4.12.0 curl-cffi>=0.5.10 nuitka==2.4.11 >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install dependencies. Please try installing manually.
        pause
        exit /b 1
    )
    echo Dependencies installed successfully!
) else (
    echo All dependencies already installed. Good to go!
)

echo Building achievements.exe...
python -m nuitka --standalone --onefile --lto=yes --remove-output --output-dir=dist achievements.py
if %ERRORLEVEL% EQU 0 (
    echo Build completed successfully!
    echo Executable created at dist\achievements.exe
) else (
    echo Build failed with error code %ERRORLEVEL%
)
pause