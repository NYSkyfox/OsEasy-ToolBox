@ECHO OFF
chcp 65001 >nul
TITLE OsEasy-ToolKit 打包工具

cd /d "%~dp0"

ECHO ========================================
ECHO  正在打包 OsEasy-ToolKit v1.0 tk
ECHO ========================================
ECHO.

REM 检查 PyInstaller
where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    ECHO [错误] 未找到 PyInstaller，请先安装：pip install pyinstaller
    pause
    exit /b 1
)

ECHO [1/3] 开始打包...
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
    ECHO [错误] 打包失败！
    pause
    exit /b 1
)

ECHO.
ECHO [2/3] 移动输出文件...
if exist "dist\toolbox_tk.exe" (
    move /Y "dist\toolbox_tk.exe" "OsEasy-ToolKit.exe" >nul
    ECHO [完成] 已生成：OsEasy-ToolKit.exe
) else (
    ECHO [警告] 未找到输出文件，请检查 dist 目录
)

ECHO.
ECHO [3/3] 清理临时文件...
rmdir /S /Q build >nul 2>&1
rmdir /S /Q dist >nul 2>&1
del /Q *.spec >nul 2>&1

ECHO.
ECHO ========================================
ECHO  打包完成！
ECHO  输出文件：OsEasy-ToolKit.exe
ECHO ========================================
ECHO.
ECHO 请右键「以管理员身份运行」使用
ECHO.
pause
