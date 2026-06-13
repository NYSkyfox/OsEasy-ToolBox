import os, time
from datetime import datetime

import pygetwindow as gw
import webbrowser
import ctypes
import sys
import psutil
import pyautogui
import socket
import re
import json

import httpx

backup_file_path = "C:\\Backups"

curr_username = os.environ.get('USERNAME')

cmd_file_path = f"C:\\Users\\{curr_username}\\OsEasy_Tools"


is_box_killer_running = False

is_protect_killer_script_running = False

is_mmpc_running = True



try:
    os.makedirs(cmd_file_path, mode=0o777, exist_ok=True)
    os.makedirs(backup_file_path, mode=0o777, exist_ok=True)
except PermissionError:
    raise Exception("权限不足: 请右键使用管理员身份运行")

class easy_dll:
    def __init__(self, dll_path):

        self.dll = ctypes.WinDLL(dll_path)

    def setup_function(self, func_name, restype=ctypes.c_int, argtypes=None):
        """
        Configures a DLL function with the specified name, return type, and argument types.

        :param func_name: Name of the function in the DLL.
        :param restype: Return type of the function (default is c_int).
        :param argtypes: List of argument types (default is None).
        """
        func = getattr(self.dll, func_name)
        func.restype = restype
        func.argtypes = argtypes or []
        return func

    def get_error_message(self, error_code):
        """
        Helper function to retrieve Windows error message for a given error code.

        :param error_code: Error code to look up.
        :return: The formatted error message string.
        """
        msg_buffer = ctypes.create_unicode_buffer(256)
        ctypes.windll.kernel32.FormatMessageW(
            0x00001000,  # FORMAT_MESSAGE_FROM_SYSTEM
            None,
            error_code,
            0,  # Default language
            msg_buffer,
            len(msg_buffer),
            None,
        )
        return msg_buffer.value


def run_easy_dll(
    dll_name, func_name, return_type, argtypes, out_buffer, after_run_func=None
):
    """
    ### 参数
    - `dll_name`: 要调用的dll文件名
    - `func_name`: 要调用的函数名
    - `return_type`: 要调用的函数的返回值类型
    - `argtypes`: 要调用的函数的参数类型
    - `out_buffer`: 要调用的函数的输出参数
    - `after_run_func`: 运行完毕后的回调函数

    """

    print("dllUse debug >", dll_name, func_name, return_type, argtypes, out_buffer)

    # dll_path = "" + dll_name
    dll_path = toolbox_cfg.oseasy_path + dll_name

    easy_dll = easy_dll(dll_path)

    runner = easy_dll.setup_function(func_name, restype=return_type, argtypes=argtypes)

    try:
        if out_buffer == None:
            result = runner()
        else:
            result = runner(out_buffer)
    except Exception as e:
        Ui_call_show_snake_message(f"调用失败 抛出异常：\n{e}")
        return

    print("[DEBUG] dll result:", result)

    ui_show_msg = f"运行结果: \n函数: {func_name}\n返回值: {result}"
    if out_buffer != None:
        ui_show_msg += f"\n输出参数: {out_buffer.value}"

    if result != 0:
        error_msg = easy_dll.get_error_message(result)
        print("[DEBUG] Error message:", error_msg)
        ui_show_msg += f"\n错误信息: {error_msg}"

    Ui_call_show_snake_message(ui_show_msg)

    if after_run_func != None:
        after_run_func()


class toolbox_config:

    def __init__(self):

        self.config_file_path = "C:\\ToolBoxConfig.json"
        self.running_student_client_ver = 0
        self.oseasypath_have_been_modified = False
        self.student_exe_name = "Student.exe"
        self.oseasy_path = (
            "C:\\Program Files (x86)\\Os-Easy\\os-easy multicast teaching system\\"
        )
        self.broadcast_cmd = None


    def first_launch_check(self) -> bool:
        """首次启动检查"""
        reads = self.get_config_key_data("first_launch_time")
        if not reads:
            self.write_first_launch_time()
            return True
        else:
            return False

    def write_first_launch_time(self) -> None:
        """写入首次启动时间"""
        self.set_config_key_data("first_launch_time", get_time_str())

    def read_config(self) -> str:
        """从配置文件中读取"""
        if check_give_file_path_is_excs(self.config_file_path):
            with open(self.config_file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            self.write_config("{}")
            return "{}"

    def write_config(self, datas: str | dict) -> None:
        """写入配置文件"""

        if isinstance(datas, dict):
            datas = json.dumps(datas, ensure_ascii=False, indent=4)

        with open(self.config_file_path, "w", encoding="utf-8") as f:
            f.write(datas)

    def get_config_key_data(self, key) -> str | None:
        """获取配置文件中指定键的数据"""
        return self.get_style_path(key)

    def set_config_key_data(self, key, value) -> None:
        """设置配置文件中的数据"""
        self.set_style_path(key, value)

    def clear_config_key_data(self, key) -> None:
        """清空配置文件中的数据"""
        cfg = self.read_config()
        if cfg == "{}":
            return
        jData: dict = json.loads(cfg)
        if key in jData:
            jData.pop(key)
        self.write_config(jData)

    def get_style_path(self, style_name: str) -> str | None:
        """获取自定义外观的路径\n
        style_name: ["yiyan","fort","bg"]\n
        一言, 字体, 背景"""

        cfg = self.read_config()
        if cfg == "{}":
            return None
        jData = json.loads(cfg)
        if style_name in jData:
            return jData[style_name]
        return None

    def set_style_path(self, style_name: str, style_path: str) -> None:
        """设置自定义外观的路径\n
        style_name: ["yiyan","fort","bg"]\n
        一言, 字体, 背景"""

        cfg = self.read_config()
        jData = json.loads(cfg)
        jData[style_name] = style_path
        self.write_config(jData)

class script_gen:
    @staticmethod
    def summon_unlocknet() -> None:
        """生成解锁网络锁定脚本"""
        global cmd_file_path
        mp = cmd_file_path + "\\net.bat"
        fm = open(mp, "w")
        cmdtext = f"""@ECHO OFF\n
        title OsEasyToolBoxUnlockNetHeler\n
        {if_is_high_ver_client_then_return_stop_cmd_line(True)}
        :a\n
        taskkill /f /t /im {toolbox_cfg.student_exe_name}\n
        taskkill /f /t /im DeviceControl_x64.exe\n
        goto a
        """
        fm.write(cmdtext)
        fm.close()
    
    @staticmethod
    def summon_unlock_usb() -> None:
        """生成解锁USB脚本"""
        global cmd_file_path
        mp = cmd_file_path + "\\usb.bat"
        fm = open(mp, "w")
        cmdtext = """@ECHO OFF\n
        title OsEasyToolBoxUnlockUSBHeler\n

        sc delete easyusbflt\n
        sc delete easyusbflt\n
        timeout 1\n
        
        del C:\\Windows\\System32\\drivers\\easyusbflt.sys\n
        timeout 5\n
        shutdown /l\n
        """
        fm.write(cmdtext)
        fm.close()
        
    @staticmethod
    def summon_killer_v2() -> None:
        """生成V2击杀脚本"""
        global cmd_file_path
        mp = cmd_file_path + "\\kv2.bat"
        fm = open(mp, "w")
        cmdtext = f"@ECHO OFF\ntitle OsEasyToolBoxKillerV2\n:awa\nfor %%p in (Ctsc_Multi.exe,DeviceControl_x64.exe,HRMon.exe,MultiClient.exe,OActiveII-Client.exe,OEClient.exe,OELogSystem.exe,OEUpdate.exe,OEProtect.exe,ProcessProtect.exe,RunClient.exe,RunClient.exe,ServerOSS.exe,{toolbox_cfg.student_exe_name},wfilesvr.exe,tvnserver.exe,updatefilesvr.exe,ScreenRender.exe) do taskkill /f /IM %%p\ngoto awa\n"
        fm.write(cmdtext)
        fm.close()
        
    @staticmethod
    def summon_killer() -> None:
        """生成击杀脚本"""
        global cmd_file_path
        mp = cmd_file_path + "\\k.bat"
        fm = open(mp, "w")
        cmdtext = f"""@ECHO OFF\n
        title OsEasyToolBoxKiller\n
        
        {if_is_high_ver_client_then_return_stop_cmd_line(True)}
        
        taskkill /f /t /im MultiClient.exe\n
        taskkill /f /t /im MultiClient.exe\n
        taskkill /f /t /im BlackSlient.exe\n
        :a\n
        taskkill /f /t /im {toolbox_cfg.student_exe_name}\n
        goto a"""
        fm.write(cmdtext)
        fm.close()
    @staticmethod
    def summon_del_dll(delMtc: bool, shutdown: bool) -> None:
        """生成删除关键文件脚本"""
        global cmd_file_path
        backup_oe_files()

        mp = cmd_file_path + "\\d.bat"
        fm = open(mp, "w")
        cmdtext = f"@ECHO OFF\ntitle OsEasyToolBox-Helper\ncd /D {toolbox_cfg.oseasy_path}\ntimeout 1\ndel /F /S LockKeyboard.dll\ndel /F /S LoadDriver.exe\ndel /F /S LoadDriver.exe\ndel /F /S oenetlimitx64.cat\ndel /F /S BlackSlient.exe\ncd x86\ndel /F /S LISSNetInfoSniffer.exe\ncd .."
        if delMtc == True:
            cmdtext += "\ndel /F /S MultiClient.exe"
        if shutdown == False:
            pass
        elif shutdown == True:
            cmdtext += "\ntimeout 5\nshutdown /l"
        # cmdtext += "\ntimeout 10\nshutdown /l"
        cmdtext += "\nexit"
        fm.write(cmdtext)
        fm.close()

class utils:
    @staticmethod
    def get_program_path(program_name) -> str | None:
        """
        获取指定程序的运行路径

        :param program_name: 程序名称，如 'exp.exe'

        :return: 程序的运行路径

        """
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                if proc.info["name"] == program_name:
                    return proc.info["exe"]
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return None
    
    @staticmethod
    def suspend_resume_process(process_name,option) -> str | bool:
        """挂起进程"""
        try:
            for process in psutil.process_iter(["pid", "name"]):
                if process.info["name"] == process_name:
                    pid = process.info["pid"]
                    
                    psutil.Process(pid).suspend() if option == "suspend" \
                    else psutil.Process(pid).resume()
                    
                    print(f"Process {process_name} (PID {pid}) {option}.")
                    return True
            print(f"Process {process_name} not found.")
            return f"尝试{option}的进程未找到"
        except psutil.AccessDenied as e:
            print(f"Permission error: {e}")
            return "尝试挂起进程失败"

    @staticmethod
    def guaqi_process(process_name) -> str | bool:
        return utils.suspend_resume_process(process_name,"suspend")
    
    @staticmethod
    def huifu_process(process_name) -> str | bool:
        """恢复挂起进程"""
        return utils.suspend_resume_process(process_name,"resume")

def get_god_potato_path():
    # PyInstaller 提取的临时路径
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "resources", "gp_net35.exe")
    # 开发环境路径
    return os.path.join("resources", "gp_net35.exe")

def run_cmd_with_god_potato(arguments:str):
    """
    使用神の土豆来运行命令
    参数：
    - arguments: 要运行的命令
    如：run_god_potato_cmd("net start MMPC")
    """
    ntsd_path = get_god_potato_path()
    if not os.path.exists(ntsd_path):
        raise FileNotFoundError(f"ntsd.exe not found at {ntsd_path}")

    cmd = f'"{ntsd_path}" -cmd "cmd /c {arguments}"'
    
    run_sigle_cmd(cmd,False)
    

toolbox_cfg = toolbox_config()


Ui_Class = None


def pass_ui_class(ui: classmethod) -> None:
    """传递Ui类到此处让这里的函数可以调用主Ui的函数"""
    global Ui_Class
    Ui_Class = ui


def Ui_call_show_snake_message(*msg: tuple) -> None:
    """Ui类 显示底部弹窗"""
    mix = ""
    for i in msg:
        mix += str(i) + " "
    msg = mix.strip()
    Ui_Class.show_snakemessage(msg)

def try_get_teacher_ip() -> str | None:
    """尝试从广播命令中提取教师机IP"""
    bdcmd = toolbox_cfg.get_config_key_data("broadcast_cmd")

    if bdcmd == "":
        return None

    # 匹配被 # 包裹的IPv4地址
    pattern = r"#(\d{1,3}(?:\.\d{1,3}){3})#"
    ips = re.findall(pattern, bdcmd)
    try:
        ip = ips[1]
        return ip
    except IndexError:
        return None

def blow_teacher_client():
    ip = try_get_teacher_ip()
    if ip is None:
        Ui_call_show_snake_message("未获取到教师机IP")
        return
    headers = {
        "User-Agent": "OsEzToolBox"
    }
    uri = "http://" + ip + ":9003"
    res = httpx.get(uri, headers=headers)
    tip = "教师端返回了无效的响应" if res.status_code != 400 \
        else "已断开教师端的连接\n可能需要约10秒生效"
    Ui_call_show_snake_message(tip)
    res.close()


def TryGetStudentPath() -> tuple[str, str] | tuple[bool, None]:
    """尝试获取学生端路径 并更新全局变量"""

    Spath = utils.get_program_path("Student.exe")
    Spath_2 = utils.get_program_path("MmcStudent.exe")
    # v10.9.1 学生端改名为MmcStudent.exe

    if Spath == None and Spath_2 == None:
        print("[DEBUG] > 未找到运行中的学生端")

        isModed = toolbox_cfg.get_config_key_data("studentPath_have_been_modified")
        print(f"[DEBUG] 配置文件 > 学生端路径是否被修改：{isModed}")
        if not isModed:
            return False, None

        toolbox_cfg.oseasypath_have_been_modified = True

        toolbox_cfg.oseasy_path = toolbox_cfg.get_config_key_data("studentPath")
        toolbox_cfg.student_exe_name = toolbox_cfg.get_config_key_data("studentExeName")

        print(f"[DEBUG] 配置文件 > 学生端路径为：{toolbox_cfg.oseasy_path}")
        print(f"[DEBUG] 配置文件 > 学生端进程名为：{toolbox_cfg.student_exe_name}")

        toolbox_cfg.set_config_key_data("studentPath", toolbox_cfg.oseasy_path)
        toolbox_cfg.set_config_key_data("studentExeName", toolbox_cfg.student_exe_name)

        return toolbox_cfg.oseasy_path, toolbox_cfg.student_exe_name

    if Spath_2:
        Spath = Spath_2
        exe_name = "MmcStudent.exe"
    else:
        exe_name = "Student.exe"

    Spath = str(Spath).replace("/", "\\").removesuffix(exe_name)
    
    toolbox_cfg.oseasypath_have_been_modified = True
    toolbox_cfg.oseasy_path = Spath
    toolbox_cfg.student_exe_name = exe_name

    print(f"[DEBUG] 学生端路径为：{toolbox_cfg.oseasy_path}")
    print(f"[DEBUG] 学生端进程名为：{toolbox_cfg.student_exe_name}")

    toolbox_cfg.set_config_key_data("studentPath", toolbox_cfg.oseasy_path)
    toolbox_cfg.set_config_key_data("studentExeName", toolbox_cfg.student_exe_name)
    toolbox_cfg.set_config_key_data("studentPath_have_been_modified", True)

    return toolbox_cfg.oseasy_path, toolbox_cfg.student_exe_name





def usb_unlock():
    """尝试解锁USB管控"""
    Ui_call_show_snake_message("尝试关闭USB服务... 请稍等")
    script_gen.summon_unlocknet()
    script_gen.summon_unlock_usb()
    runbat("net.bat")
    time.sleep(2)
    runbat("usb.bat")
    # time.sleep(2)
    # runcmd("sc delete easyusbflt")
    # time.sleep(1)


def try_guess_student_client_version() -> int:
    """尝试通过检测LissHeler.exe此类旧版本没有的程序\n
    来猜测学生端版本"""

    if not toolbox_cfg.oseasypath_have_been_modified:
        _, _2 = TryGetStudentPath()

    versions = {
        109: f"{toolbox_cfg.oseasy_path}LissHelper.exe",
        108: f"{toolbox_cfg.oseasy_path}MultiClient.exe",
        105: f"{toolbox_cfg.oseasy_path}MouseKeyBoradControl.exe",
    }

    for version, path in versions.items():
        if check_give_file_path_is_excs(path):
            print(f"[Student Ver Guess] maybe is v{version // 10}.{version % 10}")
            toolbox_cfg.running_student_client_ver = version
            toolbox_cfg.set_config_key_data("studentClientVer", version)
            return toolbox_cfg.running_student_client_ver

    print("[Student Ver Guess] 超出检测范围 学生端本体可能损坏或路径不正确")
    toolbox_cfg.running_student_client_ver = 0
    return toolbox_cfg.running_student_client_ver

    pass


def if_is_high_ver_client_auto_close_mmpc_helper():
    """检查学生端版本来决定\n
    需不需要关闭MMPC保护服务\n
    """
    if not toolbox_cfg.running_student_client_ver:
        _ = try_guess_student_client_version()

    if toolbox_cfg.running_student_client_ver >= 109:
        mpStatus = check_mmpc_status()
        if mpStatus:
            run_sigle_cmd("sc stop MMPC")
            time.sleep(1)

    pass


def if_is_high_ver_client_then_return_stop_cmd_line(IsStop = True):
    """检查学生端版本 返回根服务控制指令\n
    用于直接插入到脚本中
    """

    if not toolbox_cfg.running_student_client_ver:
        _ = try_guess_student_client_version()

    if toolbox_cfg.running_student_client_ver >= 109:
        if IsStop == True:
            return "sc stop MMPC\n"
        else:
            return "sc start MMPC\n"
    return ""


def check_give_file_path_is_excs(filePath) -> bool:
    """检查文件是否存在"""
    return os.path.isfile(filePath)


# ── Fake_SCR（假 ScreenRender）───────
FAKE_SCR_FILE = os.path.join(cmd_file_path, "fake_scr.py")
FAKE_SCR_CODE = r'''# -*- coding: utf-8 -*-
# OsEasy-ToolBox Fake ScreenRender - 拦截广播命令并保存
import sys, os, json, re

# 收集所有命令行参数（含广播命令）
cmd_parts = []
for i in sys.argv:
    cmd_parts.append(str(i))

# 把广播命令写到工具箱能读取的地方
# %appdata%/Mmc/ScreenRender.log 是原始程序写的，这里我们也写同样的格式
appdata = os.getenv("APPDATA")
if appdata:
    log_dir = os.path.join(appdata, "Mmc")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "ScreenRender.log")
    from datetime import datetime
    timestamp = datetime.now().strftime("%m-%d %H:%M:%S")
    # 筛选出看起来像广播命令的参数（以 { 开头）
    for p in cmd_parts:
        p = p.strip()
        if p.startswith("{") and p.endswith("}"):
            # 替换 # 为 " 以匹配原日志格式
            log_line = p.replace("#", "\"")
            with open(log_path, "a", encoding="gbk") as f:
                f.write(f"{timestamp} {log_line}\n")
            break

# 同时也写到工具箱配置文件方便直接读取
cfg_path = "C:\\ToolBoxConfig.json"
try:
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.loads(f.read())
    else:
        cfg = {}
    for p in cmd_parts:
        p = p.strip()
        if p.startswith("{") and p.endswith("}"):
            cfg["broadcast_cmd"] = p
            break
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(cfg, ensure_ascii=False, indent=4))
except:
    pass

# 静默退出，不渲染画面
sys.exit(0)
'''


def _ensure_fake_scr():
    """确保 fake_scr.py 存在"""
    os.makedirs(cmd_file_path, exist_ok=True)
    if not os.path.exists(FAKE_SCR_FILE):
        with open(FAKE_SCR_FILE, "w", encoding="utf-8") as f:
            f.write(FAKE_SCR_CODE)


def _get_fake_scr_debugger_cmd():
    """返回劫持 ScreenRender.exe 的 Debugger 值"""
    _ensure_fake_scr()
    python_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable
    return f'"{pythonw}" "{FAKE_SCR_FILE}"'


IEOP_KEY_SCR = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\ScreenRender.exe"


def replace_screen_render() -> bool:
    """劫持 ScreenRender.exe，用 fake_scr.py 替代"""
    check_killer_script_is_alreay_start()

    scr_path = os.path.join(toolbox_cfg.oseasy_path, "ScreenRender.exe")
    scr_y_path = os.path.join(toolbox_cfg.oseasy_path, "ScreenRender_Y.exe")

    # 备份原始 ScreenRender.exe
    if os.path.exists(scr_path) and not os.path.exists(scr_y_path):
        run_sigle_cmd(f'rename "{scr_path}" "ScreenRender_Y.exe"')
        time.sleep(2)

    # 确保 fake_scr.py 存在
    _ensure_fake_scr()

    # 注册映像劫持
    debugger = _get_fake_scr_debugger_cmd()
    run_sigle_cmd(
        f'REG ADD "{IEOP_KEY_SCR}" /v Debugger /t REG_SZ /d "{debugger}" /f'
    )
    time.sleep(1)
    return True


def restone_screen_render() -> bool:
    """还原 ScreenRender.exe（删除劫持，恢复原文件）"""
    check_killer_script_is_alreay_start()

    # 删除劫持
    run_sigle_cmd(f'REG DELETE "{IEOP_KEY_SCR}" /v Debugger /f')
    time.sleep(1)

    # 恢复原文件
    scr_path = os.path.join(toolbox_cfg.oseasy_path, "ScreenRender.exe")
    scr_y_path = os.path.join(toolbox_cfg.oseasy_path, "ScreenRender_Y.exe")

    if os.path.exists(scr_y_path):
        # 如果当前有 fake_scr 冒充的 ScreenRender.exe，删掉
        try:
            os.remove(scr_path)
        except FileNotFoundError:
            pass
        run_sigle_cmd(f'rename "{scr_y_path}" "ScreenRender.exe"')
        time.sleep(2)

    return True


def check_replace_screen_render_status() -> bool:
    """通过检查 ScreenRender_Y.exe 是否存在来判断是否已替换"""
    scr_y_path = os.path.join(toolbox_cfg.oseasy_path, "ScreenRender_Y.exe")
    return check_give_file_path_is_excs(scr_y_path)


def from_log_file_get_remote_cmd() -> str | None:
    """从文件中读取拦截到的远程命令\n
    未读取到返回None"""
    return toolbox_cfg.get_config_key_data("broadcast_cmd")


def parse_screenrender_log():
    """
    读取 `%appdata%/Mmc/ScreenRender.log` 文件，\n
    筛选符合特定格式的日志，\n
    并返回替换 " 为 # 的日志命令部分。\n

    `Returns`
        `list`: 包含处理后的命令部分的列表。
    """
    # 获取 %appdata% 路径
    appdata_path = os.getenv("APPDATA")
    if not appdata_path:
        # raise EnvironmentError("无法获取 %APPDATA% 路径")
        Ui_call_show_snake_message("无法获取 %APPDATA% 路径")
        return False, []

    log_path = os.path.join(appdata_path, "Mmc", "ScreenRender.log")
    if not os.path.exists(log_path):
        # raise FileNotFoundError(f"日志文件不存在: {log_path}")
        Ui_call_show_snake_message(f"日志文件不存在: {log_path}")
        return False, []

    # 匹配特定格式的正则表达式
    pattern = re.compile(r"\d{2}-\d{2} \d{2}:\d{2}:\d{2} (\{.*\})")

    result = []

    try:
        with open(log_path, "r", encoding="gbk") as log_file:
            for line in log_file:
                match = pattern.search(line)
                if match:
                    command = match.group(1)
                    # 替换 " 为 #
                    processed_command = command.replace('"', "#")
                    result.append(processed_command)
    except Exception as e:
        # raise RuntimeError(f"读取日志文件时发生错误: {e}")
        Ui_call_show_snake_message(f"读取日志文件时发生错误: {e}")
        return False, []

    if len(result) == 0:
        return False, []

    return True, result


# "C:\Program Files (x86)\Os-Easy\os-easy multicast teaching system\ScreenRender.exe" {#decoderName#:#h264#,#fullscreen#:0,#local#:#172.18.36.132#,#port#:7778,#remote#:#229.1.36.200#,#teacher_ip#:0,#verityPort#:7788}


def save_scr_log_cmd_to_file(log_list=None) -> None:
    """传入`parse_screenrender_log`函数返回的命令列表\n
    或直接调用\n
    保存广播命令日志中的命令到文件"""

    if log_list == []:
        return
    elif log_list == None:
        return save_scr_log_cmd_to_file(parse_screenrender_log())

    path = os.getcwd() + "\\" + "scr_log_cmd.txt"
    with open(path, "w") as f:
        f.write("\n".join(log_list))


def from_scr_log_cmd_get_yccmd() -> None:
    """从屏幕广播日志中提取广播命令\n并保存到文件"""

    status, log_list = parse_screenrender_log()
    if not status:
        return

    save_scr_log_cmd_to_file(log_list)

    handin_save_yc_cmd(log_list[-1], replace_ip=False)


def get_ipv4_address() -> str | None:
    """获取机器IPv4地址"""
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception as e:
        print(f"获取IPv4地址时出现错误: {e}")
        Ui_call_show_snake_message(f"获取IPv4地址时出现错误: {e}")
        return None


def handin_save_yc_cmd(save_cmd, replace_ip=True) -> None:
    """手动保存拦截的命令"""
    global cmd_file_path

    if replace_ip:

        localIp = get_ipv4_address()

        Ui_call_show_snake_message(f"已自动替换本地IP地址为{localIp}")

        save_cmd = re.sub(r"(#local#:)(#.*?#)", rf"\1#{localIp}#", save_cmd)

    toolbox_cfg.set_config_key_data("broadcast_cmd",save_cmd)



def generate_remote_cmd_and_save(teacher_ip) -> None:
    """生成拦截的命令并保存"""
    global cmd_file_path
    localIp = get_ipv4_address()

    cmd_base = "{#decoderName#:#h264#,#fullscreen#:0,#local#:#172.18.36.132#,#port#:7778,#remote#:#229.1.36.200#,#teacher_ip#:0,#verityPort#:7788}"

    save_cmd = re.sub(r"(#local#:)(#.*?#)", rf"\1#{localIp}#", cmd_base)
    save_cmd = re.sub(r"(#remote#:)(#.*?#)", rf"\1#{teacher_ip}#", save_cmd)
    
    toolbox_cfg.set_config_key_data("broadcast_cmd", save_cmd)
    
    print("[DEBUG]", save_cmd)

    Ui_call_show_snake_message(
        f"已尝试按照模板生成广播命令\n若无法使用请使用拦截方案获取命令"
    )



def build_run_broadcast_cmd(YC_command) -> str:
    """构造执行显示命令"""

    status = check_replace_screen_render_status()
    if status == True:
        fdb = f'"{toolbox_cfg.oseasy_path}ScreenRender_Y.exe" {YC_command}'
        return fdb
    else:
        fdb = f'"{toolbox_cfg.oseasy_path}ScreenRender.exe" {YC_command}'
        return fdb


def save_now_broadcast_cmd() -> bool | None:
    """保存现在获取到的远程指令到程序目录"""
    savepath = os.getcwd() + "\\" + "command.txt"

    cmd = toolbox_cfg.get_config_key_data("broadcast_cmd")
    if not cmd:
        return False

    fm = open(savepath, "w")
    fm.write(cmd)
    fm.close()
    return True


def check_replace_screen_render_status() -> bool:
    """通过检查SCR_Y是否存在
    \n来检查是否已经完成替换拦截程序
    \n返回True/False"""
    check_path = f"{toolbox_cfg.oseasy_path}ScreenRender_Y.exe"
    # try:
    #     fm = open(check_path,'r')
    #     fm.close()
    #     return True
    # except FileNotFoundError:
    #     return False

    return check_give_file_path_is_excs(check_path)


def get_proc_pid(name) -> int | None:
    """
    根据进程名获取进程pid\n
    未寻找到返回None
    """
    pids = psutil.process_iter()
    print("[" + name + "]'s pid is:")
    for pid in pids:
        if pid.name() == name:
            print(pid.pid)
            return pid.pid
    return None


def get_time_str() -> str:
    """返回一个时间字符串"""
    time_str = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    return time_str


def get_scshot() -> None:
    """保存一张屏幕截图"""

    savepath = os.getcwd()

    PMsize = pyautogui.size()
    print("DEBUG 屏幕尺寸 > ", PMsize)
    win_h = PMsize.height
    win_w = PMsize.width

    img = pyautogui.screenshot()

    mix_name = savepath + "\\" + get_time_str() + ".jpg"
    img.save(mix_name)
    print("DEBUG SavePath > ", mix_name)


def check_mmpc_status() -> bool:
    """检查MMPC根服务状态\n
    返回True/False"""
    name = "MMPC"
    service = None
    try:
        service = psutil.win_service_get(name)
        service = service.as_dict()
    except Exception as ex:

        return False

    if service and service["status"] == "running":
        return True
    else:
        return False


def run_upto_admin() -> None:
    """用于在非管理员运行时尝试提权"""
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, "".join(sys.argv), None, 1
        )
        sys.exit()


def del_historyrem(*e) -> None:
    """删除保存的历史路径文件"""
    neddel = ["fontPath", "bgPath", "yiyanPath"]

    for i in neddel:
        toolbox_cfg.set_config_key_data(i, None)








def check_killer_script_is_alreay_start() -> None:
    """检测是否开启了击杀脚本\n
    若未开启则帮助启动一次\n
    已经开启则忽略"""
    try:
        window = gw.getWindowsWithTitle("OsEasyToolBoxKiller")[0]
    except:
        script_gen.summon_killer()
        runbat("k.bat")


def open_github_page(*e) -> None:
    """在浏览器打开github仓库页面"""
    webbrowser.open("https://github.com/NYSkyfox/OsEasy-ToolBox")


def start_killer_protect() -> None:
    global is_protect_killer_script_running
    """启动守护进程"""
    ptct = 0
    while is_protect_killer_script_running == True:
        try:
            window = gw.getWindowsWithTitle("OsEasyToolBoxKiller")[0]
            time.sleep(0.5)
        except:
            runbat("k.bat")
            ptct += 1
            time.sleep(1)


def del_self_cmd_files() -> None:
    """删除生成的脚本文件"""
    global cmd_file_path
    for filename in ["k.bat", "d.bat", "temp.bat", "kv2.bat", "net.bat", "usb.bat"]:
        try:
            os.remove(os.path.join(cmd_file_path, filename))
        except FileNotFoundError:
            continue


def backup_oe_files() -> None:
    """备份OE的关键文件"""
    global backup_file_path
    print("[INFO] 尝试备份关键文件")
    namelist = [
        "MultiClient.exe",
        "MultiClient.exe",
        "LoadDriver.exe",
        "BlackSlient.exe",
        "\\x86\\LISSNetInfoSniffer.exe",
    ]
    for filename in namelist:

        oepath = toolbox_cfg.oseasy_path + filename

        needbkpath = backup_file_path + "\\" + filename

        run_sigle_cmd(f'copy "{oepath}" "{needbkpath}"')


def restone_sigle_oe_backup_file(filename: str) -> None:
    global backup_file_path
    oepath = toolbox_cfg.oseasy_path + filename
    needbkpath = backup_file_path + "\\" + filename
    run_sigle_cmd(f'copy "{needbkpath}" "{oepath}"')

def restone_oe_backup_key_dll() -> None:
    """恢复OE关键文件"""
    global backup_file_path
    print("尝试还原关键文件")
    namelist = [
        "oenetlimitx64.cat",
        "OeNetLimitSetup.exe",
        "OeNetLimit.sys",
        "OeNetLimit.inf",
        "MultiClient.exe",
        "LoadDriver.exe",
        "BlackSlient.exe",
        # "\\x86\\LISSNetInfoSniffer.exe",
    ]
    
    faild_file_name = []
    
    for filename in namelist:
        oepath = toolbox_cfg.oseasy_path + filename
        needbkpath = backup_file_path + "\\" + filename

        run_sigle_cmd(f'copy "{needbkpath}" "{oepath}"')
    
    time.sleep(3)
    
    for filename in namelist:
        
        oepath = toolbox_cfg.oseasy_path + filename
        
        cSta = check_give_file_path_is_excs(oepath)
        
        print(f"filename {filename} 复制检测状态 > {cSta}")
        
        if not cSta:
            faild_file_name.append(filename)
    
    if len(faild_file_name) > 0:
        msg_mix = " , ".join(faild_file_name)
        Ui_call_show_snake_message(f"在恢复文件时检测到可能复制失败的文件有: \n{msg_mix}")
        return
    
    Ui_call_show_snake_message("恢复文件完成")
        


def runbat(batname: str) -> None:
    """运行指定名称的bat脚本"""
    global cmd_file_path
    batp = os.path.join(cmd_file_path, batname)
    os.startfile(batp)





def register_killer_script() -> None:
    """生成击杀脚本并绑定粘滞键"""
    script_gen.summon_killer()
    run_sigle_cmd(
        f'REG ADD "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\sethc.exe" /v Debugger /t REG_SZ /d "{cmd_file_path}\\k.bat"'
    )

def del_register_killer() -> None:
    """清理绑定的粘滞键重定向"""
    run_sigle_cmd(
        'REG DELETE "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\sethc.exe" /v Debugger /f'
    )

def register_killer_v2_cmd() -> None:
    """生成击杀脚本V2并绑定粘滞键"""
    script_gen.summon_killer_v2()
    run_sigle_cmd(
        f'REG ADD "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\sethc.exe" /v Debugger /t REG_SZ /d "{cmd_file_path}\\kv2.bat"'
    )


def run_inner_toolbox_killer_loop() -> None:
    global is_box_killer_running
    while is_box_killer_running == True:
        # os.system(command="taskkill /f /t /im Student.exe")
        opt = os.system(f"taskkill /f /t /im {toolbox_cfg.student_exe_name}")
        # print("test run")
        time.sleep(0.2)
    # print(f"[DEBUG] Killer Runned {opt}")


def run_sigle_cmd(givecmd: str, *quiterun: bool) -> None:
    """运行指定的命令"""
    if not quiterun:
        os.popen(cmd=givecmd)
    elif quiterun == False:
        os.system(command=givecmd)
    elif quiterun == True:
        os.popen(cmd=givecmd)
    else:
        os.system(command=givecmd)


def use_bat_file_to_run_cmd(cmd: str) -> None:
    """生成一个临时cmd文件运行指定命令"""
    global cmd_file_path
    mp = cmd_file_path + "\\temp.bat"
    fm = open(mp, "w")
    cmdtext = "@ECHO OFF\n"
    cmdtext += cmd
    cmdtext += "\nexit"
    fm.write(cmdtext)
    fm.close()
    run_sigle_cmd(f"start {mp}")




def selfunc_g1plus(*e) -> None:
    # 注册V2版本的替换击杀脚本
    register_killer_v2_cmd()


def del_locked_exe_then_logout(need_shutdown: bool) -> None:
    script_gen.summon_killer()
    check_killer_script_is_alreay_start()
    script_gen.summon_del_dll(delMtc=True, shutdown=need_shutdown)
    time.sleep(2)
    runbat("d.bat")


def handle_start_student_client(*e) -> None:
    os.startfile(f"{toolbox_cfg.oseasy_path}{toolbox_cfg.student_exe_name}")



def killer_script_protect() -> None:
    global is_protect_killer_script_running
    if is_protect_killer_script_running == False:
        is_protect_killer_script_running = True
        script_gen.summon_killer()
        start_killer_protect()
    elif is_protect_killer_script_running == True:
        is_protect_killer_script_running = False
        use_bat_file_to_run_cmd(
            'taskkill /f /t /fi "imagename eq cmd.exe" /fi "windowtitle eq 管理员:  OsEasyToolBoxKiller"'
        )


# ── 拦截远程重启 ──────────────────────
IEOP_KEY_SHUTDOWN = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\shutdown.exe"

def block_remote_restart() -> bool:
    """
    拦截教师端远程重启（映像劫持 shutdown.exe → 空命令）
    教师端调用 shutdown.exe 时会直接被忽略，不会弹出重启对话框。
    """
    # 用 cmd.exe /c exit /b 0 作为劫持目标
    # 这样 shutdown.exe 被调用时，实际执行的是"退出"而不是关机
    run_sigle_cmd(
        f'REG ADD "{IEOP_KEY_SHUTDOWN}" /v Debugger /t REG_SZ /d "C:\\Windows\\System32\\cmd.exe /c exit /b 0" /f'
    )
    time.sleep(1)
    Ui_call_show_snake_message("已拦截远程重启，教师端无法再重启本机")
    return True

def unblock_remote_restart() -> bool:
    """恢复远程重启（删除 shutdown.exe 的劫持）"""
    run_sigle_cmd(f'REG DELETE "{IEOP_KEY_SHUTDOWN}" /v Debugger /f')
    time.sleep(1)
    Ui_call_show_snake_message("已恢复远程重启")
    return True

def check_block_remote_restart_status() -> bool:
    """检查是否已拦截远程重启"""
    # 通过 reg query 检查劫持是否存在
    result = os.popen(f'REG QUERY "{IEOP_KEY_SHUTDOWN}" /v Debugger 2>nul').read()
    return "Debugger" in result

def handle_run_old_unlock_net() -> None:
    script_gen.summon_unlocknet()
    runbat("net.bat")
    Ui_call_show_snake_message("解锁网络锁定中 请稍等")
    time.sleep(2)
    run_sigle_cmd("sc stop OeNetlimit")
    time.sleep(1)
    use_bat_file_to_run_cmd(
        'taskkill /f /t /fi "imagename eq cmd.exe" /fi "windowtitle eq 管理员:  OsEasyToolBoxUnlockNetHeler"'
    )
    time.sleep(1)
    Ui_call_show_snake_message("执行完成 理论上网络已解锁")


def start_oseasy_self_toolbox(*e) -> None:
    # print("执行功能8 请稍等...")
    register_killer_script()
    check_killer_script_is_alreay_start()
    time.sleep(2)
    # runcmd(f'"')
    os.startfile(f"{toolbox_cfg.oseasy_path}AssistHelper.exe")

# ═══════════════ 映像劫持方案（方案二） ═══════════════
IMAGE_HIJACK_EXES = [
    "LoadDriver.exe",
    "BlackSlient.exe",
    "MultiClient.exe",
    "LISSNetInfoSniffer.exe",
]

IMAGE_HIJACK_DLLS = [
    "LockKeyboard.dll",
]

IEOP_KEY = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"

# ── 劫持 stub ──────────────────────────────────
HIJACK_STUB_FILE = os.path.join(cmd_file_path, "hijack_stub.py")
HIJACK_STUB_CODE = r'''# -*- coding: utf-8 -*-
# OsEasy-ToolBox 广播拦截提示
import tkinter as tk
from tkinter import messagebox
import sys

root = tk.Tk()
root.title("OsEasy-ToolBox 提示")
root.attributes("-topmost", True)
# 窗口居中
sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()
x = (sw - 350) // 2
y = (sh - 120) // 2
root.geometry(f"350x120+{x}+{y}")
root.resizable(False, False)

# 标签
label = tk.Label(root, text="☑ 屏幕广播已拦截",
                 font=("微软雅黑", 14, "bold"),
                 fg="#0078D4")
label.pack(expand=True)

# 自动关闭
root.after(3000, root.destroy)
root.mainloop()
sys.exit(0)
'''


def _ensure_hijack_stub():
    """确保 hijack_stub.py 存在"""
    os.makedirs(cmd_file_path, exist_ok=True)
    if not os.path.exists(HIJACK_STUB_FILE):
        with open(HIJACK_STUB_FILE, "w", encoding="utf-8") as f:
            f.write(HIJACK_STUB_CODE)


def _get_hijack_debugger_cmd():
    """返回注册表 Debugger 值，指向 pythonw.exe + hijack_stub.py"""
    _ensure_hijack_stub()
    # 找出 pythonw.exe 路径
    python_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw):
        # 有些 Python 安装可能没 pythonw.exe，用 python.exe 代替
        pythonw = sys.executable
    return f'"{pythonw}" "{HIJACK_STUB_FILE}"'


def hijack_rename_file(full_path: str) -> bool:
    """重命名文件为 .bak 备份"""
    if not os.path.exists(full_path):
        return False
    bak_path = full_path + ".bak"
    try:
        os.rename(full_path, bak_path)
        return True
    except:
        return False


def hijack_restore_file(full_path: str) -> bool:
    """恢复 .bak 备份"""
    bak_path = full_path + ".bak"
    if not os.path.exists(bak_path):
        return False
    try:
        os.rename(bak_path, full_path)
        return True
    except:
        return False


def hijack_register_exe(exe_name: str) -> str:
    """注册EXE的映像劫持，劫持到自定义 Python stub（弹窗提示已拦截），返回状态消息"""
    key = f'{IEOP_KEY}\\{exe_name}'
    debugger = _get_hijack_debugger_cmd()
    # 先备份原文件
    full = os.path.join(toolbox_cfg.oseasy_path, exe_name)
    if hijack_rename_file(full):
        run_sigle_cmd(f'REG ADD "{key}" /v Debugger /t REG_SZ /d "{debugger}" /f')
        return f"✓ {exe_name} 已劫持（弹窗提示）"
    else:
        run_sigle_cmd(f'REG ADD "{key}" /v Debugger /t REG_SZ /d "{debugger}" /f')
        return f"⚠ {exe_name} 文件不存在，仍写入注册表"


def hijack_unregister_exe(exe_name: str) -> str:
    """移除EXE的映像劫持并恢复原文件"""
    key = f'{IEOP_KEY}\\{exe_name}'
    run_sigle_cmd(f'REG DELETE "{key}" /v Debugger /f')
    full = os.path.join(toolbox_cfg.oseasy_path, exe_name)
    if hijack_restore_file(full):
        return f"✓ {exe_name} 已恢复"
    else:
        return f"⚠ {exe_name} 无备份文件可恢复"


def hijack_rename_dll(dll_name: str) -> str:
    """重命名DLL使其失效"""
    full = os.path.join(toolbox_cfg.oseasy_path, dll_name)
    if hijack_rename_file(full):
        return f"✓ {dll_name} 已重命名屏蔽"
    else:
        return f"⚠ {dll_name} 文件不存在或重命名失败"


def hijack_restore_dll(dll_name: str) -> str:
    """恢复被重命名的DLL"""
    full = os.path.join(toolbox_cfg.oseasy_path, dll_name)
    if hijack_restore_file(full):
        return f"✓ {dll_name} 已恢复"
    else:
        return f"⚠ {dll_name} 无备份文件可恢复"


def unlock_with_hijack(shutdown: bool = True):
    """方案二：映像劫持解锁（不删除任何文件）"""
    Ui_call_show_snake_message("开始映像劫持方案...")
    # 1. 启动击杀脚本
    script_gen.summon_killer()
    check_killer_script_is_alreay_start()
    time.sleep(1)

    # 2. 劫持所有EXE
    results = []
    for exe_name in IMAGE_HIJACK_EXES:
        results.append(hijack_register_exe(exe_name))

    # 3. 重命名所有DLL
    for dll_name in IMAGE_HIJACK_DLLS:
        results.append(hijack_rename_dll(dll_name))

    # 4. 输出结果
    msg = "\n".join(results)
    Ui_call_show_snake_message(f"映像劫持完成:\n{msg}")

    if shutdown:
        time.sleep(3)
        run_sigle_cmd("shutdown /l")


def restore_from_hijack():
    """还原映像劫持方案"""
    results = []
    for exe_name in IMAGE_HIJACK_EXES:
        results.append(hijack_unregister_exe(exe_name))
    for dll_name in IMAGE_HIJACK_DLLS:
        results.append(hijack_restore_dll(dll_name))
    msg = "\n".join(results)
    Ui_call_show_snake_message(f"恢复完成:\n{msg}")
