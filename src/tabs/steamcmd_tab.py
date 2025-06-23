#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SteamCMD选项卡模块
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QFrame, QTextEdit, QProgressBar
)


class SteamCMDTab(QWidget):
    """SteamCMD选项卡"""
    
    def __init__(self, parent=None, main_window=None, steamcmd_manager=None):
        super().__init__(parent)
        self.main_window = main_window
        self.steamcmd_manager = steamcmd_manager
        self.setup_ui()
        
        # 连接SteamCMD管理器信号
        if self.steamcmd_manager:
            self._connect_steamcmd_signals()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # SteamCMD管理
        steamcmd_group = QGroupBox("SteamCMD管理")
        steamcmd_layout = QVBoxLayout(steamcmd_group)
        steamcmd_layout.setContentsMargins(10, 15, 10, 10)
        steamcmd_layout.setSpacing(8)
        
        # 状态信息
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(5, 5, 5, 5)
        
        status_layout.addWidget(QLabel("SteamCMD状态:"))
        self.steamcmd_status_label = QLabel("未安装")
        self.steamcmd_status_label.setObjectName("status_offline")
        status_layout.addWidget(self.steamcmd_status_label)
        status_layout.addStretch()
        
        steamcmd_layout.addWidget(status_frame)
        
        # 操作按钮
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(5, 5, 5, 5)
        buttons_layout.setSpacing(8)
        
        self.install_steamcmd_btn = QPushButton("安装SteamCMD")
        self.install_steamcmd_btn.clicked.connect(self.install_steamcmd)
        buttons_layout.addWidget(self.install_steamcmd_btn)
        
        self.check_steamcmd_btn = QPushButton("检查SteamCMD")
        self.check_steamcmd_btn.clicked.connect(self.check_steamcmd)
        buttons_layout.addWidget(self.check_steamcmd_btn)
        
        buttons_layout.addStretch()
        steamcmd_layout.addWidget(buttons_frame)
        
        layout.addWidget(steamcmd_group)
        
        # 服务端管理
        server_group = QGroupBox("服务端管理")
        server_layout = QVBoxLayout(server_group)
        server_layout.setContentsMargins(10, 15, 10, 10)
        server_layout.setSpacing(8)
        
        # 服务端状态
        server_status_frame = QFrame()
        server_status_layout = QHBoxLayout(server_status_frame)
        server_status_layout.setContentsMargins(5, 5, 5, 5)
        
        server_status_layout.addWidget(QLabel("服务端状态:"))
        self.server_status_label = QLabel("未安装")
        self.server_status_label.setObjectName("status_offline")
        server_status_layout.addWidget(self.server_status_label)
        server_status_layout.addStretch()
        
        server_layout.addWidget(server_status_frame)
        
        # 服务端操作按钮
        server_buttons_frame = QFrame()
        server_buttons_layout = QHBoxLayout(server_buttons_frame)
        server_buttons_layout.setContentsMargins(5, 5, 5, 5)
        server_buttons_layout.setSpacing(8)
        
        self.install_server_btn = QPushButton("安装/更新服务端")
        self.install_server_btn.clicked.connect(self.install_server)
        self.install_server_btn.setEnabled(False)
        server_buttons_layout.addWidget(self.install_server_btn)
        
        self.validate_server_btn = QPushButton("验证服务端文件")
        self.validate_server_btn.clicked.connect(self.validate_server)
        self.validate_server_btn.setEnabled(False)
        server_buttons_layout.addWidget(self.validate_server_btn)
        
        self.check_server_btn = QPushButton("检查服务端")
        self.check_server_btn.clicked.connect(self.check_server)
        server_buttons_layout.addWidget(self.check_server_btn)
        
        server_buttons_layout.addStretch()
        server_layout.addWidget(server_buttons_frame)
        
        layout.addWidget(server_group)
        
        # 进度条
        progress_group = QGroupBox("操作进度")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setContentsMargins(10, 15, 10, 10)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
        
        # 操作日志
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(10, 15, 10, 10)
        
        self.operation_log = QTextEdit()
        self.operation_log.setReadOnly(True)
        self.operation_log.setMaximumHeight(200)
        log_layout.addWidget(self.operation_log)
        
        # 日志控制按钮
        log_buttons_layout = QHBoxLayout()
        clear_log_btn = QPushButton("清除日志")
        clear_log_btn.clicked.connect(self.clear_operation_log)
        log_buttons_layout.addWidget(clear_log_btn)
        log_buttons_layout.addStretch()
        log_layout.addLayout(log_buttons_layout)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
    
    def _connect_steamcmd_signals(self):
        """连接SteamCMD管理器信号"""
        self.steamcmd_manager.download_progress.connect(self.update_download_progress)
        self.steamcmd_manager.download_finished.connect(self.on_download_finished)
        self.steamcmd_manager.installation_progress.connect(self.update_installation_progress)
        self.steamcmd_manager.installation_finished.connect(self.on_installation_finished)
        self.steamcmd_manager.log_message.connect(self.add_operation_log)
    
    def install_steamcmd(self):
        """安装SteamCMD"""
        if self.steamcmd_manager:
            try:
                self.steamcmd_manager.install_steamcmd()
                self.add_operation_log("开始下载SteamCMD...")
            except Exception as e:
                self.add_operation_log(f"安装SteamCMD失败: {e}")
    
    def check_steamcmd(self):
        """检查SteamCMD"""
        if self.steamcmd_manager:
            try:
                steamcmd_path = self.steamcmd_manager.steamcmd_exe
                self.add_operation_log(f"正在检查SteamCMD状态...")
                self.add_operation_log(f"检查路径: {steamcmd_path}")
                status = self.steamcmd_manager.check_steamcmd_installed()
                status_text = "已安装" if status else "未安装"
                self.update_steamcmd_status(status_text)
                self.add_operation_log(f"SteamCMD状态: {status_text}")
            except Exception as e:
                self.add_operation_log(f"检查SteamCMD状态失败: {e}")
    
    def install_server(self):
        """安装/更新服务端"""
        if self.steamcmd_manager:
            try:
                self.steamcmd_manager.install_game()
                self.add_operation_log("开始安装/更新游戏服务端...")
            except Exception as e:
                self.add_operation_log(f"安装游戏服务端失败: {e}")
    
    def validate_server(self):
        """验证服务端文件"""
        if self.steamcmd_manager:
            try:
                self.steamcmd_manager.validate_game()
                self.add_operation_log("开始验证游戏文件...")
            except Exception as e:
                self.add_operation_log(f"验证游戏文件失败: {e}")
    
    def check_server(self):
        """检查服务端"""
        if self.steamcmd_manager:
            try:
                server_path = self.steamcmd_manager.get_server_path()
                import os
                server_exe = os.path.join(server_path, "StartServer.bat")
                self.add_operation_log("正在检查服务端状态...")
                self.add_operation_log(f"检查路径: {server_exe}")
                status = self.steamcmd_manager.check_game_installed()
                status_text = "已安装" if status else "未安装"
                self.update_server_status(status_text)
                self.add_operation_log(f"服务端状态: {status_text}")
            except Exception as e:
                self.add_operation_log(f"检查游戏状态失败: {e}")
    
    def clear_operation_log(self):
        """清除操作日志"""
        self.operation_log.clear()
    
    def update_steamcmd_status(self, status):
        """更新SteamCMD状态"""
        self.steamcmd_status_label.setText(status)
        if status == "已安装":
            self.steamcmd_status_label.setObjectName("status_online")
            self.install_steamcmd_btn.setText("重新安装SteamCMD")
            self.install_server_btn.setEnabled(True)
            self.validate_server_btn.setEnabled(True)
        else:
            self.steamcmd_status_label.setObjectName("status_offline")
            self.install_steamcmd_btn.setText("安装SteamCMD")
            self.install_server_btn.setEnabled(False)
            self.validate_server_btn.setEnabled(False)
        
        # 重新应用样式
        self.steamcmd_status_label.style().unpolish(self.steamcmd_status_label)
        self.steamcmd_status_label.style().polish(self.steamcmd_status_label)
    
    def update_server_status(self, status):
        """更新服务端状态"""
        self.server_status_label.setText(status)
        if status == "已安装":
            self.server_status_label.setObjectName("status_online")
        else:
            self.server_status_label.setObjectName("status_offline")
        
        # 重新应用样式
        self.server_status_label.style().unpolish(self.server_status_label)
        self.server_status_label.style().polish(self.server_status_label)
    
    def update_download_progress(self, progress):
        """更新下载进度"""
        self.add_operation_log(f"下载进度: {progress}%")
    
    def on_download_finished(self, success, message):
        """下载完成处理"""
        self.add_operation_log(message)
        if success:
            self.check_steamcmd()  # 重新检查状态
    
    def update_installation_progress(self, message):
        """更新安装进度"""
        self.add_operation_log(message)
    
    def on_installation_finished(self, success, message):
        """安装完成处理"""
        self.add_operation_log(message)
        if success:
            self.check_server()  # 重新检查服务端状态
    
    def update_server_status(self, status):
        """更新服务端状态"""
        self.server_status_label.setText(status)
        if status == "已安装":
            self.server_status_label.setObjectName("status_online")
        else:
            self.server_status_label.setObjectName("status_offline")
        
        # 重新应用样式
        self.server_status_label.style().unpolish(self.server_status_label)
        self.server_status_label.style().polish(self.server_status_label)
    
    def show_progress(self, show=True):
        """显示/隐藏进度条"""
        self.progress_bar.setVisible(show)
        self.progress_label.setVisible(show)
        if not show:
            self.progress_bar.setValue(0)
            self.progress_label.setText("")
    
    def update_progress(self, value, text=""):
        """更新进度"""
        self.progress_bar.setValue(value)
        if text:
            self.progress_label.setText(text)
    
    def add_operation_log(self, message):
        """添加操作日志"""
        self.operation_log.append(message)
        # 自动滚动到底部
        cursor = self.operation_log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.operation_log.setTextCursor(cursor)