@echo off
python -c "import nuitka" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Nuitka is not installed. Installing Nuitka...
    pip install nuitka>=2.4.11
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install Nuitka. Please try installing manually: pip install nuitka
        pause
        exit /b 1
    )
    echo Nuitka installed successfully!
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