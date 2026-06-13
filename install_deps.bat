@ECHO OFF
echo 正在安装 OsEasy-ToolBox 依赖...
echo.
echo 核心依赖：
pip install pygetwindow pynput pyautogui psutil httpx pystray pillow
echo.
echo 如果安装失败，请确保已安装 Python 3.10+ 并添加到 PATH
echo.
pause