# OsEasy-ToolBox (噢易工具箱) — tkinter 原生版

Windows 环境下针对噢易多媒体教学系统的辅助工具箱，**纯 Python tkinter 实现**，无需额外 GUI 框架。

## 功能一览

| 页面 | 功能 |
|------|------|
| **进程管理** | MMPC 服务控制、挂起/恢复学生端进程、粘滞键替换（5次按Shift调出工具箱）、守护进程自动恢复 |
| **其他管理** | 删除脚本、解锁键盘/屏幕锁定、USB/网络管控、**拦截教师端远程重启** |
| **广播管理** | 替换/还原 ScreenRender、窗口化/全屏广播、杀广播进程 |
| **广播命令** | 手动输入/生成/读取广播命令 |
| **DLL工具** | USB/网络管控的 DLL 调用 + 高级手动调用 |
| **关于** | 版本信息、打击教师端连接、打开 GitHub 仓库 |

## 快速使用

```bash
# 1. 安装依赖
install_deps.bat

# 2. 启动工具箱
run_tk.bat
```

或手动安装依赖：

```bash
pip install pygetwindow pynput pyautogui psutil httpx pystray pillow
```

## 打包 exe

运行 `build.bat`，依赖 [UPX](https://github.com/upx/upx/releases)（可选，用于压缩体积）。

```bash
build.bat
```

打包后的 exe 在 `dist/` 目录下。

## 系统要求

- **操作系统**: Windows 7 / 10 / 11
- **Python**: 3.10+（开发环境），打包的 exe 自带解释器无需 Python
- **教师端**: 噢易多媒体教学系统

## 关键功能说明

### 拦截教师端远程重启
教师端远程重启走的是 `shutdown.exe`，通过**映像劫持**将 `shutdown.exe` 重定向到空命令，使其无法触发重启。从开始菜单手动关机/重启不受影响（走 `ExitWindowsEx` API）。

### 粘滞键后门
连按 5 次 Shift 触发粘滞键弹窗时，可劫持弹出工具箱（管理员权限），适用于学生端进程被保护无法关闭的场景。

### 系统托盘
点击窗口关闭按钮（✕）会**最小化到系统托盘**，托盘图标右键菜单可「显示工具箱」或「退出」。

## 免责声明

本工具仅供学习和技术研究使用。请遵守所在机房/学校的规定，合理使用。

## 许可证

MIT License
