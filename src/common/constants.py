#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
常量定义模块 - 集中管理项目中的所有静态变量
"""

import os
import sys

# 应用程序信息
APP_NAME = "灵魂面甲服务器启动器"
APP_VERSION = "V0.1"
APP_TITLE = f"{APP_NAME} {APP_VERSION}"

# 获取应用程序目录的函数
def get_app_dir():
    """获取应用程序目录，处理打包后的路径问题"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        return os.path.dirname(sys.executable)
    else:
        # 如果是源码运行
        # 获取当前文件的绝对路径
        current_file = os.path.abspath(__file__)
        # 获取common目录的路径
        common_dir = os.path.dirname(current_file)
        # 获取src目录的路径
        src_dir = os.path.dirname(common_dir)
        # 获取应用程序根目录（src的父目录）
        app_dir = os.path.dirname(src_dir)
        return app_dir

# 统一路径配置类
class PathConfig:
    """统一的路径配置管理类"""
    
    def __init__(self, root_dir=None):
        self._root_dir = root_dir or get_app_dir()
    
    @property
    def root_dir(self):
        """服务器根目录"""
        return self._root_dir
    
    @root_dir.setter
    def root_dir(self, value):
        """设置服务器根目录"""
        self._root_dir = value
    
    @property
    def steamcmd_dir(self):
        """SteamCMD目录"""
        return os.path.join(self._root_dir, "steamcmd")
    
    @property
    def steamcmd_exe(self):
        """SteamCMD可执行文件路径"""
        return os.path.join(self.steamcmd_dir, "steamcmd.exe")
    
    @property
    def game_install_dir(self):
        """游戏安装目录"""
        path = os.path.join(self.steamcmd_dir, "steamapps", "common", "Soulmask Dedicated Server For Windows")
        return os.path.normpath(path)
    
    @property
    def server_exe(self):
        """服务器可执行文件路径"""
        return os.path.join(self.game_install_dir, "WSServer.exe")
    
    @property
    def backup_dir(self):
        """备份目录 - 放在exe执行目录下"""
        return os.path.join(get_app_dir(), "backups")
    
    @property
    def logs_dir(self):
        """日志目录 - 放在exe执行目录下"""
        return os.path.join(get_app_dir(), "logs")
    
    @property
    def log_file(self):
        """日志文件路径"""
        return os.path.join(self.logs_dir, "launcher.log")
    
    @property
    def configs_dir(self):
        """配置目录 - 放在exe执行目录下"""
        return os.path.join(get_app_dir(), "configs")
    
    @property
    def config_file(self):
        """配置文件路径"""
        return os.path.join(self.configs_dir, "server_config.json")
    
    def get_all_paths(self):
        """获取所有路径的字典"""
        return {
            'root_dir': self.root_dir,
            'steamcmd_dir': self.steamcmd_dir,
            'steamcmd_exe': self.steamcmd_exe,
            'game_install_dir': self.game_install_dir,
            'server_exe': self.server_exe,
            'backup_dir': self.backup_dir,
            'logs_dir': self.logs_dir,
            'log_file': self.log_file,
            'configs_dir': self.configs_dir,
            'config_file': self.config_file
        }

# 默认路径配置实例
DEFAULT_PATHS = PathConfig()

# 为了向后兼容，保留原有的常量名
APP_DIR = get_app_dir()
DEFAULT_STEAMCMD_DIR = DEFAULT_PATHS.steamcmd_dir
DEFAULT_STEAMCMD_EXE = DEFAULT_PATHS.steamcmd_exe
DEFAULT_server_path = DEFAULT_PATHS.game_install_dir
DEFAULT_SERVER_EXE = "WSServer.exe"
DEFAULT_BACKUP_DIR = DEFAULT_PATHS.backup_dir
DEFAULT_LOG_FILE = DEFAULT_PATHS.log_file
DEFAULT_CONFIG_FILE = DEFAULT_PATHS.config_file

# SteamCMD 相关
STEAMCMD_DOWNLOAD_URLS = [
    "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip",
    "https://steamcmd.net/steamcmd.zip"
]
GAME_APP_ID = "3017310"  # 灵魂面甲服务器的 Steam AppID

# 服务器默认配置
DEFAULT_SERVER_CONFIG = {
    "server_name": "灵魂面甲服务器",
    "max_players": 20,
    "port": 7777,
    "multihome": "0.0.0.0",  # 服务器监听地址
    "game_mode": "pve",  # 游戏模式：pve或pvp
    "auto_backup": True,
    "backup_interval": 30,  # 分钟
    "steamcmd_path": "",  # 自定义SteamCMD路径
    "server_path": "",  # 服务端路径
    "backup_dir": "",  # 自定义备份目录
    "log_file_path": "",  # 自定义日志文件路径
    "config_file_path": "",  # 自定义配置文件路径
    "rcon_enabled": True,  # 是否启用RCON
    "rcon_addr": "127.0.0.1",  # RCON地址
    "rcon_port": 25575,  # RCON端口
    "rcon_password": "admin",  # RCON密码
    "extra_args": ""  # 额外启动参数
}

# RCON相关常量
DEFAULT_RCON_PORT = 25575
DEFAULT_RCON_PASSWORD = "admin"
RCON_TIMEOUT = 10  # RCON连接超时时间（秒）

# 日志相关
MAX_LOG_LINES = 1000  # 最大日志行数
LOG_LEVELS = ["INFO", "WARNING", "ERROR", "SUCCESS"]

# UI相关
STATUS_CHECK_INTERVAL = 5000  # 服务器状态检查间隔（毫秒）
GAME_MODE_OPTIONS = ["pve", "pvp"]
APP_GEOMETRY = (50, 50, 1200, 800)  # 窗口位置和大小，紧贴屏幕上边

# UI标签文本
UI_LABELS = {
    'paths_tab_info': "在此页面可以自定义各种路径设置。修改后需点击保存按钮生效。",
    'paths_group': "路径设置",
    'steamcmd_path': "SteamCMD路径:",
    'server_path': "游戏安装路径:",
    'backup_dir': "备份目录:",
    'log_file_path': "日志文件路径:",
    'config_file_path': "配置文件路径:"
}

# UI对话框标题
UI_DIALOG_TITLES = {
    'steamcmd_path': "选择SteamCMD目录",
    'server_path': "选择游戏安装目录",
    'backup_dir': "选择备份目录",
    'log_file_path': "设置日志文件路径",
    'config_file_path': "设置配置文件路径",
    'log_file_filter': "日志文件 (*.log);;所有文件 (*.*)",
    'config_file_filter': "JSON文件 (*.json);;所有文件 (*.*)"
}

# UI按钮文本
UI_BUTTON_TEXTS = {
    'browse': "浏览",
    'save_settings': "保存设置",
    'reset_default': "重置为默认",
    'start_server': "启动服务器",
    'stop_server': "停止服务器",
    'install_steamcmd': "安装SteamCMD",
    'install_game': "安装/更新服务端",
    'validate_game': "验证服务端文件",
    'create_backup': "创建备份",
    'restore_backup': "恢复备份",
    'delete_backup': "删除备份",
    'clear_logs': "清除日志"
}

# 备份相关
DEFAULT_BACKUP_INTERVAL = 30  # 默认备份间隔（分钟）
DEFAULT_KEEP_BACKUPS_COUNT = 10  # 默认保留的备份数量