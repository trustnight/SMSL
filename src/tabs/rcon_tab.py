# -*- coding: utf-8 -*-

"""
RCON选项卡模块
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QFrame, QTextEdit, QLineEdit, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class RconTab(QWidget):
    """RCON选项卡"""
    
    def __init__(self, parent=None, main_window=None, rcon_manager=None):
        super().__init__(parent)
        self.main_window = main_window
        self.rcon_manager = rcon_manager
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # RCON连接控制
        connection_group = QGroupBox("RCON连接控制")
        connection_layout = QVBoxLayout(connection_group)
        connection_layout.setContentsMargins(10, 15, 10, 10)
        
        # 连接状态显示
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(5, 5, 5, 5)
        
        status_layout.addWidget(QLabel("连接状态:"))
        self.connection_status_label = QLabel("未连接")
        self.connection_status_label.setObjectName("status_offline")
        status_layout.addWidget(self.connection_status_label)
        status_layout.addStretch()
        
        connection_layout.addWidget(status_frame)
        
        # 连接控制按钮
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(5, 5, 5, 5)
        buttons_layout.setSpacing(8)
        
        self.connect_button = QPushButton("连接RCON")
        self.connect_button.setObjectName("connect_button")
        self.connect_button.clicked.connect(self.connect_rcon)
        buttons_layout.addWidget(self.connect_button)
        
        self.disconnect_button = QPushButton("断开连接")
        self.disconnect_button.setObjectName("disconnect_button")
        self.disconnect_button.clicked.connect(self.disconnect_rcon)
        self.disconnect_button.setEnabled(False)
        buttons_layout.addWidget(self.disconnect_button)
        
        self.reconnect_button = QPushButton("重新连接")
        self.reconnect_button.setObjectName("reconnect_button")
        self.reconnect_button.clicked.connect(self.reconnect_rcon)
        buttons_layout.addWidget(self.reconnect_button)
        
        buttons_layout.addStretch()
        connection_layout.addWidget(buttons_frame)
        
        layout.addWidget(connection_group)
        
        # RCON输出显示
        output_group = QGroupBox("RCON输出")
        output_layout = QVBoxLayout(output_group)
        output_layout.setContentsMargins(10, 15, 10, 10)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 9))
        output_layout.addWidget(self.output_text)
        
        layout.addWidget(output_group)
        
        # 命令输入
        command_group = QGroupBox("命令输入")
        command_layout = QVBoxLayout(command_group)
        command_layout.setContentsMargins(10, 15, 10, 10)
        
        # 命令输入框和发送按钮
        input_frame = QFrame()
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(5, 5, 5, 5)
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("输入RCON命令...")
        self.command_input.returnPressed.connect(self.send_command)
        input_layout.addWidget(self.command_input)
        
        self.send_button = QPushButton("发送")
        self.send_button.setObjectName("send_button")
        self.send_button.clicked.connect(self.send_command)
        self.send_button.setEnabled(False)
        input_layout.addWidget(self.send_button)
        
        command_layout.addWidget(input_frame)
        
        # 预设命令按钮
        preset_frame = QFrame()
        preset_layout = QGridLayout(preset_frame)
        preset_layout.setContentsMargins(5, 5, 5, 5)
        preset_layout.setSpacing(6)
        
        # 定义预设命令 (名称, 指令, 参数, 执行次数)
        # 参数和执行次数可以为None或空字符串
        preset_commands = [
            ("查看在线玩家", "lp", None, None),
            ("查看注册玩家", "lap", None, None),
            ("服务器公告", "say", "10分钟后重启服务器！", 3),
            ("保存游戏", "saveworld", None, None),
            ("聊天查看", "soc", "1", None),
            ("聊天关闭", "soc", "0", None),
            ("查看帮助", "help", None, None)
        ]
        
        # 创建预设命令按钮
        row = 0
        col = 0
        for preset_data in preset_commands:
            name = preset_data[0]
            button = QPushButton(name)
            button.clicked.connect(lambda checked, data=preset_data: self.send_preset_command(data))
            button.setEnabled(False)
            preset_layout.addWidget(button, row, col)
            
            # 保存按钮引用以便后续启用/禁用
            if not hasattr(self, 'preset_buttons'):
                self.preset_buttons = []
            self.preset_buttons.append(button)
            
            col += 1
            if col >= 4:  # 每行4个按钮
                col = 0
                row += 1
        
        command_layout.addWidget(preset_frame)
        layout.addWidget(command_group)
    
    def connect_rcon(self):
        """连接RCON"""
        if self.main_window and hasattr(self.main_window, 'server_manager'):
            success = self.main_window.server_manager.connect_rcon()
            if success:
                self.update_connection_status(True)
    
    def disconnect_rcon(self):
        """断开RCON连接"""
        if self.main_window and hasattr(self.main_window, 'server_manager'):
            self.main_window.server_manager.disconnect_rcon()
            self.update_connection_status(False)
    
    def reconnect_rcon(self):
        """重新连接RCON"""
        self.disconnect_rcon()
        self.connect_rcon()
    
    def send_command(self):
        """发送命令"""
        command = self.command_input.text().strip()
        if not command:
            return
        
        if self.main_window and hasattr(self.main_window, 'server_manager'):
            # 显示发送的命令
            self.add_output(f"> {command}", "command")
            
            # 执行命令
            result = self.main_window.server_manager.execute_rcon_command(command)
            
            # 显示结果
            self.add_output(result, "response")
            
            # 清空输入框
            self.command_input.clear()
    
    def send_preset_command(self, preset_data):
        """发送预设命令"""
        name, command, params, count = preset_data
        
        # 构建完整命令
        full_command = command
        if params:
            full_command += f" {params}"
        
        # 确定执行次数
        execute_count = count if count and count > 0 else 1
        
        # 执行命令指定次数
        for i in range(execute_count):
            self.command_input.setText(full_command)
            self.send_command()
    
    def update_connection_status(self, connected):
        """更新连接状态"""
        if connected:
            self.connection_status_label.setText("已连接")
            self.connection_status_label.setObjectName("status_online")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.send_button.setEnabled(True)
            
            # 启用预设命令按钮
            if hasattr(self, 'preset_buttons'):
                for button in self.preset_buttons:
                    button.setEnabled(True)
        else:
            self.connection_status_label.setText("未连接")
            self.connection_status_label.setObjectName("status_offline")
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.send_button.setEnabled(False)
            
            # 禁用预设命令按钮
            if hasattr(self, 'preset_buttons'):
                for button in self.preset_buttons:
                    button.setEnabled(False)
        
        # 刷新样式
        self.connection_status_label.style().unpolish(self.connection_status_label)
        self.connection_status_label.style().polish(self.connection_status_label)
    
    def add_output(self, text, message_type="info"):
        """添加输出信息"""
        # 检查是否为表格数据（包含 | 分隔符）
        if '|' in text and message_type == "info":
            formatted_text = self._format_table(text)
        else:
            # 将换行符转换为HTML换行标签
            text = text.replace('\n', '<br>')
            
            if message_type == "command":
                formatted_text = f"<span style='color: #007acc; font-weight: bold;'>{text}</span>"
            elif message_type == "response":
                formatted_text = f"<span style='color: #333;'>{text}</span>"
            elif message_type == "error":
                formatted_text = f"<span style='color: #dc3545; font-weight: bold;'>{text}</span>"
            else:
                formatted_text = f"<span style='color: #6c757d;'>{text}</span>"
        
        self.output_text.append(formatted_text)
        
        # 滚动到底部
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output_text.setTextCursor(cursor)
    
    def _format_table(self, text):
        """格式化表格数据"""
        lines = text.strip().split('\n')
        if len(lines) < 2:
            br_text = text.replace('\n', '<br>')
            return f"<span style='color: #6c757d;'>{br_text}</span>"
        
        # 构建HTML表格
        table_html = "<table style='border-collapse: collapse; width: 100%; font-family: monospace; margin: 5px 0;'>"
        
        for i, line in enumerate(lines):
            if '|' in line:
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                if cells:
                    if i == 0:  # 表头
                        table_html += "<tr style='background-color: #f8f9fa;'>"
                        for cell in cells:
                            table_html += f"<th style='border: 1px solid #dee2e6; padding: 8px; text-align: left; font-weight: bold;'>{cell}</th>"
                        table_html += "</tr>"
                    else:  # 数据行
                        table_html += "<tr style='background-color: white;'>"
                        for cell in cells:
                            table_html += f"<td style='border: 1px solid #dee2e6; padding: 8px; text-align: left;'>{cell}</td>"
                        table_html += "</tr>"
        
        table_html += "</table>"
        return table_html
    
    def clear_output(self):
        """清空输出"""
        self.output_text.clear()