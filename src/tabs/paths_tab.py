#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
灵魂面甲服务器启动器 - 路径设置选项卡
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QLineEdit, QPushButton, QFileDialog, QMessageBox
)
from ..common.constants import UI_LABELS, UI_DIALOG_TITLES, UI_BUTTON_TEXTS


class PathsTab(QWidget):
    """路径设置选项卡"""
    
    def __init__(self, parent=None, main_window=None, paths_manager=None):
        super().__init__(parent)
        self.main_window = main_window
        self.paths_manager = paths_manager
        self.has_unsaved_changes = False  # 跟踪是否有未保存的更改
        self.original_steamcmd_dir = ""  # 保存原始SteamCMD路径值
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 说明标签
        info_label = QLabel("设置SteamCMD路径，其他路径将跟随exe执行路径自动生成")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # SteamCMD路径设置组
        steamcmd_group = QGroupBox("SteamCMD路径设置")
        steamcmd_layout = QVBoxLayout(steamcmd_group)
        
        # SteamCMD路径
        steamcmd_dir_layout = QHBoxLayout()
        self.steamcmd_dir_label = QLabel("SteamCMD路径:")
        steamcmd_dir_layout.addWidget(self.steamcmd_dir_label)
        self.steamcmd_dir_edit = QLineEdit()
        self.steamcmd_dir_edit.textChanged.connect(self.on_steamcmd_dir_changed)
        steamcmd_dir_layout.addWidget(self.steamcmd_dir_edit)
        steamcmd_dir_btn = QPushButton(UI_BUTTON_TEXTS['browse'])
        steamcmd_dir_btn.clicked.connect(self.browse_steamcmd_dir)
        steamcmd_dir_layout.addWidget(steamcmd_dir_btn)
        steamcmd_layout.addLayout(steamcmd_dir_layout)
        
        layout.addWidget(steamcmd_group)
        
        # 按钮组
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton(UI_BUTTON_TEXTS['save_settings'])
        self.save_btn.clicked.connect(self.save_steamcmd_path)
        buttons_layout.addWidget(self.save_btn)
        
        reset_btn = QPushButton(UI_BUTTON_TEXTS['reset_default'])
        reset_btn.clicked.connect(self.reset_steamcmd_path)
        buttons_layout.addWidget(reset_btn)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        # 初始化显示
        self.update_unsaved_changes_indicator()
    
    def browse_steamcmd_dir(self):
        """浏览SteamCMD目录"""
        path = QFileDialog.getExistingDirectory(self, "选择SteamCMD目录")
        if path:
            self.steamcmd_dir_edit.setText(path)
    
    def on_steamcmd_dir_changed(self):
        """SteamCMD目录改变时检查未保存更改"""
        self.check_for_unsaved_changes()
    
    def check_for_unsaved_changes(self):
        """检查是否有未保存的更改"""
        current_steamcmd_dir = self.steamcmd_dir_edit.text().strip()
        self.has_unsaved_changes = (current_steamcmd_dir != self.original_steamcmd_dir)
        self.update_unsaved_changes_indicator()
    
    def update_unsaved_changes_indicator(self):
        """更新未保存更改的视觉指示器"""
        if self.has_unsaved_changes:
            # 显示未保存更改的指示
            self.steamcmd_dir_label.setText("SteamCMD路径: *")
            self.steamcmd_dir_label.setStyleSheet("color: #ff6b35; font-weight: bold;")
            self.save_btn.setText("保存设置 *")
            self.save_btn.setStyleSheet("QPushButton { background-color: #ff6b35; color: white; font-weight: bold; }")
        else:
            # 恢复正常显示
            self.steamcmd_dir_label.setText("SteamCMD路径:")
            self.steamcmd_dir_label.setStyleSheet("")
            self.save_btn.setText("保存设置")
            self.save_btn.setStyleSheet("")
    
    def mark_as_saved(self):
        """标记为已保存状态"""
        self.original_steamcmd_dir = self.steamcmd_dir_edit.text().strip()
        self.has_unsaved_changes = False
        self.update_unsaved_changes_indicator()
    
    def save_steamcmd_path(self):
        """保存SteamCMD路径设置"""
        if not self.main_window:
            return
            
        steamcmd_dir = self.steamcmd_dir_edit.text().strip()
        if not steamcmd_dir:
            QMessageBox.warning(self, "警告", "请设置SteamCMD路径")
            return
            
        # 更新SteamCMD管理器的路径
        if hasattr(self.main_window, 'steamcmd_manager'):
            self.main_window.steamcmd_manager.set_steamcmd_dir(steamcmd_dir)
            # 游戏安装路径使用SteamCMD默认目录
            import os
            server_path = os.path.join(steamcmd_dir, "steamapps", "common", "Soulmask Dedicated Server For Windows")
            # 标准化路径格式，统一使用反斜杠
            server_path = os.path.normpath(server_path)
            self.main_window.steamcmd_manager.set_server_path(server_path)
        
        # 保存配置
        self.main_window.save_config()
        
        # 标记为已保存状态
        self.mark_as_saved()
        
        # 在状态栏显示保存成功信息
        if hasattr(self.main_window, 'status_label'):
            self.main_window.status_label.setText("SteamCMD路径设置已保存")
            # 3秒后恢复默认状态
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self.main_window.status_label.setText("就绪"))
    
    def reset_steamcmd_path(self):
        """重置SteamCMD路径为默认值"""
        reply = QMessageBox.question(
            self, "确认", 
            "确定要重置SteamCMD路径为默认值吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 重置为默认SteamCMD路径
            from ..common.constants import DEFAULT_PATHS
            self.steamcmd_dir_edit.setText(DEFAULT_PATHS.steamcmd_dir)
            
            # 保存配置
            if self.main_window:
                self.main_window.save_config()
            
            # 标记为已保存状态
            self.mark_as_saved()
            
            QMessageBox.information(self, "成功", "SteamCMD路径已重置为默认值")
    
    def update_from_config(self, config):
        """从配置更新UI"""
        # 获取SteamCMD路径
        steamcmd_dir = config.get('steamcmd_dir', '')
        if not steamcmd_dir:
            # 使用默认SteamCMD路径
            from ..common.constants import DEFAULT_PATHS
            steamcmd_dir = DEFAULT_PATHS.steamcmd_dir
        
        self.steamcmd_dir_edit.setText(steamcmd_dir)
        self.original_steamcmd_dir = steamcmd_dir  # 设置原始值
        self.mark_as_saved()  # 标记为已保存状态