@ECHO OFF
TITLE OsEasy-ToolKit Builder

cd /d "%~dp0"

ECHO ========================================
ECHO  Building OsEasy-ToolKit v1.0 tk
ECHO ========================================
ECHO.

REM Check PyInstaller
where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    ECHO [ERROR] PyInstaller not found. Install: pip install pyinstaller
    pause
    exit /b 1
)

ECHO [1/3] Packaging...
pyinstaller --onefile --noconsole ^
    --add-data "remain_tk.py;." ^
    --add-data "sv_ttk;sv_ttk" ^
    --hidden-import pygetwindow ^
    --hidden-import pynput ^
    --hidden-import pyautogui ^
    --hidden-import psutil ^
    --hidden-import httpx ^
    toolbox_tk.py

if %errorlevel% neq 0 (
    ECHO [ERROR] Build failed!
    pause
    exit /b 1
)

ECHO.
ECHO [2/3] Moving output...
if exist "dist\toolbox_tk.exe" (
    move /Y "dist\toolbox_tk.exe" "OsEasy-ToolKit.exe" >nul
    ECHO [DONE] Output: OsEasy-ToolKit.exe
) else (
    ECHO [WARN] Output not found, check dist folder.
)

ECHO.
ECHO [3/3] Cleaning temp files...
rmdir /S /Q build >nul 2>&1
rmdir /S /Q dist >nul 2>&1
del /Q *.spec >nul 2>&1

ECHO.
ECHO ========================================
ECHO  Build complete!
ECHO  Output: OsEasy-ToolKit.exe
ECHO ========================================
ECHO.
ECHO Right-click and "Run as administrator" to use
ECHO.
pause
