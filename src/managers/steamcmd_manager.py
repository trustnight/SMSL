#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SteamCMD管理模块
"""

import os
import subprocess
import zipfile
import requests
from PySide6.QtCore import QObject, Signal, QThread
from ..common.constants import DEFAULT_STEAMCMD_DIR, DEFAULT_STEAMCMD_EXE, STEAMCMD_DOWNLOAD_URLS, GAME_APP_ID


class SteamCMDDownloadThread(QThread):
    """SteamCMD下载线程"""
    progress_updated = Signal(int)  # 下载进度信号
    download_finished = Signal(bool, str)  # 下载完成信号
    
    def __init__(self, download_url, save_path):
        super().__init__()
        self.download_url = download_url
        self.save_path = save_path
    
    def run(self):
        try:
            response = requests.get(self.download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(self.save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.progress_updated.emit(progress)
            
            self.download_finished.emit(True, "下载完成")
            
        except Exception as e:
            self.download_finished.emit(False, f"下载失败: {str(e)}")


class SteamCMDManager(QObject):
    """SteamCMD管理器"""
    # 信号定义
    download_progress = Signal(int)  # 下载进度信号
    download_finished = Signal(bool, str)  # 下载完成信号
    installation_progress = Signal(str)  # 安装进度信号
    installation_finished = Signal(bool, str)  # 安装完成信号
    log_message = Signal(str)  # 日志消息信号
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self.steamcmd_dir = DEFAULT_STEAMCMD_DIR
        self.steamcmd_exe = DEFAULT_STEAMCMD_EXE
        self.download_thread = None
        
        # SteamCMD下载链接
        self.steamcmd_urls = STEAMCMD_DOWNLOAD_URLS
        
        # 如果提供了配置管理器，从配置中获取路径
        if self.config_manager:
            self.update_paths_from_config()
    
    def update_paths_from_config(self):
        """从配置中更新路径"""
        if self.config_manager:
            steamcmd_path = self.config_manager.get_config("steamcmd_path")
            if steamcmd_path and os.path.exists(steamcmd_path):
                self.steamcmd_dir = steamcmd_path
                self.steamcmd_exe = os.path.join(self.steamcmd_dir, "steamcmd.exe")
    
    def is_steamcmd_installed(self):
        """检查SteamCMD是否已安装"""
        return os.path.exists(self.steamcmd_exe)
    
    def check_steamcmd_installed(self):
        """检查SteamCMD是否已安装（GUI调用的方法）"""
        return self.is_steamcmd_installed()
    
    def install_steamcmd(self):
        """安装SteamCMD（GUI调用的方法）"""
        return self.download_steamcmd()
    
    def download_steamcmd(self, download_path=None):
        """下载SteamCMD"""
        if download_path:
            self.steamcmd_dir = download_path
            self.steamcmd_exe = os.path.join(self.steamcmd_dir, "steamcmd.exe")
        
        # 确保目录存在
        os.makedirs(self.steamcmd_dir, exist_ok=True)
        
        zip_path = os.path.join(self.steamcmd_dir, "steamcmd.zip")
        
        # 尝试从多个源下载
        for url in self.steamcmd_urls:
            try:
                self.log_message.emit(f"正在从 {url} 下载SteamCMD...")
                
                self.download_thread = SteamCMDDownloadThread(url, zip_path)
                self.download_thread.progress_updated.connect(self.download_progress.emit)
                self.download_thread.download_finished.connect(self._on_download_finished)
                self.download_thread.start()
                
                return True
                
            except Exception as e:
                self.log_message.emit(f"从 {url} 下载失败: {str(e)}")
                continue
        
        self.download_finished.emit(False, "所有下载源都失败了")
        return False
    
    def _on_download_finished(self, success, message):
        """下载完成处理"""
        if success:
            self.log_message.emit("SteamCMD下载完成，正在解压...")
            zip_path = os.path.join(self.steamcmd_dir, "steamcmd.zip")
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(self.steamcmd_dir)
                
                # 删除zip文件
                os.remove(zip_path)
                
                self.log_message.emit("SteamCMD安装完成")
                self.download_finished.emit(True, "")
                
            except Exception as e:
                self.download_finished.emit(False, f"解压失败: {str(e)}")
        else:
            self.download_finished.emit(False, message)
    
    def install_game(self, app_id=GAME_APP_ID, validate=False):
        """安装/更新游戏"""
        if not self.is_steamcmd_installed():
            self.installation_finished.emit(False, "SteamCMD未安装")
            return False
        
        # 在独立线程中执行安装，避免阻塞GUI
        import threading
        def install_thread():
            try:
                # 获取游戏安装路径
                server_path = self.get_server_path()
                
                # 构建SteamCMD命令
                cmd = [
                    self.steamcmd_exe,
                    "+force_install_dir", server_path,
                    "+login", "anonymous",
                    "+app_update", app_id
                ]
                
                if validate:
                    cmd.append("validate")
                
                cmd.append("+quit")
                
                self.log_message.emit("正在启动SteamCMD...")
                self.installation_progress.emit("正在连接Steam...")
                
                # 执行SteamCMD命令 - 不弹出cmd窗口，输出重定向到GUI，使用无缓冲模式
                process = subprocess.Popen(
                    cmd,
                    cwd=self.steamcmd_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    bufsize=0  # 无缓冲模式，实现实时输出
                )
                
                # 实时读取输出并显示在GUI日志窗口中
                self.installation_progress.emit("正在安装/更新游戏...")
                
                # 实时监控输出 - 优化版本
                last_progress_type = None
                try:
                    while True:
                        line = process.stdout.readline()
                        if not line and process.poll() is not None:
                            break
                        if line:
                            line = line.strip()
                            if line:
                                self.log_message.emit(f"SteamCMD: {line}")
                                
                                # 改进的进度检测，避免重复消息
                                current_progress = None
                                if "downloading" in line.lower() and "[" in line and "%" in line:
                                    current_progress = "downloading"
                                elif "verifying" in line.lower() or "progress:" in line.lower():
                                    current_progress = "verifying"
                                elif "installing" in line.lower():
                                    current_progress = "installing"
                                elif "success" in line.lower() or "fully installed" in line.lower():
                                    current_progress = "completed"
                                
                                # 只在进度类型改变时发送消息
                                if current_progress and current_progress != last_progress_type:
                                    if current_progress == "downloading":
                                        self.installation_progress.emit("正在下载游戏文件...")
                                    elif current_progress == "verifying":
                                        self.installation_progress.emit("正在验证游戏文件...")
                                    elif current_progress == "installing":
                                        self.installation_progress.emit("正在安装游戏文件...")
                                    elif current_progress == "completed":
                                        self.installation_progress.emit("安装完成")
                                    last_progress_type = current_progress
                    process.stdout.close()
                except Exception as e:
                    self.log_message.emit(f"读取SteamCMD输出时出错: {str(e)}")
                
                # 等待进程完成
                process.wait()
                
                if process.returncode == 0:
                    self.log_message.emit("游戏安装/更新完成")
                    self.installation_finished.emit(True, "")
                else:
                    self.log_message.emit(f"SteamCMD执行失败，返回码: {process.returncode}")
                    self.installation_finished.emit(False, f"安装失败，返回码: {process.returncode}")
                    
            except Exception as e:
                error_msg = f"安装游戏时出错: {str(e)}"
                self.log_message.emit(error_msg)
                self.installation_finished.emit(False, error_msg)
        
        # 启动安装线程
        thread = threading.Thread(target=install_thread, daemon=True)
        thread.start()
        return True
    
    def validate_game(self, app_id=GAME_APP_ID):
        """验证游戏文件"""
        return self.install_game(app_id, validate=True)
    
    def get_server_path(self):
        """获取游戏安装路径"""
        if self.config_manager:
            custom_path = self.config_manager.get_config("server_path")
            if custom_path and os.path.exists(os.path.dirname(custom_path)):
                return os.path.normpath(custom_path)
        path = os.path.join(self.steamcmd_dir, "steamapps", "common", "Soulmask Dedicated Server For Windows")
        return os.path.normpath(path)
    
    def is_game_installed(self):
        """检查游戏是否已安装"""
        game_path = self.get_server_path()
        server_exe = os.path.join(game_path, "StartServer.bat")
        return os.path.exists(server_exe)
    
    def check_game_installed(self):
        """检查游戏是否已安装（GUI调用的方法）"""
        return self.is_game_installed()
    
    def get_steamcmd_dir(self):
        """获取SteamCMD目录"""
        return self.steamcmd_dir
    
    def set_steamcmd_dir(self, path):
        """设置SteamCMD目录"""
        self.steamcmd_dir = path
        self.steamcmd_exe = os.path.join(self.steamcmd_dir, "steamcmd.exe")
        
    def set_server_path(self, path):
        """设置游戏安装路径"""
        if self.config_manager:
            self.config_manager.set_config("server_path", path)