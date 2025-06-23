#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
服务器启动参数选项卡模块
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QFrame, QLineEdit, QSpinBox, QComboBox,
    QCheckBox, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from ..common.constants import DEFAULT_SERVER_CONFIG, GAME_MODE_OPTIONS


class ServerParamsTab(QWidget):
    """服务器启动参数选项卡"""
    
    # 定义信号
    config_saved = Signal(dict)
    
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 创建内容widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 基本配置
        basic_group = QGroupBox("基本配置")
        basic_layout = QVBoxLayout(basic_group)
        basic_layout.setContentsMargins(10, 15, 10, 10)
        basic_layout.setSpacing(8)
        
        # 服务器名称
        server_name_frame = QFrame()
        server_name_layout = QHBoxLayout(server_name_frame)
        server_name_layout.setContentsMargins(5, 5, 5, 5)
        
        server_name_label = QLabel("服务器名称:")
        server_name_label.setMinimumWidth(120)
        self.server_name_edit = QLineEdit()
        self.server_name_edit.setPlaceholderText("请输入服务器名称")
        
        server_name_layout.addWidget(server_name_label)
        server_name_layout.addWidget(self.server_name_edit)
        basic_layout.addWidget(server_name_frame)
        
        # 最大玩家数
        max_players_frame = QFrame()
        max_players_layout = QHBoxLayout(max_players_frame)
        max_players_layout.setContentsMargins(5, 5, 5, 5)
        
        max_players_label = QLabel("最大玩家数:")
        max_players_label.setMinimumWidth(120)
        self.max_players_spin = QSpinBox()
        self.max_players_spin.setRange(1, 100)
        self.max_players_spin.setValue(20)
        
        max_players_layout.addWidget(max_players_label)
        max_players_layout.addWidget(self.max_players_spin)
        max_players_layout.addStretch()
        basic_layout.addWidget(max_players_frame)
        
        # 端口
        port_frame = QFrame()
        port_layout = QHBoxLayout(port_frame)
        port_layout.setContentsMargins(5, 5, 5, 5)
        
        port_label = QLabel("端口:")
        port_label.setMinimumWidth(120)
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(7777)
        
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_spin)
        port_layout.addStretch()
        basic_layout.addWidget(port_frame)
        
        # 监听地址
        multihome_frame = QFrame()
        multihome_layout = QHBoxLayout(multihome_frame)
        multihome_layout.setContentsMargins(5, 5, 5, 5)
        
        multihome_label = QLabel("监听地址:")
        multihome_label.setMinimumWidth(120)
        self.multihome_edit = QLineEdit()
        self.multihome_edit.setText("0.0.0.0")
        self.multihome_edit.setPlaceholderText("服务器监听的IP地址，0.0.0.0表示监听所有网卡")
        
        multihome_layout.addWidget(multihome_label)
        multihome_layout.addWidget(self.multihome_edit)
        basic_layout.addWidget(multihome_frame)
        
        layout.addWidget(basic_group)
        
        # 游戏设置
        game_group = QGroupBox("游戏设置")
        game_layout = QVBoxLayout(game_group)
        game_layout.setContentsMargins(10, 15, 10, 10)
        game_layout.setSpacing(8)
        
        # 游戏模式
        game_mode_frame = QFrame()
        game_mode_layout = QHBoxLayout(game_mode_frame)
        game_mode_layout.setContentsMargins(5, 5, 5, 5)
        
        game_mode_label = QLabel("游戏模式:")
        game_mode_label.setMinimumWidth(120)
        self.game_mode_combo = QComboBox()
        self.game_mode_combo.addItems(["PvE", "PvP"])
        
        game_mode_layout.addWidget(game_mode_label)
        game_mode_layout.addWidget(self.game_mode_combo)
        game_mode_layout.addStretch()
        game_layout.addWidget(game_mode_frame)
        
        layout.addWidget(game_group)
        
        # RCON设置
        rcon_group = QGroupBox("RCON设置")
        rcon_layout = QVBoxLayout(rcon_group)
        rcon_layout.setContentsMargins(10, 15, 10, 10)
        rcon_layout.setSpacing(8)
        
        # 启用RCON
        enable_rcon_frame = QFrame()
        enable_rcon_layout = QHBoxLayout(enable_rcon_frame)
        enable_rcon_layout.setContentsMargins(5, 5, 5, 5)
        
        self.rcon_enabled_checkbox = QCheckBox("启用RCON远程控制")
        self.rcon_enabled_checkbox.setChecked(True)
        self.rcon_enabled_checkbox.toggled.connect(self.toggle_rcon_settings)
        
        enable_rcon_layout.addWidget(self.rcon_enabled_checkbox)
        enable_rcon_layout.addStretch()
        rcon_layout.addWidget(enable_rcon_frame)
        
        # RCON地址
        rcon_addr_frame = QFrame()
        rcon_addr_layout = QHBoxLayout(rcon_addr_frame)
        rcon_addr_layout.setContentsMargins(5, 5, 5, 5)
        
        rcon_addr_label = QLabel("RCON地址:")
        rcon_addr_label.setMinimumWidth(120)
        self.rcon_addr_edit = QLineEdit()
        self.rcon_addr_edit.setText("127.0.0.1")
        
        rcon_addr_layout.addWidget(rcon_addr_label)
        rcon_addr_layout.addWidget(self.rcon_addr_edit)
        rcon_layout.addWidget(rcon_addr_frame)
        
        # RCON端口
        rcon_port_frame = QFrame()
        rcon_port_layout = QHBoxLayout(rcon_port_frame)
        rcon_port_layout.setContentsMargins(5, 5, 5, 5)
        
        rcon_port_label = QLabel("RCON端口:")
        rcon_port_label.setMinimumWidth(120)
        self.rcon_port_spin = QSpinBox()
        self.rcon_port_spin.setRange(1024, 65535)
        self.rcon_port_spin.setValue(25575)
        
        rcon_port_layout.addWidget(rcon_port_label)
        rcon_port_layout.addWidget(self.rcon_port_spin)
        rcon_port_layout.addStretch()
        rcon_layout.addWidget(rcon_port_frame)
        
        # RCON密码
        rcon_password_frame = QFrame()
        rcon_password_layout = QHBoxLayout(rcon_password_frame)
        rcon_password_layout.setContentsMargins(5, 5, 5, 5)
        
        rcon_password_label = QLabel("RCON密码:")
        rcon_password_label.setMinimumWidth(120)
        self.rcon_password_edit = QLineEdit()
        self.rcon_password_edit.setText("")
        self.rcon_password_edit.setPlaceholderText("请设置RCON密码，不设置将无法连接")
        self.rcon_password_edit.setEchoMode(QLineEdit.Password)
        
        rcon_password_layout.addWidget(rcon_password_label)
        rcon_password_layout.addWidget(self.rcon_password_edit)
        rcon_layout.addWidget(rcon_password_frame)
        
        layout.addWidget(rcon_group)
        
        # 额外启动参数
        extra_group = QGroupBox("额外启动参数")
        extra_layout = QVBoxLayout(extra_group)
        extra_layout.setContentsMargins(10, 10, 10, 10)
        extra_layout.setSpacing(6)
        
        # 参数输入框
        extra_args_frame = QFrame()
        extra_args_layout = QVBoxLayout(extra_args_frame)
        extra_args_layout.setContentsMargins(5, 3, 5, 5)
        
        extra_args_label = QLabel("额外参数:")
        self.extra_args_edit = QLineEdit()
        self.extra_value = "-PSW=\"服务器密码\" -adminpsw=\"管理员密码\" -pve -gamedistindex=4 -mod=\"3459140312,3400177243,3325592770,3412334480\""
        self.extra_args_edit.setPlaceholderText(self.extra_value)
        # 连接双击事件
        self.extra_args_edit.mouseDoubleClickEvent = self.on_extra_args_double_click
        # 设置样式
        self.extra_args_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 10pt;
            }
        """)
        
        extra_args_layout.addWidget(extra_args_label)
        extra_args_layout.addWidget(self.extra_args_edit)
        
        extra_layout.addWidget(extra_args_frame)
        layout.addWidget(extra_group)
        
        # 保存按钮
        save_button = QPushButton("保存配置")
        save_button.setObjectName("save_button")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)
        
        layout.addStretch()
        
        # 设置滚动区域
        scroll_area.setWidget(content_widget)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
    
    def toggle_rcon_settings(self, enabled):
        """切换RCON设置的启用状态"""
        self.rcon_addr_edit.setEnabled(enabled)
        self.rcon_port_spin.setEnabled(enabled)
        self.rcon_password_edit.setEnabled(enabled)
    
    def on_extra_args_double_click(self, event):
        """处理额外参数输入框的双击事件"""
        # 示例启动参数
        example_args = self.extra_value
        self.extra_args_edit.setText(example_args)
        # 选中所有文本，方便用户修改
        self.extra_args_edit.selectAll()
    
    def save_config(self):
        """保存配置"""
        config = {
            'server_name': self.server_name_edit.text(),
            'max_players': self.max_players_spin.value(),
            'port': self.port_spin.value(),
            'multihome': self.multihome_edit.text(),
            'game_mode': 'pve' if self.game_mode_combo.currentText() == 'PvE' else 'pvp',
            'rcon_enabled': self.rcon_enabled_checkbox.isChecked(),
            'rcon_addr': self.rcon_addr_edit.text(),
            'rcon_port': self.rcon_port_spin.value(),
            'rcon_password': self.rcon_password_edit.text(),
            'extra_args': self.extra_args_edit.text()
        }
        # 发出信号
        self.config_saved.emit(config)
    
    def load_config(self, config):
        """加载配置"""
        self.server_name_edit.setText(config.get('server_name', ''))
        self.max_players_spin.setValue(config.get('max_players', 20))
        self.port_spin.setValue(config.get('port', 7777))
        self.multihome_edit.setText(config.get('multihome', '0.0.0.0'))
        
        game_mode = config.get('game_mode', 'pve')
        self.game_mode_combo.setCurrentText('PvE' if game_mode == 'pve' else 'PvP')
        
        self.rcon_enabled_checkbox.setChecked(config.get('rcon_enabled', True))
        self.rcon_addr_edit.setText(config.get('rcon_addr', '127.0.0.1'))
        self.rcon_port_spin.setValue(config.get('rcon_port', 25575))
        self.rcon_password_edit.setText(config.get('rcon_password', ''))
        self.extra_args_edit.setText(config.get('extra_args', ''))
        
        # 更新RCON设置状态
        self.toggle_rcon_settings(self.rcon_enabled_checkbox.isChecked())