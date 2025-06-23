# -*- coding: utf-8 -*-

"""
备份选项卡模块 - 备份版本
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
        
        keep_layout.addWidget(keep_label)
        keep_layout.addWidget(self.keep_backups_spin)
        keep_layout.addStretch()
        
        auto_backup_layout.addWidget(keep_frame)
        
        # 保存设置按钮
        save_settings_btn = QPushButton("保存设置")
        save_settings_btn.clicked.connect(self.save_backup_settings)
        auto_backup_layout.addWidget(save_settings_btn)
        
        layout.addWidget(auto_backup_group)
        
        # 手动备份
        manual_backup_group = QGroupBox("手动备份")
        manual_backup_layout = QVBoxLayout(manual_backup_group)
        manual_backup_layout.setContentsMargins(10, 15, 10, 10)
        manual_backup_layout.setSpacing(8)
        
        # 备份状态
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(5, 5, 5, 5)
        
        status_layout.addWidget(QLabel("备份状态:"))
        self.backup_status_label = QLabel("就绪")
        self.backup_status_label.setObjectName("status_offline")
        status_layout.addWidget(self.backup_status_label)
        status_layout.addStretch()
        
        manual_backup_layout.addWidget(status_frame)
        
        # 手动备份按钮
        manual_buttons_frame = QFrame()
        manual_buttons_layout = QHBoxLayout(manual_buttons_frame)
        manual_buttons_layout.setContentsMargins(5, 5, 5, 5)
        manual_buttons_layout.setSpacing(8)
        
        self.create_backup_btn = QPushButton("创建备份")
        self.create_backup_btn.clicked.connect(self.create_backup)
        manual_buttons_layout.addWidget(self.create_backup_btn)
        
        self.refresh_backups_btn = QPushButton("刷新列表")
        self.refresh_backups_btn.clicked.connect(self.refresh_backup_list)
        manual_buttons_layout.addWidget(self.refresh_backups_btn)
        
        manual_buttons_layout.addStretch()
        manual_backup_layout.addWidget(manual_buttons_frame)
        
        layout.addWidget(manual_backup_group)
        
        # 备份列表
        backup_list_group = QGroupBox("备份列表")
        backup_list_layout = QVBoxLayout(backup_list_group)
        backup_list_layout.setContentsMargins(10, 15, 10, 10)
        backup_list_layout.setSpacing(8)
        
        # 备份列表控件
        self.backup_list = QListWidget()
        self.backup_list.itemSelectionChanged.connect(self.on_backup_selected)
        backup_list_layout.addWidget(self.backup_list)
        
        # 备份操作按钮
        backup_ops_frame = QFrame()
        backup_ops_layout = QHBoxLayout(backup_ops_frame)
        backup_ops_layout.setContentsMargins(5, 5, 5, 5)
        backup_ops_layout.setSpacing(8)
        
        self.restore_backup_btn = QPushButton("恢复备份")
        self.restore_backup_btn.clicked.connect(self.restore_backup)
        self.restore_backup_btn.setEnabled(False)
        backup_ops_layout.addWidget(self.restore_backup_btn)
        
        self.delete_backup_btn = QPushButton("删除备份")
        self.delete_backup_btn.clicked.connect(self.delete_backup)
        self.delete_backup_btn.setEnabled(False)
        backup_ops_layout.addWidget(self.delete_backup_btn)
        
        backup_ops_layout.addStretch()
        backup_list_layout.addWidget(backup_ops_frame)
        
        layout.addWidget(backup_list_group)
        
        # 操作日志
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(10, 15, 10, 10)
        
        self.backup_log = QTextEdit()
        self.backup_log.setReadOnly(True)
        self.backup_log.setMaximumHeight(150)
        log_layout.addWidget(self.backup_log)
        
        # 日志控制按钮
        log_buttons_layout = QHBoxLayout()
        clear_log_btn = QPushButton("清除日志")
        clear_log_btn.clicked.connect(self.clear_backup_log)
        log_buttons_layout.addWidget(clear_log_btn)
        log_buttons_layout.addStretch()
        log_layout.addLayout(log_buttons_layout)
        
        layout.addWidget(log_group)
    
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
        if self.main_window:
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
        self.backup_status_label.setText(status)
        if status in ["备份中", "恢复中"]:
            self.backup_status_label.setObjectName("status_warning")
            self.create_backup_btn.setEnabled(False)
        elif status == "完成":
            self.backup_status_label.setObjectName("status_online")
            self.create_backup_btn.setEnabled(True)
        else:
            self.backup_status_label.setObjectName("status_offline")
            self.create_backup_btn.setEnabled(True)
        
        # 重新应用样式
        self.backup_status_label.style().unpolish(self.backup_status_label)
        self.backup_status_label.style().polish(self.backup_status_label)
    
    def update_backup_list(self, backups):
        """更新备份列表"""
        self.backup_list.clear()
        for backup in backups:
            item_text = f"{backup['name']} - {backup['date']} ({backup['size']})"
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