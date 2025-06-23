#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志管理模块
"""

import os
import datetime
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QTextEdit, QApplication
from ..common.utils import get_app_dir
from ..common.constants import DEFAULT_LOG_FILE, MAX_LOG_LINES


class LogManager(QObject):
    """日志管理器"""
    # 信号定义
    log_updated = Signal(str)  # 日志更新信号
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self.log_file = DEFAULT_LOG_FILE
        self.max_log_lines = MAX_LOG_LINES
        self.log_widget = None
        
        # 如果有配置管理器，从配置中更新路径
        if self.config_manager:
            self.update_paths_from_config()
        
        # 不在初始化时创建日志文件，延迟到真正需要时创建
    
    def set_log_widget(self, widget):
        """设置日志显示控件"""
        self.log_widget = widget
        if isinstance(widget, QTextEdit):
            widget.setReadOnly(True)
            widget.document().setMaximumBlockCount(self.max_log_lines)
    
    def add_log(self, message, level="INFO", save_to_file=True):
        """添加日志"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        
        # 发送信号
        self.log_updated.emit(formatted_message)
        
        # 显示到控件
        if self.log_widget:
            self.log_widget.append(formatted_message)
            # 自动滚动到底部
            cursor = self.log_widget.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.log_widget.setTextCursor(cursor)
            # 强制处理事件循环，使日志实时显示
            QApplication.processEvents()
        
        # 保存到文件
        if save_to_file:
            try:
                # 确保日志文件存在
                self._ensure_log_file_exists()
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(formatted_message + '\n')
            except Exception as e:
                print(f"写入日志文件时出错: {str(e)}")
    
    def add_info(self, message):
        """添加信息日志"""
        self.add_log(message, "INFO")
    
    def add_warning(self, message):
        """添加警告日志"""
        self.add_log(message, "WARNING")
    
    def add_error(self, message):
        """添加错误日志"""
        self.add_log(message, "ERROR")
    
    def add_success(self, message):
        """添加成功日志"""
        self.add_log(message, "SUCCESS")
    
    def _save_to_file(self, message):
        """保存日志到文件"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
            
            # 检查文件大小，如果太大则清理
            self._cleanup_log_file()
            
        except Exception as e:
            print(f"保存日志到文件时出错: {str(e)}")
    
    def _cleanup_log_file(self):
        """清理日志文件，保持合理大小"""
        try:
            # 检查文件行数
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 如果行数超过限制，保留最新的行
            if len(lines) > self.max_log_lines:
                keep_lines = lines[-self.max_log_lines:]
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.writelines(keep_lines)
                    
        except Exception as e:
            print(f"清理日志文件时出错: {str(e)}")
    
    def clear_log(self):
        """清空日志"""
        if self.log_widget:
            self.log_widget.clear()
        
        # 清空日志文件
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(f"# 灵魂面甲服务器启动器日志\n")
                f.write(f"# 清空时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        except Exception as e:
            print(f"清空日志文件时出错: {str(e)}")
    
    def save_log_to_file(self, file_path):
        """保存日志到指定文件"""
        try:
            if self.log_widget and hasattr(self.log_widget, 'toPlainText'):
                content = self.log_widget.toPlainText()
            else:
                # 从日志文件读取
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            self.add_error(f"保存日志文件时出错: {str(e)}")
            return False
    
    def load_log_from_file(self):
        """从文件加载日志"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if self.log_widget:
                    self.log_widget.setPlainText(content)
                    # 滚动到底部
                    cursor = self.log_widget.textCursor()
                    cursor.movePosition(cursor.MoveOperation.End)
                    self.log_widget.setTextCursor(cursor)
                
                return True
            
        except Exception as e:
            print(f"加载日志文件时出错: {str(e)}")
            return False
    
    def get_log_file_path(self):
        """获取日志文件路径"""
        return self.log_file
        
    def set_log_file_path(self, path):
        """设置日志文件路径"""
        self.log_file = path
        # 不在设置时创建文件，只在需要时创建
        
        # 如果有配置管理器，更新配置
        if self.config_manager:
            self.config_manager.set_config("log_file_path", path)
    
    def update_paths_from_config(self):
        """从配置中更新路径"""
        if not self.config_manager:
            return
            
        # 获取日志文件路径配置
        log_file_path = self.config_manager.get_config("log_file_path")
        if log_file_path:
            # 只设置路径，不在初始化时创建目录和文件
            self.log_file = log_file_path
    
    def _ensure_log_file_exists(self):
        """确保日志文件存在"""
        # 确保日志目录存在
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception as e:
                print(f"创建日志目录失败: {log_dir}, 错误: {str(e)}")
                return
        
        # 确保文件存在
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(f"# 灵魂面甲服务器启动器日志\n")
                f.write(f"# 启动时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    def set_max_log_lines(self, max_lines):
        """设置最大日志行数"""
        self.max_log_lines = max_lines
        if self.log_widget and isinstance(self.log_widget, QTextEdit):
            self.log_widget.document().setMaximumBlockCount(max_lines)
    
    def filter_logs(self, level=None, keyword=None):
        """过滤日志"""
        if not self.log_widget:
            return
        
        try:
            # 获取所有日志内容
            all_content = self.log_widget.toPlainText()
            lines = all_content.split('\n')
            
            filtered_lines = []
            for line in lines:
                # 级别过滤
                if level and f"[{level}]" not in line:
                    continue
                
                # 关键词过滤
                if keyword and keyword.lower() not in line.lower():
                    continue
                
                filtered_lines.append(line)
            
            # 显示过滤后的内容
            self.log_widget.setPlainText('\n'.join(filtered_lines))
            
        except Exception as e:
            self.add_error(f"过滤日志时出错: {str(e)}")
    
    def get_log_statistics(self):
        """获取日志统计信息"""
        stats = {
            'total_lines': 0,
            'info_count': 0,
            'warning_count': 0,
            'error_count': 0,
            'success_count': 0
        }
        
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                stats['total_lines'] = len(lines)
                
                for line in lines:
                    if '[INFO]' in line:
                        stats['info_count'] += 1
                    elif '[WARNING]' in line:
                        stats['warning_count'] += 1
                    elif '[ERROR]' in line:
                        stats['error_count'] += 1
                    elif '[SUCCESS]' in line:
                        stats['success_count'] += 1
        
        except Exception as e:
            print(f"获取日志统计时出错: {str(e)}")
        
        return stats
        
    def get_recent_logs(self, max_lines=None):
        """获取最近的日志记录
        
        Args:
            max_lines: 最大返回行数，默认为None表示返回所有日志
            
        Returns:
            list: 日志行列表
        """
        if max_lines is None:
            max_lines = self.max_log_lines
            
        logs = []
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 获取最近的日志（最后的max_lines行）
                logs = [line.strip() for line in lines[-max_lines:] if line.strip()]
        except Exception as e:
            print(f"获取最近日志时出错: {str(e)}")
            
        return logs
    
    def clear_logs(self):
        """清除日志文件（GUI调用的方法）"""
        try:
            # 清空日志文件
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write('')
            
            # 清空日志显示控件
            if self.log_widget:
                self.log_widget.clear()
            
            # 添加清除日志的记录
            self.add_log("日志已清除", "INFO")
            
        except Exception as e:
            error_msg = f"清除日志失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)