# -*- coding: utf-8 -*-

"""
路径管理器模块 - 负责管理应用程序中的各种路径配置
"""

import os
from PySide6.QtCore import QObject, Signal
from ..common.constants import DEFAULT_PATHS, PathConfig
from ..common.utils import ensure_dir_exists, is_valid_path


class PathsManager(QObject):
    """
    路径管理器 - 负责管理和验证应用程序中的各种路径
    """
    
    # 信号定义
    path_changed = Signal(str, str)      # 路径改变信号 (path_type, new_path)
    path_validated = Signal(str, bool)   # 路径验证信号 (path_type, is_valid)
    directory_created = Signal(str)      # 目录创建信号
    error_occurred = Signal(str)         # 错误发生信号
    
    def __init__(self):
        super().__init__()
        # 使用统一的路径配置
        self.path_config = PathConfig()
        
        # 路径类型的中文名称映射
        self.path_names = {
            'root_dir': '服务器根目录',
            'steamcmd_dir': 'SteamCMD目录',
            'game_install_dir': '游戏安装路径',
            'backup_dir': '备份目录',
            'log_file': '日志文件',
            'config_file': '配置文件',
            'server_exe': '服务器可执行文件',
        }
        
    def set_root_directory(self, root_dir):
        """
        设置服务器根目录，其他路径将自动基于此目录生成
        """
        # 标准化路径
        normalized_path = os.path.normpath(root_dir)
        
        # 验证路径
        if self.validate_path('root_dir', normalized_path):
            old_path = self.path_config.root_dir
            self.path_config.root_dir = normalized_path
            self.path_changed.emit('root_dir', normalized_path)
            return True
        else:
            return False
    
    def set_path(self, path_type, path):
        """
        设置指定类型的路径（主要用于根目录设置）
        """
        if path_type == 'root_dir':
            return self.set_root_directory(path)
        else:
            self.error_occurred.emit(f"不支持直接设置路径类型: {path_type}，请设置根目录")
            return False
            
    def get_path(self, path_type):
        """
        获取指定类型的路径
        """
        if hasattr(self.path_config, path_type):
            return getattr(self.path_config, path_type)
        else:
            return ''
        
    def get_all_paths(self):
        """
        获取所有路径配置
        """
        return self.path_config.get_all_paths()
        
    def validate_path(self, path_type, path):
        """
        验证路径是否有效
        """
        try:
            if not path:
                self.path_validated.emit(path_type, False)
                return False
                
            # 根据路径类型进行不同的验证
            if path_type in ['root_dir', 'steamcmd_dir', 'game_install_dir', 'backup_dir']:
                # 目录路径验证
                is_valid = self._validate_directory_path(path)
            elif path_type in ['log_file', 'config_file']:
                # 文件路径验证
                is_valid = self._validate_file_path(path)
            elif path_type == 'server_exe':
                # 可执行文件验证
                is_valid = self._validate_executable_path(path)
            else:
                is_valid = is_valid_path(path)
                
            self.path_validated.emit(path_type, is_valid)
            return is_valid
            
        except Exception as e:
            self.error_occurred.emit(f"验证路径时发生错误: {str(e)}")
            self.path_validated.emit(path_type, False)
            return False
            
    def _validate_directory_path(self, path):
        """
        验证目录路径
        """
        # 检查路径格式是否有效
        if not is_valid_path(path):
            return False
            
        # 如果目录不存在，检查是否可以创建
        if not os.path.exists(path):
            try:
                parent_dir = os.path.dirname(path)
                if parent_dir and not os.path.exists(parent_dir):
                    # 检查父目录是否可以创建
                    return is_valid_path(parent_dir)
                return True
            except Exception:
                return False
        else:
            # 如果存在，检查是否为目录
            return os.path.isdir(path)
            
    def _validate_file_path(self, path):
        """
        验证文件路径
        """
        # 检查路径格式是否有效
        if not is_valid_path(path):
            return False
            
        # 检查父目录是否存在或可以创建
        parent_dir = os.path.dirname(path)
        if parent_dir:
            return self._validate_directory_path(parent_dir)
        return True
        
    def _validate_executable_path(self, path):
        """
        验证可执行文件路径
        """
        if not is_valid_path(path):
            return False
            
        if os.path.exists(path):
            return os.path.isfile(path) and os.access(path, os.X_OK)
        else:
            # 如果文件不存在，检查扩展名
            _, ext = os.path.splitext(path)
            return ext.lower() in ['.exe', '.bat', '.cmd']
            
    def create_directory(self, path_type):
        """
        创建指定类型的目录
        """
        if path_type not in self.path_names:
            self.error_occurred.emit(f"未知的路径类型: {path_type}")
            return False
            
        path = self.get_path(path_type)
        
        # 对于文件路径，创建其父目录
        if path_type in ['log_file', 'config_file', 'server_exe']:
            path = os.path.dirname(path)
            
        if not path:
            self.error_occurred.emit(f"路径为空: {self.path_names.get(path_type, path_type)}")
            return False
            
        try:
            if ensure_dir_exists(path):
                self.directory_created.emit(path)
                return True
            else:
                self.error_occurred.emit(f"无法创建目录: {path}")
                return False
        except Exception as e:
            self.error_occurred.emit(f"创建目录时发生错误: {str(e)}")
            return False
            
    def create_all_directories(self):
        """
        创建所有必要的目录
        """
        success_count = 0
        total_count = 0
        
        for path_type in ['steamcmd_dir', 'game_install_dir', 'backup_dir']:
            total_count += 1
            if self.create_directory(path_type):
                success_count += 1
                
        # 为文件路径创建父目录
        for path_type in ['log_file', 'config_file']:
            total_count += 1
            if self.create_directory(path_type):
                success_count += 1
                
        return success_count == total_count
        
    def get_path_info(self, path_type):
        """
        获取路径信息
        """
        if path_type not in self.paths:
            return None
            
        path = self.paths[path_type]
        info = {
            'type': path_type,
            'name': self.path_names.get(path_type, path_type),
            'path': path,
            'exists': os.path.exists(path) if path else False,
            'is_valid': False
        }
        
        if path:
            info['is_valid'] = self.validate_path(path_type, path)
            
            if os.path.exists(path):
                info['is_directory'] = os.path.isdir(path)
                info['is_file'] = os.path.isfile(path)
                info['size'] = os.path.getsize(path) if os.path.isfile(path) else 0
                info['modified_time'] = os.path.getmtime(path)
                
        return info
        
    def get_all_paths_info(self):
        """
        获取所有路径的信息
        """
        return {path_type: self.get_path_info(path_type) for path_type in self.paths}
        
    def reset_to_defaults(self):
        """
        重置所有路径为默认值
        """
        default_paths = {
            'steamcmd_dir': DEFAULT_STEAMCMD_DIR,
            'server_path': DEFAULT_server_path,
            'backup_dir': DEFAULT_BACKUP_DIR,
            'log_file': DEFAULT_LOG_FILE,
            'config_file': DEFAULT_CONFIG_FILE,
            'server_exe': '',
            'world_save_dir': '',
        }
        
        for path_type, default_path in default_paths.items():
            if self.paths[path_type] != default_path:
                self.paths[path_type] = default_path
                self.path_changed.emit(path_type, default_path)
                
    def export_paths_config(self):
        """
        导出路径配置
        """
        return {
            'paths': self.paths.copy(),
            'version': '1.0'
        }
        
    def import_paths_config(self, config):
        """
        导入路径配置
        """
        try:
            if 'paths' not in config:
                self.error_occurred.emit("无效的配置格式")
                return False
                
            imported_paths = config['paths']
            for path_type, path in imported_paths.items():
                if path_type in self.paths:
                    self.set_path(path_type, path)
                    
            return True
        except Exception as e:
            self.error_occurred.emit(f"导入配置时发生错误: {str(e)}")
            return False