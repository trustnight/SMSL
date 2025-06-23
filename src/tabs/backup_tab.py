#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
备份选项卡模块
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QFrame, QListWidget, QListWidgetItem,
    QCheckBox, QSpinBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from ..common.constants import DEFAULT_BACKUP_INTERVAL, DEFAULT_KEEP_BACKUPS_COUNT


class BackupTab(QWidget):
    """备份选项卡"""
    
    # 定义信号
    backup_settings_saved = Signal(dict)
    
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 自动备份设置
        auto_backup_group = QGroupBox("自动备份设置")
        auto_backup_layout = QVBoxLayout(auto_backup_group)
        auto_backup_layout.setContentsMargins(10, 15, 10, 10)
        auto_backup_layout.setSpacing(8)
        
        # 启用自动备份
        enable_frame = QFrame()
        enable_layout = QHBoxLayout(enable_frame)
        enable_layout.setContentsMargins(5, 5, 5, 5)
        
        self.auto_backup_checkbox = QCheckBox("启用自动备份")
        self.auto_backup_checkbox.setChecked(True)
        self.auto_backup_checkbox.toggled.connect(self.toggle_auto_backup)
        enable_layout.addWidget(self.auto_backup_checkbox)
        enable_layout.addStretch()
        
        auto_backup_layout.addWidget(enable_frame)
        
        # 备份间隔
        interval_frame = QFrame()
        interval_layout = QHBoxLayout(interval_frame)
        interval_layout.setContentsMargins(5, 5, 5, 5)
        
        interval_label = QLabel("备份间隔:")
        interval_label.setMinimumWidth(120)
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(5, 1440)  # 5分钟到24小时
        self.backup_interval_spin.setValue(DEFAULT_BACKUP_INTERVAL)
        self.backup_interval_spin.setSuffix(" 分钟")
        self.backup_interval_spin.setMinimumWidth(120)
        self.backup_interval_spin.setMaximumWidth(120)
        
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.backup_interval_spin)
        interval_layout.addStretch()
        
        auto_backup_layout.addWidget(interval_frame)
        
        # 保留备份数量
        keep_frame = QFrame()
        keep_layout = QHBoxLayout(keep_frame)
        keep_layout.setContentsMargins(5, 5, 5, 5)
        
        keep_label = QLabel("保留备份数量:")
        keep_label.setMinimumWidth(120)
        self.keep_backups_spin = QSpinBox()
        self.keep_backups_spin.setRange(1, 100)
        self.keep_backups_spin.setValue(DEFAULT_KEEP_BACKUPS_COUNT)
        self.keep_backups_spin.setSuffix(" 个")
        self.keep_backups_spin.setMinimumWidth(120)
        self.keep_backups_spin.setMaximumWidth(120)
        
        keep_layout.addWidget(keep_label)
        keep_layout.addWidget(self.keep_backups_spin)
        keep_layout.addStretch()
        
        auto_backup_layout.addWidget(keep_frame)
        
        # 保存设置按钮
        save_settings_btn = QPushButton("保存设置")
        save_settings_btn.clicked.connect(self.save_backup_settings)
        auto_backup_layout.addWidget(save_settings_btn)
        
        layout.addWidget(auto_backup_group)
        
        # 创建水平布局容器，包含备份列表和操作日志
        horizontal_container = QHBoxLayout()
        horizontal_container.setSpacing(10)
        
        # 备份列表
        backup_list_group = QGroupBox("备份列表")
        backup_list_layout = QVBoxLayout(backup_list_group)
        backup_list_layout.setContentsMargins(10, 15, 10, 10)
        backup_list_layout.setSpacing(8)
        
        # 备份列表控件
        self.backup_list = QListWidget()
        self.backup_list.itemSelectionChanged.connect(self.on_backup_selected)
        backup_list_layout.addWidget(self.backup_list)
        
        # 备份列表操作按钮
        backup_list_buttons_frame = QFrame()
        backup_list_buttons_layout = QHBoxLayout(backup_list_buttons_frame)
        backup_list_buttons_layout.setContentsMargins(5, 5, 5, 5)
        backup_list_buttons_layout.setSpacing(8)
        
        self.refresh_backups_btn = QPushButton("刷新列表")
        self.refresh_backups_btn.clicked.connect(self.refresh_backup_list)
        backup_list_buttons_layout.addWidget(self.refresh_backups_btn)
        
        self.restore_backup_btn = QPushButton("恢复备份")
        self.restore_backup_btn.clicked.connect(self.restore_backup)
        self.restore_backup_btn.setEnabled(False)
        backup_list_buttons_layout.addWidget(self.restore_backup_btn)
        
        self.delete_backup_btn = QPushButton("删除备份")
        self.delete_backup_btn.clicked.connect(self.delete_backup)
        self.delete_backup_btn.setEnabled(False)
        backup_list_buttons_layout.addWidget(self.delete_backup_btn)
        
        backup_list_buttons_layout.addStretch()
        backup_list_layout.addWidget(backup_list_buttons_frame)
        
        horizontal_container.addWidget(backup_list_group)
        
        # 操作日志
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(10, 15, 10, 10)
        log_layout.setSpacing(8)
        
        # 操作日志文本框（添加明显边框）
        self.backup_log = QTextEdit()
        self.backup_log.setReadOnly(True)
        self.backup_log.setMinimumHeight(200)
        self.backup_log.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        self.backup_log.setLineWidth(2)  # 设置边框宽度
        self.backup_log.setStyleSheet("QTextEdit { border: 2px solid #cccccc; border-radius: 4px; }")
        
        log_layout.addWidget(self.backup_log)
        
        # 操作日志按钮
        log_buttons_frame = QFrame()
        log_buttons_layout = QHBoxLayout(log_buttons_frame)
        log_buttons_layout.setContentsMargins(5, 5, 5, 5)
        log_buttons_layout.setSpacing(8)
        
        self.create_backup_btn = QPushButton("创建备份")
        self.create_backup_btn.clicked.connect(self.create_backup)
        log_buttons_layout.addWidget(self.create_backup_btn)
        
        clear_log_btn = QPushButton("清除日志")
        clear_log_btn.clicked.connect(self.clear_backup_log)
        log_buttons_layout.addWidget(clear_log_btn)
        
        log_buttons_layout.addStretch()
        log_layout.addWidget(log_buttons_frame)
        
        horizontal_container.addWidget(log_group)
        
        # 将水平布局添加到主布局
        layout.addLayout(horizontal_container)
        
        # 初始化时刷新备份列表
        self.refresh_backup_list()
    
    def toggle_auto_backup(self, enabled):
        """切换自动备份设置"""
        self.backup_interval_spin.setEnabled(enabled)
        self.keep_backups_spin.setEnabled(enabled)
    
    def save_backup_settings(self):
        """保存备份设置"""
        settings = {
            'auto_backup': self.auto_backup_checkbox.isChecked(),
            'backup_interval': self.backup_interval_spin.value(),
            'keep_backups_count': self.keep_backups_spin.value()
        }
        # 发出信号
        self.backup_settings_saved.emit(settings)
    
    def create_backup(self):
        """创建备份"""
        if self.main_window:
            self.main_window.create_backup()
    
    def refresh_backup_list(self):
        """刷新备份列表"""
        if self.main_window and hasattr(self.main_window, 'backup_tab'):
            self.main_window.refresh_backup_list()
    
    def restore_backup(self):
        """恢复备份"""
        current_item = self.backup_list.currentItem()
        if current_item and self.main_window:
            backup_name = current_item.text().split(' - ')[0]
            self.main_window.restore_backup(backup_name)
    
    def delete_backup(self):
        """删除备份"""
        current_item = self.backup_list.currentItem()
        if current_item and self.main_window:
            backup_name = current_item.text().split(' - ')[0]
            self.main_window.delete_backup(backup_name)
    
    def on_backup_selected(self):
        """备份选择改变"""
        has_selection = bool(self.backup_list.currentItem())
        self.restore_backup_btn.setEnabled(has_selection)
        self.delete_backup_btn.setEnabled(has_selection)
    
    def clear_backup_log(self):
        """清除备份日志"""
        self.backup_log.clear()
    
    def update_backup_status(self, status):
        """更新备份状态"""
        # 根据状态启用/禁用创建备份按钮
        if status in ["备份中", "恢复中"]:
            self.create_backup_btn.setEnabled(False)
        else:
            self.create_backup_btn.setEnabled(True)
    
    def update_backup_list(self, backups):
        """更新备份列表"""
        self.backup_list.clear()
        for backup in backups:
            # 格式化文件大小
            size_mb = backup['size'] / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB"
            # 格式化创建时间
            date_str = backup['created'].strftime("%Y-%m-%d %H:%M:%S")
            item_text = f"{backup['name']} - {date_str} ({size_str})"
            item = QListWidgetItem(item_text)
            self.backup_list.addItem(item)
    
    def add_backup_log(self, message):
        """添加备份日志"""
        self.backup_log.append(message)
        # 自动滚动到底部
        cursor = self.backup_log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.backup_log.setTextCursor(cursor)
    
    def load_backup_settings(self, settings):
        """加载备份设置"""
        self.auto_backup_checkbox.setChecked(settings.get('auto_backup', True))
        self.backup_interval_spin.setValue(settings.get('backup_interval', DEFAULT_BACKUP_INTERVAL))
        self.keep_backups_spin.setValue(settings.get('keep_backups_count', DEFAULT_KEEP_BACKUPS_COUNT))
        
        # 更新控件状态
        self.toggle_auto_backup(self.auto_backup_checkbox.isChecked())