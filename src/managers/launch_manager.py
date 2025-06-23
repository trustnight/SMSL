#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
启动管理器模块 - 负责管理应用程序启动相关的逻辑
"""

from PySide6.QtCore import QObject, Signal
from ..common.constants import APP_NAME, APP_VERSION, APP_TITLE
from ..common.utils import ensure_dir_exists, get_backup_dir, get_log_file_path
import os
import logging


class LaunchManager(QObject):
    """
    启动管理器 - 负责应用程序启动时的初始化工作
    """
    
    # 信号定义
    initialization_complete = Signal()  # 初始化完成信号
    initialization_error = Signal(str)   # 初始化错误信号
    
    def __init__(self):
        super().__init__()
        self.app_name = APP_NAME
        self.app_version = APP_VERSION
        self.app_title = APP_TITLE
        self.is_initialized = False
        
    def initialize_application(self):
        """
        初始化应用程序
        """
        try:
            # 创建必要的目录
            self._create_directories()
            
            # 初始化日志系统
            self._setup_logging()
            
            # 检查应用程序环境
            self._check_environment()
            
            self.is_initialized = True
            self.initialization_complete.emit()
            
        except Exception as e:
            error_msg = f"应用程序初始化失败: {str(e)}"
            self.initialization_error.emit(error_msg)
            
    def _create_directories(self):
        """
        创建必要的目录 - 改为延迟创建，不在启动时创建
        """
        # 不在启动时创建目录，改为在需要时创建
        pass
                
    def _setup_logging(self):
        """
        设置日志系统 - 只设置控制台输出，不创建文件
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
        
    def _check_environment(self):
        """
        检查应用程序运行环境
        """
        # 检查Python版本
        import sys
        if sys.version_info < (3, 8):
            raise Exception("需要Python 3.8或更高版本")
            
        # 检查必要的模块
        try:
            import PySide6
        except ImportError:
            raise Exception("缺少PySide6模块，请安装相关依赖")
            
    def get_app_info(self):
        """
        获取应用程序信息
        """
        return {
            'name': self.app_name,
            'version': self.app_version,
            'title': self.app_title,
            'initialized': self.is_initialized
        }
        
    def shutdown(self):
        """
        应用程序关闭时的清理工作
        """
        logging.info(f"{self.app_name} 正在关闭...")
        self.is_initialized = False