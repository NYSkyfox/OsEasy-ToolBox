# -*- coding: utf-8 -*-
# OsEasy-ToolKit tkinter 原生版（纯 Windows 默认样式 + 全功能确认弹窗）
import sys, os, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# ═══════════════ 高 DPI 适配 ═══════════════
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ═══════════════ 自动提权（PowerShell 方式） ═══════════════
def _is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

if not _is_admin():
    import subprocess
    script = (
        f'Start-Process -Verb RunAs -FilePath "{sys.executable}" '
        f'-ArgumentList \'{" ".join(sys.argv)} --elevated\''
    )
    subprocess.run(["powershell", "-Command", script],
                   capture_output=True,
                   creationflags=0x08000000)
    sys.exit()

if "--elevated" in sys.argv:
    sys.argv.remove("--elevated")
# ───────────────────────────────────────────

from remain_tk import *
import tkinter as tk
from tkinter import ttk, messagebox

# ── 系统托盘 ─────────────────────────────
try:
    import pystray
    from PIL import Image, ImageDraw
    _HAS_TRAY = True
except ImportError:
    _HAS_TRAY = False

def _create_tray_image():
    """生成一个 64x64 的托盘图标（蓝色工具箱）"""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 画一个蓝色工具箱形状
    draw.rectangle([8, 20, 56, 52], fill="#0078D4", outline="#005a9e", width=2)
    draw.rectangle([12, 28, 52, 48], fill="#ffffff", outline="#005a9e", width=1)
    draw.text((20, 32), "OE", fill="#0078D4")
    # 提手
    draw.rectangle([20, 14, 44, 22], fill="#0078D4", outline="#005a9e", width=2)
    return img

fstst = toolbox_cfg.first_launch_check()
if fstst:
    use_bat_file_to_run_cmd(
        'rename "C:\\Program Files\\Autodesk\\Autodesk Sync\\AdSyncNamespace.dll" "AdSyncNamespace.dll.bak"')

# ═══════════════ 色板 ═══════════════
COLORS = {
    "root_bg": "#f0f0f0", "fg": "#000000",
    "btn_bg": "#e8e8e8", "btn_fg": "#000000",
    "status_bg": "#e0e0e0", "status_fg": "#000000",
    "sep_bg": "#cccccc", "dlg_bg": "#f0f0f0",
}


class ToolBoxTk:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OsEasy-ToolKit v1.0 tk")
        self.root.resizable(True, True)

        # ═══ DPI 缩放 ═══
        try:
            self.dpi_scale = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
        except Exception:
            self.dpi_scale = 1.0
        self.root.tk.call('tk', 'scaling', self.dpi_scale * 1.3333333333)
        self._font = "微软雅黑"

        base_w, base_h = 600, 650
        win_w = int(base_w * self.dpi_scale)
        win_h = int(base_h * self.dpi_scale)
        self.root.geometry(f"{win_w}x{win_h}")
        self.root.minsize(win_w, win_h)

        # Windows 原生主题
        self.style = ttk.Style()
        self.style.theme_use("vista")
        self._configure_ttk_style()

        self.root.configure(bg=COLORS["root_bg"])

        pass_ui_class(self)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var,
                                   relief=tk.SUNKEN, anchor=tk.W,
                                   bg=COLORS["status_bg"], fg=COLORS["status_fg"])
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self._build_process_page()
        self._build_other_page()
        self._build_broadcast_page()
        self._build_command_page()
        self._build_dll_page()
        self._build_about_page()

        self.root.after(500, self._reflash_student_path)

        # ── 系统托盘初始化 ──
        self.tray_icon = None
        if _HAS_TRAY:
            self.root.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)

    # ── 系统托盘方法 ──
    def _minimize_to_tray(self):
        """点击 X 时最小化到系统托盘"""
        self.root.withdraw()
        if self.tray_icon is None:
            self._start_tray()

    def _start_tray(self):
        """启动系统托盘图标（在后台线程运行）"""
        def _run_tray():
            menu = (
                pystray.MenuItem("显示工具箱", self._show_window, default=True),
                pystray.MenuItem("退出", self._quit_app),
            )
            self.tray_icon = pystray.Icon(
                "OsEasyToolBox",
                _create_tray_image(),
                "OsEasy-ToolKit",
                menu
            )
            self.tray_icon.run()

        t = threading.Thread(target=_run_tray, daemon=True)
        t.start()

    def _show_window(self):
        """从托盘恢复窗口"""
        self.root.after(0, lambda: self.root.deiconify())
        self.root.after(0, lambda: self.root.lift())

    def _quit_app(self):
        """退出程序（停止托盘、关闭窗口）"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.root.destroy)

    # ═══════════════ 通用确认弹窗 ═══════════════
    def _confirm(self, title, msg):
        """弹出确认对话框，返回 True/False"""
        return messagebox.askyesno(title, msg)

    def _confirm_then(self, title, msg, func):
        """确认后异步执行"""
        if self._confirm(title, msg):
            self._async(func)

    def _confirm_then_result(self, title, msg, func, result_title="执行结果"):
        """确认后异步执行，执行完弹结果窗"""
        if not self._confirm(title, msg):
            return
        def wrapper():
            try:
                res = func()
                self.root.after(0, lambda: messagebox.showinfo(result_title, str(res)))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(result_title, f"执行失败: {e}"))
        self._async(wrapper)

    # ═══════════════ ttk 样式配置 ═══════════════
    def _configure_ttk_style(self):
        s = self.style
        s.configure("TNotebook", background=COLORS["root_bg"], borderwidth=0)
        s.configure("TNotebook.Tab",
                    background=COLORS["btn_bg"], foreground=COLORS["fg"],
                    borderwidth=0, padding=[22, 5], font=(self._font, 9))
        s.map("TNotebook.Tab",
              background=[("selected", "#cce5ff")])

    # ═══════════════ 辅助方法 ═══════════════
    def _lbl(self, parent, text, font_size=9, bold=False):
        f = (self._font, font_size, "bold") if bold else (self._font, font_size)
        return tk.Label(parent, text=text, font=f,
                        bg=COLORS["root_bg"], fg=COLORS["fg"])

    def _btn(self, parent, text, cmd, confirm_msg=None):
        """创建按钮，带确认弹窗"""
        if confirm_msg is None:
            confirm_msg = f"确定要执行「{text}」吗？"
        w = ttk.Button(parent, text=text,
                       command=lambda: self._confirm_then("确认操作", confirm_msg, cmd))
        return w

    def _frame(self, parent):
        return tk.Frame(parent, bg=COLORS["root_bg"])

    def _sep(self, parent):
        w = tk.Frame(parent, height=1, bg=COLORS["sep_bg"])
        w.pack(fill=tk.X, pady=4)
        return w

    def _chk(self, parent, text, on_cmd, off_cmd=None):
        var = tk.BooleanVar()
        def toggle():
            if var.get(): self._async(on_cmd)
            elif off_cmd: self._async(off_cmd)
        w = ttk.Checkbutton(parent, text=text, variable=var, command=toggle)
        w.pack(fill=tk.X, pady=2)
        return w, var

    def _entry(self, parent):
        return tk.Entry(parent, font=(self._font, 9),
                        bg="#ffffff", fg=COLORS["fg"],
                        insertbackground=COLORS["fg"])

    def _text(self, parent, height=3):
        w = tk.Text(parent, height=height, font=("Consolas", 9),
                    bg="#ffffff", fg=COLORS["fg"],
                    insertbackground=COLORS["fg"])
        return w

    # ═══════════════ 工具 ═══════════════
    def show_snakemessage(self, msg):
        self.status_var.set(str(msg))
        self.root.after(5000, lambda: self.status_var.set("就绪"))

    def _async(self, func):
        threading.Thread(target=func, daemon=True).start()

    # ═══════════════ 进程管理页 ═══════════════
    def _build_process_page(self):
        tab = self._frame(self.notebook)
        self.notebook.add(tab, text="进程管理")

        self.mmpc_label = self._lbl(tab, "根服务状态: 未知")
        self.mmpc_label.pack(anchor=tk.W, pady=(8, 2))

        row = self._frame(tab); row.pack(fill=tk.X, pady=2)
        ttk.Button(row, text="刷新MMPC",
                   command=self._update_mmpc).pack(side=tk.LEFT, padx=2)
        ttk.Button(row, text="停止MMPC",
                   command=lambda: self._confirm_then("确认操作", "确定要停止 MMPC 服务吗？",
                       lambda: run_sigle_cmd("sc stop MMPC"))
                   ).pack(side=tk.LEFT, padx=2)
        ttk.Button(row, text="启动MMPC",
                   command=lambda: self._confirm_then("确认操作", "确定要启动 MMPC 服务吗？",
                       lambda: run_sigle_cmd("sc start MMPC"))
                   ).pack(side=tk.LEFT, padx=2)

        self._sep(tab)
        self._btn(tab, "重启学生端", handle_start_student_client,
                  "确定要重启学生端吗？").pack(fill=tk.X, pady=2)
        self._btn(tab, "重新获取学生端路径", self._reflash_student_path,
                  "确定要重新获取学生端路径吗？").pack(fill=tk.X, pady=2)
        self._btn(tab, "注册粘滞键替换", register_killer_script,
                  "确定要注册粘滞键替换吗？\n（按5次Shift可触发击杀脚本）").pack(fill=tk.X, pady=2)
        self._btn(tab, "还原粘滞键", del_register_killer,
                  "确定要还原粘滞键吗？").pack(fill=tk.X, pady=2)
        self._chk(tab, "外部cmd守护进程", on_cmd=self._start_daemon, off_cmd=self._stop_daemon)
        self.guaqi_var = tk.BooleanVar(value=False)
        def _do_guaqi():
            if self.guaqi_var.get():
                return  # 已经在挂起状态，忽略
            self.root.withdraw()  # 隐藏工具箱窗口
            self.root.update()
            status = utils.guaqi_process(toolbox_cfg.student_exe_name)
            status_ = utils.guaqi_process("MultiClient.exe")  # 同时挂起MultiClient
            self.root.after(800, lambda: self.root.deiconify())  # 0.8秒后显示回来
            if status == True:
                self.guaqi_var.set(True)
            else:
                self.guaqi_var.set(False)
                self.show_snakemessage(str(status))
        def _do_huifu():
            if not self.guaqi_var.get():
                return  # 不在挂起状态，忽略
            status = utils.huifu_process(toolbox_cfg.student_exe_name)
            status_ = utils.huifu_process("MultiClient.exe")
            if status == True:
                self.guaqi_var.set(False)
            else:
                self.show_snakemessage(str(status))
        w = ttk.Checkbutton(tab, text="挂起学生端", variable=self.guaqi_var)
        w.configure(command=lambda: _do_guaqi() if self.guaqi_var.get() else _do_huifu())
        w.pack(fill=tk.X, pady=2)
        self._btn(tab, "打开噢易自带工具", start_oseasy_self_toolbox,
                  "确定要打开噢易自带工具箱吗？").pack(fill=tk.X, pady=2)

    def _update_mmpc(self):
        try:
            r = check_mmpc_status()
            self.mmpc_label.configure(text=f"根服务状态: {'运行中' if r else '已停止'}")
        except:
            self.mmpc_label.configure(text="根服务状态: 获取失败")

    def _start_daemon(self):
        global is_protect_killer_script_running
        is_protect_killer_script_running = True; start_killer_protect()

    def _stop_daemon(self):
        global is_protect_killer_script_running
        is_protect_killer_script_running = False

    # ═══════════════ 其他管理页 ═══════════════
    def _build_other_page(self):
        tab = self._frame(self.notebook)
        self.notebook.add(tab, text="其他管理")

        self._btn(tab, "删除脚本文件", del_self_cmd_files,
                  "确定要删除所有生成的脚本文件吗？").pack(fill=tk.X, pady=2)
        ttk.Button(tab, text="删除键盘锁驱动 & 控屏锁定程序",
                   command=self._ask_unlock).pack(fill=tk.X, pady=2)
        self._btn(tab, "恢复所有备份文件", restone_oe_backup_key_dll,
                  "确定要恢复所有备份文件吗？").pack(fill=tk.X, pady=2)
        self._btn(tab, "恢复黑屏安静程序",
                        lambda: restone_sigle_oe_backup_file("BlackSlient.exe"),
                        "确定要恢复黑屏安静程序吗？").pack(fill=tk.X, pady=2)
        self._btn(tab, "恢复控屏锁定程序",
                        lambda: restone_sigle_oe_backup_file("MultiClient.exe"),
                        "确定要恢复控屏锁定程序吗？").pack(fill=tk.X, pady=2)
        self._btn(tab, "停止网络管控服务(不可逆)", handle_run_old_unlock_net,
                  "确定要停止网络管控服务吗？\n此操作不可逆！").pack(fill=tk.X, pady=2)
        self._btn(tab, "关闭USB管控服务", usb_unlock,
                  "确定要关闭USB管控服务吗？\n此操作将删除USB驱动并注销！").pack(fill=tk.X, pady=2)
        self._btn(tab, "拦截教师端远程重启", block_remote_restart,
                  "确定要拦截远程重启吗？\n（映像劫持 shutdown.exe）").pack(fill=tk.X, pady=2)
        self._btn(tab, "恢复远程重启", unblock_remote_restart,
                  "确定要恢复远程重启吗？").pack(fill=tk.X, pady=2)

    def _ask_unlock(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("解锁方案选择")
        dw = int(500 * self.dpi_scale)
        dh = int(300 * self.dpi_scale)
        dlg.geometry(f"{dw}x{dh}")
        dlg.resizable(False, False); dlg.transient(self.root); dlg.grab_set()
        dlg.configure(bg=COLORS["dlg_bg"])
        tk.Label(dlg, text="选择解锁方案", font=(self._font, int(13 * self.dpi_scale), "bold"),
                 bg=COLORS["dlg_bg"], fg=COLORS["fg"]).pack(pady=int(10 * self.dpi_scale))

        desc = tk.Frame(dlg, bg=COLORS["dlg_bg"])
        desc.pack(fill=tk.X, padx=int(10 * self.dpi_scale))
        tk.Label(desc, text="方案一：删除文件（传统方式）\n  ·直接删除黑屏安静、键盘锁驱动、控屏锁定等文件\n  ·效果彻底，但不可逆（需恢复备份）\n\n方案二：映像劫持（推荐）\n  ·不删除任何文件，通过注册表劫持+重命名DLL\n  ·可随时还原，文件保留在磁盘上",
                 font=(self._font, int(9 * self.dpi_scale)), bg=COLORS["dlg_bg"], fg=COLORS["fg"],
                 wraplength=int(460 * self.dpi_scale), justify=tk.LEFT).pack(pady=int(6 * self.dpi_scale))

        bf = tk.Frame(dlg, bg=COLORS["dlg_bg"]); bf.pack(pady=int(12 * self.dpi_scale))
        def choose(plan):
            dlg.destroy()
            if plan == 1:
                self._confirm_then("确认操作",
                    "方案一：将删除文件并注销，确定吗？",
                    lambda: del_locked_exe_then_logout(True))
            elif plan == 2:
                self._confirm_then("确认操作",
                    "方案二：将注册映像劫持+重命名DLL并注销，确定吗？",
                    lambda: unlock_with_hijack(True))
            elif plan == 3:
                self._confirm_then("确认操作",
                    "确定要还原映像劫持方案吗？",
                    restore_from_hijack)
            else:
                self.show_snakemessage("取消解锁了")
        ttk.Button(bf, text="方案一：删除文件",
                   command=lambda: choose(1)).pack(side=tk.LEFT, padx=int(4 * self.dpi_scale))
        ttk.Button(bf, text="方案二：映像劫持",
                   command=lambda: choose(2)).pack(side=tk.LEFT, padx=int(4 * self.dpi_scale))
        ttk.Button(bf, text="还原劫持",
                   command=lambda: choose(3)).pack(side=tk.LEFT, padx=int(4 * self.dpi_scale))
        ttk.Button(bf, text="取消",
                   command=lambda: choose(None)).pack(side=tk.LEFT, padx=int(4 * self.dpi_scale))

    # ═══════════════ 广播管理页 ═══════════════
    def _build_broadcast_page(self):
        tab = self._frame(self.notebook)
        self.notebook.add(tab, text="广播管理")

        ttk.Button(tab, text="点我查看使用说明",
               command=lambda: messagebox.showinfo("使用说明",
                   "1.在「其他管理」页删除键盘锁&控屏锁定\n2.点击「替换拦截命令程序」\n"
                   "3.等老师控制一次屏幕即完成拦截\n4.此时可运行窗口化广播\n"
                   "5.老师来时切全屏,走后再杀进程")).pack(fill=tk.X, pady=2)

        self.rep_status = self._lbl(tab, "替换状态: 未知")
        self.rep_status.pack(anchor=tk.W, pady=2)
        ttk.Button(tab, text="刷新替换状态",
                   command=self._update_rep).pack(anchor=tk.W)
        self._sep(tab)
        self._btn(tab, "替换拦截命令程序", self._replace_scr,
                  "确定要替换屏幕广播拦截程序吗？\n（约需6秒）").pack(fill=tk.X, pady=2)
        self._btn(tab, "运行窗口化广播命令", self._run_win_bc,
                  "确定要以窗口化模式运行广播吗？").pack(fill=tk.X, pady=2)
        self._btn(tab, "运行全屏广播命令", self._run_full_bc,
                  "确定要运行全屏广播命令吗？").pack(fill=tk.X, pady=2)
        self._btn(tab, "手动杀屏幕广播进程", self._kill_scr,
                  "确定要强制结束屏幕广播进程吗？").pack(fill=tk.X, pady=2)
        self._btn(tab, "恢复原有屏幕广播程序", self._restore_scr,
                  "确定要恢复原有的屏幕广播程序吗？").pack(fill=tk.X, pady=2)

    def _update_rep(self):
        if check_replace_screen_render_status():
            self.rep_status.configure(text="替换状态: 已替换 ✓")
        else:
            self.rep_status.configure(text="替换状态: 未替换 ✗")

    def _replace_scr(self):
        if_is_high_ver_client_auto_close_mmpc_helper(); time.sleep(1)
        self.show_snakemessage("开始替换,约需6秒...")
        replace_screen_render()
        self.show_snakemessage("替换成功!")

    def _restore_scr(self):
        if_is_high_ver_client_auto_close_mmpc_helper(); time.sleep(1)
        if restone_screen_render(): self.show_snakemessage("还原成功!")
        else: self.show_snakemessage("还原失败")

    def _run_win_bc(self):
        cmd = from_log_file_get_remote_cmd()
        if not cmd: self.show_snakemessage("未拦截到控制命令参数"); return
        bcmd = build_run_broadcast_cmd(cmd).replace("#fullscreen#:1", "#fullscreen#:0")
        run_sigle_cmd(bcmd)

    def _run_full_bc(self):
        cmd = from_log_file_get_remote_cmd()
        if not cmd: self.show_snakemessage("未拦截到控制命令参数"); return
        bcmd = build_run_broadcast_cmd(cmd.replace("#fullscreen#:0", "#fullscreen#:1"))
        run_sigle_cmd(bcmd)

    def _kill_scr(self):
        run_sigle_cmd("taskkill /f /t /im ScreenRender_Y.exe")
        run_sigle_cmd("taskkill /f /t /im ScreenRender.exe")
        self.show_snakemessage("已杀广播进程")

    # ═══════════════ 广播命令页 ═══════════════
    def _build_command_page(self):
        tab = self._frame(self.notebook)
        self.notebook.add(tab, text="广播命令")

        self._lbl(tab, "键入完整的远程广播命令:").pack(anchor=tk.W)
        self.cmd_input = self._text(tab, 3)
        self.cmd_input.pack(fill=tk.X, pady=2)

        row1 = self._frame(tab); row1.pack(fill=tk.X, pady=2)
        self._btn(row1, "自动替换IP并更新", lambda: self._save_cmd(True),
                  "确定要自动替换IP并更新广播命令吗？").pack(side=tk.LEFT, padx=2)
        self._btn(row1, "手动更新(不替换IP)", lambda: self._save_cmd(False),
                  "确定要手动更新广播命令吗？").pack(side=tk.LEFT, padx=2)

        self._sep(tab)
        self._lbl(tab, "输入教师机IP地址:").pack(anchor=tk.W)
        self.teach_ip_entry = self._entry(tab)
        self.teach_ip_entry.pack(fill=tk.X, pady=2)
        self._btn(tab, "由教师机IP生成远程命令", self._gen_from_ip,
                  "确定要由教师机IP生成远程命令吗？").pack(fill=tk.X, pady=2)

        self._sep(tab)
        self._btn(tab, "从日志文件获取远程命令", from_scr_log_cmd_get_yccmd,
                  "确定要从日志文件获取远程命令吗？").pack(fill=tk.X, pady=2)
        self._btn(tab, "读取已拦截的广播命令", self._read_cmd,
                  "确定要读取已拦截的广播命令吗？").pack(fill=tk.X, pady=2)

    def _save_cmd(self, replace_ip):
        cmd = self.cmd_input.get("1.0", tk.END).strip()
        if not cmd: self.show_snakemessage("请先输入命令"); return
        handin_save_yc_cmd(cmd, replace_ip); self.show_snakemessage("命令已保存")

    def _gen_from_ip(self):
        ip = self.teach_ip_entry.get().strip()
        if not ip: self.show_snakemessage("请先输入教师机IP"); return
        generate_remote_cmd_and_save(ip); self.show_snakemessage("已生成并保存")

    def _read_cmd(self):
        if save_now_broadcast_cmd(): self.show_snakemessage("保存拦截命令成功 → command.txt")
        else: self.show_snakemessage("未拦截到控制命令参数")

    # ═══════════════ DLL工具页 ═══════════════
    def _run_dll_and_show(self, dll_name, func_name, return_type, argtypes, out_buffer):
        """执行DLL调用，结果用弹窗展示"""
        try:
            dll_path = toolbox_cfg.oseasy_path + dll_name
            self.show_snakemessage(f"正在调用: {dll_name} → {func_name} ...")
            edll = easy_dll(dll_path)
            runner = edll.setup_function(func_name, restype=return_type, argtypes=argtypes)
            if out_buffer is None:
                result = runner()
            else:
                result = runner(out_buffer)

            lines = [f"DLL: {dll_name}",
                     f"函数: {func_name}",
                     f"返回值: {result} (0=成功)"]
            if out_buffer is not None:
                lines.append(f"输出参数: {out_buffer.value}")
            if result != 0:
                err = edll.get_error_message(result)
                lines.append(f"错误信息: {err}")
            msg = "\n".join(lines)
            self.root.after(0, lambda: messagebox.showinfo("DLL 调用结果", msg))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("DLL 调用失败", str(e)))

    def _build_dll_page(self):
        tab = self._frame(self.notebook)
        self.notebook.add(tab, text="DLL工具")

        self._lbl(tab, "DLL 快捷调用（不删除文件，直接通过DLL接口操作）",
                  font_size=11, bold=True).pack(pady=6)
        self._sep(tab)

        self._lbl(tab, "USB 管控").pack(anchor=tk.W)

        def make_dll_handler(dll_name, func_name, return_type, argtypes, out_buffer):
            def handler():
                detail = f"DLL: {dll_name}\n函数: {func_name}\n\n确定要执行此调用吗？"
                if self._confirm("确认 DLL 调用", detail):
                    self._async(lambda: self._run_dll_and_show(
                        dll_name, func_name, return_type, argtypes, out_buffer))
            return handler

        ttk.Button(tab, text="关闭USB管控",
                   command=make_dll_handler(
                       "\\x64\\easyusbctrl.dll", "EasyUsb_StopWorking",
                       ctypes.c_int, [], None)
                   ).pack(fill=tk.X, pady=2)
        ttk.Button(tab, text="启动USB管控",
                   command=make_dll_handler(
                       "\\x64\\easyusbctrl.dll", "EasyUsb_StartWorking",
                       ctypes.c_int, [], None)
                   ).pack(fill=tk.X, pady=2)
        ttk.Button(tab, text="查询USB管控状态",
                   command=make_dll_handler(
                       "\\x64\\easyusbctrl.dll", "EasyUsb_IsWorking",
                       ctypes.c_int,
                       [ctypes.POINTER(ctypes.wintypes.DWORD)],
                       ctypes.wintypes.DWORD(0))
                   ).pack(fill=tk.X, pady=2)

        self._sep(tab)
        self._lbl(tab, "网络管控").pack(anchor=tk.W)
        ttk.Button(tab, text="开启网络管控",
                   command=make_dll_handler(
                       "\\x64\\OeNetlimit.dll", "DisableInternet",
                       ctypes.c_int, [], None)
                   ).pack(fill=tk.X, pady=2)
        ttk.Button(tab, text="关闭网络管控",
                   command=make_dll_handler(
                       "\\x64\\OeNetlimit.dll", "EnableNet",
                       ctypes.c_int, [], None)
                   ).pack(fill=tk.X, pady=2)

        # ═══ 下方：高级手动调用 ═══
        self._sep(tab)
        self._lbl(tab, "DLL 高级调用（手动输入）", font_size=11, bold=True).pack(pady=6)

        self._lbl(tab, "DLL 文件名:").pack(anchor=tk.W)
        self.dll_name_entry = self._entry(tab)
        self.dll_name_entry.pack(fill=tk.X, pady=2)

        self._lbl(tab, "函数名:").pack(anchor=tk.W)
        self.dll_func_entry = self._entry(tab)
        self.dll_func_entry.pack(fill=tk.X, pady=2)

        self._btn(tab, "调用 DLL 函数", self._confirm_and_run_dll_advanced,
                  "确定要调用此 DLL 函数吗？").pack(fill=tk.X, pady=6)

        self.dll_result = self._text(tab, 4)
        self.dll_result.configure(state=tk.DISABLED)
        self.dll_result.pack(fill=tk.BOTH, expand=True, pady=2)

    def _confirm_and_run_dll_advanced(self):
        dll_name = self.dll_name_entry.get().strip()
        func_name = self.dll_func_entry.get().strip()
        if not dll_name or not func_name:
            self.show_snakemessage("请先输入 DLL 文件名和函数名")
            return
        detail = f"DLL: {dll_name}\n函数: {func_name}\n\n确定要执行此调用吗？"
        if self._confirm("确认 DLL 调用", detail):
            self._async(lambda: self._run_dll_advanced(dll_name, func_name))

    def _run_dll_advanced(self, dll_name, func_name):
        try:
            dll_path = toolbox_cfg.oseasy_path + dll_name
            self.show_snakemessage(f"正在调用: {dll_name} → {func_name} ...")
            edll = easy_dll(dll_path)
            runner = edll.setup_function(func_name)
            result = runner()
            msg = f"函数: {func_name}\n返回值: {result}"
            if result != 0:
                err = edll.get_error_message(result)
                msg += f"\n错误信息: {err}"
            self.root.after(0, lambda: self._show_dll_advanced_result(msg))
        except Exception as e:
            self.root.after(0, lambda: self._show_dll_advanced_result(f"调用失败: {e}"))

    def _show_dll_advanced_result(self, msg):
        self.dll_result.configure(state=tk.NORMAL)
        self.dll_result.delete("1.0", tk.END)
        self.dll_result.insert("1.0", msg)
        self.dll_result.configure(state=tk.DISABLED)

    # ═══════════════ 关于页 ═══════════════
    def _build_about_page(self):
        tab = self._frame(self.notebook)
        self.notebook.add(tab, text="关于")

        self._lbl(tab, "OsEasy-ToolKit v1.0 tk", font_size=16, bold=True).pack(pady=10)
        self._lbl(tab, "愿我们的电脑课都不再无聊~🥳", font_size=11).pack(pady=4)
        ttk.Button(tab, text="打开工具箱 Github 页",
                   command=open_github_page).pack(pady=10)
        self._btn(tab, "打击教师端连接", blow_teacher_client,
                  "确定要断开教师端连接吗？").pack(pady=4)
        self._sep(tab)
        self._lbl(tab, "基于原版 remain.py 逻辑", font_size=8).pack()

    # ═══════════════ 启动 ═══════════════
    def _reflash_student_path(self):
        try:
            v = try_guess_student_client_version()
            if toolbox_cfg.oseasypath_have_been_modified:
                hint = f"猜测版本 v{v/10}" if v else "版本检测失败"
                self.show_snakemessage(f"更新成功 {toolbox_cfg.oseasy_path} [{toolbox_cfg.student_exe_name}] {hint}")
            else:
                self.show_snakemessage("更新失败,学生端未运行?")
        except Exception as e:
            self.show_snakemessage(f"更新出错: {e}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    ToolBoxTk().run()