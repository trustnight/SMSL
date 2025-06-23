#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
启动选项卡模块
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QFrame, QTextEdit, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from ..common.constants import UI_BUTTON_TEXTS


class LaunchTab(QWidget):
    """启动选项卡"""
    
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 服务器控制按钮
        control_group = QGroupBox("服务器控制")
        control_layout = QHBoxLayout(control_group)  # 改为水平布局
        control_layout.setContentsMargins(10, 15, 10, 10)
        control_layout.setSpacing(15)
        
        # 左侧：控制按钮面板
        buttons_frame = QFrame()
        buttons_layout = QVBoxLayout(buttons_frame)  # 按钮垂直排列
        buttons_layout.setSpacing(8)
        buttons_layout.setContentsMargins(8, 8, 8, 8)
        
        # 启动服务器按钮
        self.start_button = QPushButton("  启动服务器  ")
        self.start_button.setObjectName("start_button")
        self.start_button.clicked.connect(self.start_server)
        buttons_layout.addWidget(self.start_button)
        
        # 停止服务器按钮
        self.stop_button = QPushButton("  停止服务器  ")
        self.stop_button.setObjectName("stop_button")
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setEnabled(False)
        buttons_layout.addWidget(self.stop_button)
        
        # 重启服务器按钮
        self.restart_button = QPushButton("  重启服务器  ")
        self.restart_button.setObjectName("restart_button")
        self.restart_button.clicked.connect(self.restart_server)
        self.restart_button.setEnabled(False)
        buttons_layout.addWidget(self.restart_button)
        
        # 重新加载按钮
        # self.reload_button = QPushButton("  重新加载  ")
        # self.reload_button.setObjectName("reload_button")
        # self.reload_button.clicked.connect(self.reload_server_status)
        # self.reload_button.setToolTip("重新检测服务器进程状态")
        # buttons_layout.addWidget(self.reload_button)
        
        # GUI流式输出开关
        self.gui_streaming_checkbox = QCheckBox("GUI显示服务器日志")
        self.gui_streaming_checkbox.setToolTip("开启后在GUI中实时显示服务器日志，关闭后仅保存到文件")
        self.gui_streaming_checkbox.setChecked(False)  # 默认关闭
        self.gui_streaming_checkbox.stateChanged.connect(self.on_gui_streaming_changed)
        buttons_layout.addWidget(self.gui_streaming_checkbox)
        

        
        # RCON自动连接开关
        self.auto_rcon_checkbox = QCheckBox("服务器启动后自动连接RCON")
        self.auto_rcon_checkbox.setToolTip("开启后，服务器完全启动时将自动连接RCON")
        self.auto_rcon_checkbox.setChecked(False)  # 默认关闭
        self.auto_rcon_checkbox.stateChanged.connect(self.on_auto_rcon_changed)
        buttons_layout.addWidget(self.auto_rcon_checkbox)
        
        buttons_layout.addStretch()
        
        # 设置按钮面板的固定宽度
        buttons_frame.setMinimumWidth(200)
        buttons_frame.setMaximumWidth(250)
        control_layout.addWidget(buttons_frame, 0)  # 权重0，固定大小
        
        # 右侧：Mod加载状态显示
        mod_panel = QFrame()
        mod_panel_layout = QVBoxLayout(mod_panel)
        mod_panel_layout.setContentsMargins(8, 8, 8, 8)
        mod_panel_layout.setSpacing(8)
        
        mod_title = QLabel("Mod加载状态:")
        mod_title.setStyleSheet("font-weight: bold; color: #333; font-size: 11pt;")
        mod_panel_layout.addWidget(mod_title)
        
        # Mod状态显示容器（水平布局）
        self.mod_status_container = QFrame()
        self.mod_status_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #fff3e0, stop:1 #ffe0b2);
                border: 2px solid #ff9800;
                border-radius: 8px;
                padding: 6px;
                margin: 2px;
                min-height: 40px;
            }
        """)
        self.mod_status_layout = QHBoxLayout(self.mod_status_container)
        self.mod_status_layout.setContentsMargins(8, 4, 8, 4)
        self.mod_status_layout.setSpacing(8)
        self.mod_status_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # 左对齐
        
        # 初始状态标签
        self.mod_status_label = QLabel("等待服务器启动...")
        self.mod_status_label.setStyleSheet("font-weight: bold; color: #e65100; background: transparent; border: none; font-size: 10pt;")
        self.mod_status_layout.addWidget(self.mod_status_label)
        
        mod_panel_layout.addWidget(self.mod_status_container)
        mod_panel_layout.addStretch()
        
        # 将mod面板添加到主控制布局，设置更大的权重
        mod_panel.setMinimumWidth(400)
        control_layout.addWidget(mod_panel, 1)  # 权重1，占据剩余空间
        layout.addWidget(control_group)
        
        # 服务器状态信息
        status_group = QGroupBox("服务器状态")
        status_layout = QVBoxLayout(status_group)
        status_layout.setContentsMargins(10, 15, 10, 10)
        
        # 状态信息面板
        status_frame = QFrame()
        status_info_layout = QHBoxLayout(status_frame)
        status_info_layout.setContentsMargins(8, 8, 8, 8)
        status_info_layout.setSpacing(15)
        
        # 在线状态
        status_container = QFrame()
        status_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                border: 2px solid #2196f3;
                border-radius: 8px;
                padding: 8px;
                margin: 2px;
            }
        """)
        status_container_layout = QHBoxLayout(status_container)
        status_container_layout.setContentsMargins(8, 6, 8, 6)
        
        status_title = QLabel("状态:")
        status_title.setStyleSheet("font-weight: bold; color: #1976d2; background: transparent; border: none;")
        self.status_label = QLabel("离线")
        self.status_label.setObjectName("status_offline")
        self.status_label.setStyleSheet("font-weight: bold; background: transparent; border: none;")
        
        status_container_layout.addWidget(status_title)
        status_container_layout.addWidget(self.status_label)
        status_container_layout.addStretch()
        status_info_layout.addWidget(status_container)
        
        # 运行时间
        uptime_container = QFrame()
        uptime_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #f3e5f5, stop:1 #e1bee7);
                border: 2px solid #9c27b0;
                border-radius: 8px;
                padding: 8px;
                margin: 2px;
            }
        """)
        uptime_container_layout = QHBoxLayout(uptime_container)
        uptime_container_layout.setContentsMargins(8, 6, 8, 6)
        
        uptime_title = QLabel("运行时间:")
        uptime_title.setStyleSheet("font-weight: bold; color: #7b1fa2; background: transparent; border: none;")
        self.uptime_label = QLabel("--:--:--")
        self.uptime_label.setStyleSheet("font-weight: bold; background: transparent; border: none;")
        
        uptime_container_layout.addWidget(uptime_title)
        uptime_container_layout.addWidget(self.uptime_label)
        uptime_container_layout.addStretch()
        status_info_layout.addWidget(uptime_container)
        
        # 内存使用
        memory_container = QFrame()
        memory_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #e8f5e8, stop:1 #c8e6c9);
                border: 2px solid #4caf50;
                border-radius: 8px;
                padding: 8px;
                margin: 2px;
            }
        """)
        memory_container_layout = QHBoxLayout(memory_container)
        memory_container_layout.setContentsMargins(8, 6, 8, 6)
        
        memory_title = QLabel("内存:")
        memory_title.setStyleSheet("font-weight: bold; color: #388e3c; background: transparent; border: none;")
        self.memory_label = QLabel("-- MB")
        self.memory_label.setStyleSheet("font-weight: bold; background: transparent; border: none;")
        
        memory_container_layout.addWidget(memory_title)
        memory_container_layout.addWidget(self.memory_label)
        memory_container_layout.addStretch()
        status_info_layout.addWidget(memory_container)
        
        status_layout.addWidget(status_frame)
        layout.addWidget(status_group)
        
        # 服务器日志区（移除在线玩家区域，让日志区占据全部空间）
        log_group = QGroupBox("服务器日志")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(10, 15, 10, 10)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                font-size: 12pt;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        # 日志控制按钮
        log_buttons_layout = QHBoxLayout()
        clear_log_btn = QPushButton("清除日志")
        clear_log_btn.clicked.connect(self.clear_logs)
        log_buttons_layout.addWidget(clear_log_btn)
        log_buttons_layout.addStretch()
        log_layout.addLayout(log_buttons_layout)
        
        layout.addWidget(log_group)
        
        # 在线玩家列表（保留代码但不显示）
        self.players_group = QGroupBox("在线玩家")
        players_layout = QVBoxLayout(self.players_group)
        players_layout.setContentsMargins(10, 15, 10, 10)
        
        # 在线玩家彩色文本显示区域
        self.players_display = QTextEdit()
        self.players_display.setReadOnly(True)
        self.players_display.setMaximumHeight(200)
        self.players_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                font-size: 12pt;
            }
        """)
        players_layout.addWidget(self.players_display)
        
        # 玩家管理按钮
        player_buttons_layout = QHBoxLayout()
        refresh_players_btn = QPushButton("在线玩家")
        refresh_players_btn.clicked.connect(self.refresh_players)
        player_buttons_layout.addWidget(refresh_players_btn)
        player_buttons_layout.addStretch()
        players_layout.addLayout(player_buttons_layout)
        
        # 不添加到主布局中，保留代码但隐藏
        self.players_group.hide()
    
    def start_server(self):
        """启动服务器"""
        if self.main_window:
            self.main_window.start_server()
    
    def stop_server(self):
        """停止服务器"""
        if self.main_window:
            self.main_window.stop_server()
    
    def restart_server(self):
        """重启服务器"""
        if self.main_window:
            self.main_window.restart_server()
    
    def reload_server_status(self):
        """重新加载服务器状态"""
        if self.main_window:
            self.main_window.reload_server_status()
    
    def connect_signals(self):
        """连接信号"""
        if self.main_window and hasattr(self.main_window, 'server_manager'):
            # 连接互斥状态变化信号
            self.main_window.server_manager.gui_streaming_changed.connect(self.on_gui_streaming_signal_changed)
    

    
    def on_gui_streaming_signal_changed(self, enabled):
        """响应GUI流式输出状态变化信号"""
        # 阻止信号循环触发
        self.gui_streaming_checkbox.blockSignals(True)
        self.gui_streaming_checkbox.setChecked(enabled)
        self.gui_streaming_checkbox.blockSignals(False)
    
    def clear_logs(self):
        """清除日志"""
        if self.main_window:
            self.main_window.clear_logs()
    
    def refresh_players(self):
        """刷新玩家列表"""
        if self.main_window:
            # 先尝试连接RCON
            if hasattr(self.main_window, 'server_manager'):
                if not self.main_window.server_manager.is_rcon_connected:
                    self.main_window.server_manager.connect_rcon()
            # 然后刷新玩家列表
            self.main_window.refresh_players()
    
    def on_gui_streaming_changed(self, state):
        """处理GUI流式输出开关状态变化"""
        if self.main_window and hasattr(self.main_window, 'server_manager'):
            enabled = state == 2  # Qt.CheckState.Checked
            self.main_window.server_manager.set_gui_streaming(enabled)
    

    
    def update_status(self, status):
        """更新服务器状态"""
        self.status_label.setText(status)
        
        if status == "在线":
            self.status_label.setObjectName("status_online")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.restart_button.setEnabled(True)
        elif status == "启动中":
            self.status_label.setObjectName("status_starting")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.restart_button.setEnabled(False)
        else:
            self.status_label.setObjectName("status_offline")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.restart_button.setEnabled(False)
        
        # 重新应用样式
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
    

    
    def update_uptime(self, uptime):
        """更新运行时间"""
        self.uptime_label.setText(uptime)
    
    def update_memory(self, memory):
        """更新内存使用"""
        self.memory_label.setText(memory)
    
    def add_log(self, message):
        """添加日志"""
        self.log_text.append(message)
        
        # 限制显示行数，避免内存占用过大
        if self.log_text.document().blockCount() > 1000:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 100)
            cursor.removeSelectedText()
        
        # 强制自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # 确保光标在最后位置
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()
    
    def add_log_with_players(self, message):
        """添加日志（不再显示在线玩家信息，因为已移除在线玩家区域）"""
        self.log_text.append(message)
        
        # 强制自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # 确保光标在最后位置
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()
    
    def clear_log_display(self):
        """清除日志显示"""
        self.log_text.clear()
    
    def update_mod_status(self, mod_name, mod_id):
        """更新mod加载状态"""
        # 清除初始状态标签（添加安全检查）
        try:
            if (hasattr(self, 'mod_status_label') and 
                self.mod_status_label is not None and 
                not self.mod_status_label.isHidden() and
                self.mod_status_label.text() == "等待服务器启动..."):
                self.mod_status_label.hide()
        except RuntimeError:
            # QLabel已被删除，忽略错误
            pass
        
        # 创建mod状态标签
        mod_label = QLabel(f"{mod_name}")
        mod_label.setStyleSheet("""
            QLabel {
                background-color: #4caf50;
                color: white;
                border-radius: 12px;
                padding: 4px 8px;
                font-size: 10pt;
                font-weight: bold;
                margin: 2px;
            }
        """)
        mod_label.setToolTip(f"Mod ID: {mod_id}")
        
        # 添加到布局中
        self.mod_status_layout.addWidget(mod_label)
    
    def reset_mod_status(self):
        """重置mod状态显示"""
        # 清除所有mod标签
        while self.mod_status_layout.count() > 0:
            child = self.mod_status_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 重新创建初始状态标签（因为上面的清除操作可能已经删除了它）
        self.mod_status_label = QLabel("等待服务器启动...")
        self.mod_status_label.setStyleSheet("font-weight: bold; color: #e65100; background: transparent; border: none; font-size: 10pt;")
        self.mod_status_layout.addWidget(self.mod_status_label)
    
    def update_players_table(self, players_data):
        """更新玩家显示"""
        if not players_data:
            self.players_display.setHtml("<p style='color: #6c757d; font-style: italic;'>暂无在线玩家</p>")
            return
        
        # 定义彩色样式列表
        colors = [
            '#e74c3c',  # 红色
            '#3498db',  # 蓝色
            '#2ecc71',  # 绿色
            '#f39c12',  # 橙色
            '#9b59b6',  # 紫色
            '#1abc9c',  # 青色
            '#e67e22',  # 深橙色
            '#34495e',  # 深蓝灰色
            '#e91e63',  # 粉红色
            '#00bcd4'   # 青蓝色
        ]
        
        html_content = "<div style='line-height: 1.6;'>"
        html_content += "<h4 style='margin: 0 0 10px 0; color: #495057;'>在线玩家列表:</h4>"
        
        for i, player in enumerate(players_data):
            name = str(player.get('name', '未知玩家'))
            time = str(player.get('time', ''))
            
            # 循环使用颜色
            color = colors[i % len(colors)]
            
            # 创建彩色玩家名字
            player_html = f"<span style='color: {color}; font-weight: bold; font-size: 13pt;'>● {name}</span>"
            
            # 如果有在线时间信息，添加到后面
            if time and time != '未知':
                player_html += f" <span style='color: #6c757d; font-size: 10pt;'>({time})</span>"
            
            html_content += player_html + "<br>"
        
        html_content += "</div>"
        self.players_display.setHtml(html_content)
    
    def on_auto_rcon_changed(self, state):
        """处理RCON自动连接开关状态变化"""
        if self.main_window and hasattr(self.main_window, 'server_manager'):
            enabled = state == 2  # Qt.CheckState.Checked
            self.main_window.server_manager.set_auto_rcon_enabled(enabled)
        else:
            print("无法访问服务器管理器")