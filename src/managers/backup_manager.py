#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
备份管理模块
"""

import os
import shutil
import zipfile
from datetime import datetime
import threading
import time
from PySide6.QtCore import QObject, Signal, QTimer
from ..common.utils import get_app_dir
from ..common.constants import DEFAULT_BACKUP_DIR, DEFAULT_BACKUP_INTERVAL, DEFAULT_KEEP_BACKUPS_COUNT


class BackupManager(QObject):
    """备份管理器"""
    # 信号定义
    backup_started = Signal(str)  # 备份开始信号
    backup_finished = Signal(bool, str)  # 备份完成信号
    backup_progress = Signal(str)  # 备份进度信号
    log_message = Signal(str)  # 日志消息信号
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self.backup_dir = DEFAULT_BACKUP_DIR
        self.auto_backup_timer = QTimer()
        self.auto_backup_timer.timeout.connect(self.auto_backup)
        self.auto_backup_enabled = False
        self.backup_interval = DEFAULT_BACKUP_INTERVAL
        self.server_path = ""
        
        # 如果有配置管理器，从配置中更新路径
        if self.config_manager:
            self.update_paths_from_config()
        
        # 不在初始化时创建目录，延迟到真正需要时创建
    
    def set_server_path(self, path):
        """设置服务器路径"""
        self.server_path = path
    
    def set_auto_backup(self, enabled, interval_minutes=30):
        """设置自动备份"""
        self.auto_backup_enabled = enabled
        self.backup_interval = interval_minutes
        
        if enabled:
            self.auto_backup_timer.start(interval_minutes * 60 * 1000)  # 转换为毫秒
            self.log_message.emit(f"自动备份已启用，间隔: {interval_minutes} 分钟")
        else:
            self.auto_backup_timer.stop()
            self.log_message.emit("自动备份已禁用")
    
    def create_backup(self, backup_name=None, include_logs=True):
        """创建备份"""
        if not self.server_path or not os.path.exists(self.server_path):
            self.backup_finished.emit(False, "服务器路径无效")
            return False
        
        # 确保备份目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
        
        try:
            # 生成备份名称
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}"
            
            backup_file = os.path.join(self.backup_dir, f"{backup_name}.zip")
            
            self.backup_started.emit(backup_name)
            self.log_message.emit(f"开始创建备份: {backup_name}")
            
            # 在后台线程中执行备份
            threading.Thread(
                target=self._create_backup_thread,
                args=(backup_file, include_logs),
                daemon=True
            ).start()
            
            return True
            
        except Exception as e:
            error_msg = f"创建备份时出错: {str(e)}"
            self.log_message.emit(error_msg)
            self.backup_finished.emit(False, error_msg)
            return False
    
    def _create_backup_thread(self, backup_file, include_logs):
        """备份线程函数"""
        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 备份整个WS\Saved目录（包含世界存档）
                saved_dir = os.path.join(self.server_path, "WS", "Saved")
                if os.path.exists(saved_dir):
                    self.backup_progress.emit("正在备份世界存档文件...")
                    for root, dirs, files in os.walk(saved_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # 保持相对路径结构
                            arc_path = os.path.relpath(file_path, self.server_path)
                            zipf.write(file_path, arc_path)
                            
                            # 显示备份进度
                            if file.endswith(('.sav', '.db')):
                                self.backup_progress.emit(f"备份存档文件: {file}")
                else:
                    self.backup_progress.emit("⚠️ 未找到WS\\Saved目录")
                
                # 备份服务器配置文件
                config_files = [
                    "ServerSettings.ini",
                    "Game.ini",
                    "Engine.ini"
                ]
                
                self.backup_progress.emit("正在备份配置文件...")
                for config_file in config_files:
                    config_path = os.path.join(self.server_path, "WS", "Saved", "Config", "WindowsServer", config_file)
                    if os.path.exists(config_path):
                        arc_path = os.path.relpath(config_path, self.server_path)
                        zipf.write(config_path, arc_path)
                        self.backup_progress.emit(f"备份配置文件: {config_file}")
                
                # 备份日志文件（可选）
                if include_logs:
                    self.backup_progress.emit("正在备份日志文件...")
                    logs_dir = os.path.join(self.server_path, "WS", "Saved", "Logs")
                    if os.path.exists(logs_dir):
                        for root, dirs, files in os.walk(logs_dir):
                            for file in files:
                                if file.endswith('.log') or file.endswith('.txt'):
                                    file_path = os.path.join(root, file)
                                    arc_path = os.path.relpath(file_path, self.server_path)
                                    zipf.write(file_path, arc_path)
                                    self.backup_progress.emit(f"备份日志文件: {file}")
            
            # 获取备份文件大小
            backup_size = os.path.getsize(backup_file)
            size_mb = backup_size / (1024 * 1024)
            
            success_msg = f"备份创建成功: {os.path.basename(backup_file)} ({size_mb:.2f} MB)"
            self.log_message.emit(success_msg)
            
            # 清理旧备份
            self._cleanup_old_backups()
            
            self.backup_finished.emit(True, success_msg)
            
        except Exception as e:
            error_msg = f"备份过程中出错: {str(e)}"
            self.log_message.emit(error_msg)
            self.backup_finished.emit(False, error_msg)
    
    def restore_backup(self, backup_file):
        """恢复备份（会先自动保存当前存档）"""
        # 如果传入的是文件名而不是完整路径，则构建完整路径
        if not os.path.isabs(backup_file):
            backup_file = os.path.join(self.backup_dir, backup_file)
        
        if not os.path.exists(backup_file):
            self.backup_finished.emit(False, "备份文件不存在")
            return False
        
        if not self.server_path or not os.path.exists(self.server_path):
            self.backup_finished.emit(False, "服务器路径无效")
            return False
        
        try:
            self.backup_started.emit("恢复备份")
            self.log_message.emit(f"开始恢复备份: {os.path.basename(backup_file)}")
            
            # 在后台线程中执行恢复（包含先保存当前存档）
            threading.Thread(
                target=self._restore_backup_thread,
                args=(backup_file,),
                daemon=True
            ).start()
            
            return True
            
        except Exception as e:
            error_msg = f"恢复备份时出错: {str(e)}"
            self.log_message.emit(error_msg)
            self.backup_finished.emit(False, error_msg)
            return False
    
    def _restore_backup_thread(self, backup_file):
        """恢复备份线程函数（先保存当前存档）"""
        try:
            # 第一步：先保存当前存档
            self.backup_progress.emit("正在保存当前存档...")
            self.log_message.emit("恢复前先保存当前存档...")
            
            # 生成当前存档备份的文件名（添加"恢复前"标识）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_backup_name = f"恢复前备份_{timestamp}.zip"
            current_backup_path = os.path.join(self.backup_dir, current_backup_name)
            
            # 创建当前存档的备份（只备份WS/Saved目录）
            with zipfile.ZipFile(current_backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                file_count = 0
                processed_count = 0
                
                # 只备份WS/Saved目录
                saved_dir = os.path.join(self.server_path, "WS", "Saved")
                if os.path.exists(saved_dir):
                    # 先统计文件总数
                    for root, dirs, files in os.walk(saved_dir):
                        file_count += len(files)
                    
                    # 备份文件并显示进度
                    for root, dirs, files in os.walk(saved_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, self.server_path)
                            zipf.write(file_path, arcname)
                            
                            processed_count += 1
                            if file_count > 0:
                                progress = int((processed_count / file_count) * 50)  # 保存当前存档占50%进度
                                self.backup_progress.emit(f"正在保存当前存档... {progress}%")
                else:
                    self.backup_progress.emit("⚠️ 未找到WS\\Saved目录，跳过当前存档备份")
            
            self.log_message.emit(f"当前存档已保存为: {current_backup_name}")
            
            # 第二步：恢复选中的备份
            self.backup_progress.emit("正在恢复备份文件...")
            self.log_message.emit(f"开始恢复备份: {os.path.basename(backup_file)}")
            
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                file_list = zipf.namelist()
                total_files = len(file_list)
                
                for i, file_info in enumerate(zipf.infolist()):
                    zipf.extract(file_info, self.server_path)
                    
                    # 更新进度（恢复过程占50%-100%）
                    if total_files > 0:
                        progress = 50 + int((i + 1) / total_files * 50)
                        self.backup_progress.emit(f"正在恢复备份文件... {progress}%")
            
            success_msg = f"备份恢复成功: {os.path.basename(backup_file)}"
            self.log_message.emit(success_msg)
            self.backup_finished.emit(True, success_msg)
            
        except Exception as e:
            error_msg = f"恢复备份过程中出错: {str(e)}"
            self.log_message.emit(error_msg)
            self.backup_finished.emit(False, error_msg)
    
    def auto_backup(self):
        """自动备份"""
        if self.auto_backup_enabled:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"auto_backup_{timestamp}"
            self.log_message.emit("执行自动备份...")
            self.create_backup(backup_name, include_logs=False)
    
    def get_backup_list(self):
        """获取备份列表"""
        backups = []
        try:
            for file in os.listdir(self.backup_dir):
                if file.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, file)
                    stat = os.stat(file_path)
                    backups.append({
                        'name': file,
                        'path': file_path,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime),
                        'modified': datetime.fromtimestamp(stat.st_mtime)
                    })
            
            # 按创建时间排序
            backups.sort(key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            self.log_message.emit(f"获取备份列表时出错: {str(e)}")
        
        return backups
    
    def delete_backup(self, backup_file):
        """删除备份"""
        try:
            # 如果传入的是文件名而不是完整路径，则构建完整路径
            if not os.path.isabs(backup_file):
                backup_file = os.path.join(self.backup_dir, backup_file)
            
            if os.path.exists(backup_file):
                os.remove(backup_file)
                self.log_message.emit(f"备份已删除: {os.path.basename(backup_file)}")
                return True
            else:
                self.log_message.emit("备份文件不存在")
                return False
                
        except Exception as e:
            error_msg = f"删除备份时出错: {str(e)}"
            self.log_message.emit(error_msg)
            return False
    
    def _cleanup_old_backups(self):
        """清理旧备份，保留指定数量的最新备份"""
        try:
            if not self.config_manager:
                return
                
            # 获取保留备份数量设置
            keep_count = self.config_manager.get_config("keep_backups_count")
            if keep_count is None:
                keep_count = 5  # 默认保留5个备份
            
            if keep_count <= 0:
                return  # 如果设置为0或负数，不删除任何备份
                
            # 获取所有备份文件
            if not os.path.exists(self.backup_dir):
                return
                
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, file)
                    if os.path.isfile(file_path):
                        # 获取文件修改时间
                        mtime = os.path.getmtime(file_path)
                        backup_files.append((file_path, mtime))
            
            # 按修改时间排序，最新的在前
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # 如果备份数量超过保留数量，删除多余的
            if len(backup_files) > keep_count:
                files_to_delete = backup_files[keep_count:]
                
                for file_path, _ in files_to_delete:
                    try:
                        os.remove(file_path)
                        self.log_message.emit(f"已删除旧备份: {os.path.basename(file_path)}")
                    except Exception as e:
                        self.log_message.emit(f"删除旧备份失败 {os.path.basename(file_path)}: {str(e)}")
                        
                self.log_message.emit(f"清理完成，保留最新 {keep_count} 个备份")
                
        except Exception as e:
            self.log_message.emit(f"清理旧备份时出错: {str(e)}")
    
    def get_backup_dir(self):
        """获取备份目录"""
        return self.backup_dir
    
    def set_backup_dir(self, path):
        """设置备份目录"""
        self.backup_dir = path
        # 不在设置时创建目录，只在需要时创建
        
        # 如果有配置管理器，更新配置
        if self.config_manager:
            self.config_manager.set_config("backup_dir", path)
    
    def update_paths_from_config(self):
        """从配置中更新路径"""
        if not self.config_manager:
            return
            
        # 获取备份目录配置
        backup_dir = self.config_manager.get_config("backup_dir")
        if backup_dir and os.path.exists(os.path.dirname(backup_dir)):
            self.backup_dir = backup_dir
            # 不在初始化时创建目录，只在需要时创建