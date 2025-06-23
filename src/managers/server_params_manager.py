#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
服务器启动参数管理模块
"""

import os
import json
from PySide6.QtCore import QObject, Signal
from ..common.utils import get_app_dir
from ..common.constants import DEFAULT_CONFIG_FILE, DEFAULT_SERVER_CONFIG


class ServerParamsManager(QObject):
    # 信号定义
    config_loaded = Signal(dict)  # 配置加载完成信号
    config_saved = Signal()       # 配置保存完成信号
    
    def __init__(self):
        super().__init__()
        # 首先尝试从默认位置读取根目录配置
        self.config_file = self._determine_config_file()
        self.default_config = DEFAULT_SERVER_CONFIG
        self.current_config = self.default_config.copy()
    
    def _determine_config_file(self):
        """确定配置文件路径"""
        from ..common.utils import get_app_dir
        import json
        
        # 创建根目录索引文件路径（固定在应用程序目录）
        app_dir = get_app_dir()
        root_index_file = os.path.join(app_dir, 'root_directory.json')
        
        # 首先检查根目录索引文件
        try:
            if os.path.exists(root_index_file):
                with open(root_index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    root_dir = index_data.get('current_root_dir')
                    if root_dir and os.path.exists(root_dir):
                        # 使用索引文件中记录的根目录
                        from ..common.constants import PathConfig
                        path_config = PathConfig(root_dir)
                        config_file = path_config.config_file
                        # 确保配置文件目录存在
                        os.makedirs(os.path.dirname(config_file), exist_ok=True)
                        return config_file
        except Exception:
            pass
        
        # 如果索引文件不存在或无效，检查默认配置文件
        default_config_file = DEFAULT_CONFIG_FILE
        try:
            if os.path.exists(default_config_file):
                with open(default_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    root_dir = config.get('root_dir')
                    if root_dir and os.path.exists(root_dir):
                        # 创建/更新根目录索引文件
                        self._update_root_index(root_dir)
                        # 使用该根目录下的配置文件
                        from ..common.constants import PathConfig
                        path_config = PathConfig(root_dir)
                        return path_config.config_file
        except Exception:
            pass
        
        # 如果都没有找到，使用默认配置文件
        return default_config_file
    
    def _update_root_index(self, root_dir):
        """更新根目录索引文件"""
        from ..common.utils import get_app_dir
        import json
        
        try:
            app_dir = get_app_dir()
            root_index_file = os.path.join(app_dir, 'root_directory.json')
            
            index_data = {
                'current_root_dir': root_dir,
                'last_updated': str(os.path.getmtime(root_dir)) if os.path.exists(root_dir) else None
            }
            
            with open(root_index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"更新根目录索引文件失败: {e}")
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    self.current_config.update(loaded_config)
            # 如果配置文件不存在，不自动创建，使用默认配置
            
            # 如果路径为空，使用默认路径
            from ..common.utils import (
                get_steamcmd_dir, get_server_path, 
                get_backup_dir, get_log_file_path, get_config_file_path
            )
            
            # server_path已合并到server_path，无需单独处理
            if not self.current_config.get('steamcmd_path'):
                self.current_config['steamcmd_path'] = get_steamcmd_dir()
            if not self.current_config.get('server_path'):
                self.current_config['server_path'] = get_server_path()
            if not self.current_config.get('backup_dir'):
                self.current_config['backup_dir'] = get_backup_dir()
            if not self.current_config.get('log_file_path'):
                self.current_config['log_file_path'] = get_log_file_path()
            if not self.current_config.get('config_file_path'):
                self.current_config['config_file_path'] = get_config_file_path()
            
            self.config_loaded.emit(self.current_config)
            return self.current_config
            
        except Exception as e:
            print(f"加载配置文件时出错: {str(e)}")
            # 使用默认配置
            self.config_loaded.emit(self.current_config)
            return self.current_config
    
    def save_config(self, config=None, show_message=True):
        """保存配置文件"""
        try:
            if config:
                self.current_config.update(config)
            
            # 如果配置中包含root_dir变更，需要更新配置文件路径和索引文件
            if config and 'root_dir' in config:
                new_root_dir = config['root_dir']
                if new_root_dir and os.path.exists(new_root_dir):
                    # 更新根目录索引文件
                    self._update_root_index(new_root_dir)
                    from ..common.constants import PathConfig
                    path_config = PathConfig(new_root_dir)
                    new_config_file = path_config.config_file
                    
                    # 如果配置文件路径发生变化，更新路径
                    if new_config_file != self.config_file:
                        self.config_file = new_config_file
            
            # 确保配置目录存在
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_config, f, ensure_ascii=False, indent=2)
            
            self.config_saved.emit()
            return True
            
        except Exception as e:
            print(f"保存配置文件时出错: {str(e)}")
            return False
    
    def get_config(self, key=None):
        """获取配置值"""
        if key:
            return self.current_config.get(key)
        return self.current_config.copy()
    
    def set_config(self, key, value):
        """设置配置值"""
        self.current_config[key] = value
    
    def update_config(self, config_dict):
        """批量更新配置"""
        self.current_config.update(config_dict)
    
    def reset_to_default(self):
        """重置为默认配置"""
        self.current_config = self.default_config.copy()
        self.save_config()
        self.config_loaded.emit(self.current_config)