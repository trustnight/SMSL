#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
通用工具函数模块 - 路径处理专用
"""

import os
import sys
import ipaddress
from .constants import (DEFAULT_STEAMCMD_DIR, DEFAULT_STEAMCMD_EXE, DEFAULT_server_path, 
                        DEFAULT_SERVER_EXE, DEFAULT_BACKUP_DIR, DEFAULT_LOG_FILE, DEFAULT_CONFIG_FILE,
                        get_app_dir, APP_DIR)


def get_steamcmd_dir(custom_path=None):
    """获取SteamCMD目录，支持自定义路径"""
    if custom_path:
        return custom_path
    return DEFAULT_STEAMCMD_DIR


def get_steamcmd_exe_path(custom_path=None):
    """获取SteamCMD可执行文件路径，支持自定义路径"""
    if custom_path:
        return os.path.join(custom_path, "steamcmd.exe")
    return DEFAULT_STEAMCMD_EXE


def get_server_path(custom_path=None):
    """获取游戏安装路径，支持自定义路径"""
    if custom_path:
        return custom_path
    return DEFAULT_server_path


def get_server_exe_path(server_path=None):
    """获取服务器可执行文件路径"""
    if server_path is None:
        server_path = get_server_path()
    return os.path.join(server_path, "StartServer.bat")


def get_backup_dir(custom_path=None):
    """获取备份目录，支持自定义路径"""
    if custom_path:
        return custom_path
    return DEFAULT_BACKUP_DIR


def get_log_file_path(custom_path=None):
    """获取日志文件路径，支持自定义路径"""
    if custom_path:
        return custom_path
    return DEFAULT_LOG_FILE


def get_config_file_path(custom_path=None):
    """获取配置文件路径，支持自定义路径"""
    if custom_path:
        return custom_path
    return DEFAULT_CONFIG_FILE


def ensure_dir_exists(dir_path):
    """确保目录存在，如果不存在则创建"""
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"创建目录失败: {dir_path}, 错误: {str(e)}")
        return False


def is_valid_path(path):
    """检查路径是否有效"""
    return path and os.path.exists(path)


def is_steamcmd_installed(custom_path=None):
    """检查SteamCMD是否已安装，支持自定义路径"""
    return os.path.exists(get_steamcmd_exe_path(custom_path))


def is_game_installed(custom_path=None):
    """检查游戏是否已安装，支持自定义路径"""
    return os.path.exists(get_server_exe_path(custom_path))


def get_file_size_mb(file_path):
    """获取文件大小（MB）"""
    try:
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        return 0
    except Exception:
        return 0


def get_dir_size(dir_path):
    """获取目录大小（字节）"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(dir_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
    except Exception:
        pass
    return total_size


def format_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_backup_file_path(backup_name):
    """获取备份文件完整路径"""
    return os.path.join(get_backup_dir(), f"{backup_name}.zip")


def get_save_game_dir(server_path):
    """获取存档目录路径"""
    return os.path.join(server_path, "savegame")


def get_logs_dir(server_path):
    """获取服务器日志目录路径"""
    return os.path.join(server_path, "logs")


def get_config_files_list():
    """获取需要备份的配置文件列表"""
    return [
        "enshrouded_server.json",
        "server.properties",
        "whitelist.txt",
        "blacklist.txt"
    ]


def get_config_file_path_in_server(server_path, config_file):
    """获取服务器目录中配置文件的完整路径"""
    return os.path.join(server_path, config_file)


def validate_ip_address(ip):
    """验证IP地址格式是否正确"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_port(port):
    """验证端口号是否有效"""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False