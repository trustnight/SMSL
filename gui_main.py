#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
灵魂面甲服务器启动器 - 主GUI界面
重构版本：只负责QMainWindow设置和选项卡管理
"""

import sys
import os
import shutil
import ctypes
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QLabel, QMessageBox, QInputDialog
)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QCloseEvent

# 导入常量和工具
from src.common.constants import APP_TITLE, APP_GEOMETRY, APP_DIR

# 导入管理器
from src.managers.log_manager import LogManager
from src.managers.server_manager import ServerManager

from src.managers.backup_manager import BackupManager
from src.managers.launch_manager import LaunchManager
from src.managers.paths_manager import PathsManager
from src.managers.rcon_manager import RconManager
from src.managers.server_params_manager import ServerParamsManager
from src.managers.steamcmd_manager import SteamCMDManager

# 导入选项卡模块
from src.tabs.backup_tab import BackupTab
from src.tabs.launch_tab import LaunchTab
from src.tabs.paths_tab import PathsTab
from src.tabs.rcon_tab import RconTab
from src.tabs.server_params_tab import ServerParamsTab
from src.tabs.steamcmd_tab import SteamCMDTab


class SoulServerLauncher(QMainWindow):
    """灵魂面甲服务器启动器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setGeometry(*APP_GEOMETRY)
        
        # 初始化管理器
        self.launch_manager = LaunchManager()
        self.config_manager = ServerParamsManager()
        self.paths_manager = PathsManager()
        self.rcon_manager = RconManager()
        self.server_manager = ServerManager()
        self.steamcmd_manager = SteamCMDManager(config_manager=self.config_manager)
        self.backup_manager = BackupManager(config_manager=self.config_manager)
        self.log_manager = LogManager(config_manager=self.config_manager)
        
        # 连接信号
        self._connect_signals()
        
        # 创建UI
        self.create_ui()
        
        # 加载样式表
        self.load_stylesheet()
        
        # 加载配置
        self.load_config()
        
        # 设置定时器检查服务器状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_server_status)
        self.status_timer.start(5000)  # 每5秒检查一次
        
        # 设置安装状态检测定时器
        self.installation_timer = QTimer()
        self.installation_timer.timeout.connect(self.check_installations)
        self.installation_timer.start(30000)  # 每30秒检查一次安装状态
        
        # 启动应用程序初始化
        self.launch_manager.initialize_application()
        
        # 启动时自动检测安装状态
        self.auto_detect_installations()
    
    def closeEvent(self, event: QCloseEvent):
        """处理窗口关闭事件，检查未保存的更改"""
        # 检查路径选项卡是否有未保存的更改
        if hasattr(self, 'paths_tab') and self.paths_tab.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "未保存的更改",
                "路径设置有未保存的更改，确定要退出吗？\n\n点击'Yes'退出程序\n点击'No'返回保存更改",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()  # 取消关闭事件
                return
        
        # 如果没有未保存的更改或用户选择退出，继续关闭程序
        self.log_manager.add_info("程序正在关闭...")
        event.accept()
    
    def load_stylesheet(self):
        """加载样式表"""
        # 尝试从打包后的资源路径加载
        if getattr(sys, 'frozen', False):
            # 打包后的环境，从临时目录加载
            css_file_path = os.path.join(sys._MEIPASS, 'src', 'common', 'styles.css')
        else:
            # 开发环境
            css_file_path = os.path.join(APP_DIR, 'src', 'common', 'styles.css')
        
        try:
            with open(css_file_path, 'r', encoding='utf-8') as file:
                stylesheet = file.read()
                self.setStyleSheet(stylesheet)
        except Exception as e:
            print(f"加载样式表文件失败: {e}")
            # 如果加载失败，使用基本样式
            self.setStyleSheet("QWidget { background-color: white; }")
    
    def _connect_signals(self):
        """连接信号槽"""
        # 启动管理器信号
        self.launch_manager.initialization_complete.connect(self.on_initialization_complete)
        self.launch_manager.initialization_error.connect(self.on_initialization_error)
        
        # 配置管理器信号
        self.config_manager.config_loaded.connect(self.on_config_loaded)
        
        # 路径管理器信号
        self.paths_manager.path_changed.connect(self.on_path_changed)
        self.paths_manager.error_occurred.connect(self.log_manager.add_error)
        
        # RCON管理器信号
        self.rcon_manager.connection_status_changed.connect(self.on_rcon_status_changed)
        self.rcon_manager.command_result.connect(self.on_rcon_command_result)
        self.rcon_manager.error_occurred.connect(self.on_rcon_error)
        
        # 服务器管理器信号
        self.server_manager.status_changed.connect(self.on_server_status_changed)
        # 移除重复的日志连接，现在通过on_server_log_message统一处理
        # self.server_manager.log_message.connect(self.log_manager.add_info)
        self.server_manager.server_started.connect(self.on_server_started)
        self.server_manager.server_stopped.connect(self.on_server_stopped)
        
        # RCON相关信号
        self.server_manager.rcon_connected.connect(self.on_rcon_connected)
        self.server_manager.rcon_disconnected.connect(self.on_rcon_disconnected)
        self.server_manager.rcon_error.connect(self.on_rcon_error)
        self.server_manager.players_updated.connect(self.on_players_updated)
        
        # SteamCMD管理器信号 - 现在直接连接到steamcmd_tab
        self.steamcmd_manager.log_message.connect(self.log_manager.add_info)
        
        # 备份管理器信号
        self.backup_manager.backup_started.connect(self.on_backup_started)
        self.backup_manager.backup_finished.connect(self.on_backup_finished)
        self.backup_manager.backup_progress.connect(self.on_backup_progress)
        self.backup_manager.log_message.connect(self.log_manager.add_info)
    
    def create_ui(self):
        """创建用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 创建标题栏
        title_bar = QLabel("灵魂面甲服务器启动器")
        title_bar.setObjectName("title_bar")
        title_bar.setStyleSheet("""
            QLabel#title_bar {
                background-color: #f8f9fa;
                color: #495057;
                padding: 8px;
                font-size: 14pt;
                font-weight: 600;
                text-align: center;
                border-bottom: 1px solid #dee2e6;
            }
        """)
        main_layout.addWidget(title_bar)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建各个选项卡
        self.launch_tab = LaunchTab(main_window=self)
        self.config_tab = ServerParamsTab(main_window=self)
        self.steamcmd_tab = SteamCMDTab(main_window=self, steamcmd_manager=self.steamcmd_manager)
        self.backup_tab = BackupTab(main_window=self)
        self.paths_tab = PathsTab(main_window=self, paths_manager=self.paths_manager)
        self.rcon_tab = RconTab(main_window=self, rcon_manager=self.rcon_manager)
        
        # 添加选项卡到选项卡控件
        self.tab_widget.addTab(self.launch_tab, "启动服务器")
        self.tab_widget.addTab(self.config_tab, "服务器启动参数")
        self.tab_widget.addTab(self.steamcmd_tab, "SteamCMD管理")
        self.tab_widget.addTab(self.backup_tab, "备份管理")
        self.tab_widget.addTab(self.rcon_tab, "RCON控制台")
        self.tab_widget.addTab(self.paths_tab, "路径设置")
        
    
        # 连接选项卡信号（在创建选项卡后）
        self.config_tab.config_saved.connect(self.save_server_config)
        self.backup_tab.backup_settings_saved.connect(self.save_backup_settings)
        
        # 连接服务器管理器的日志信号到启动选项卡，这样启动命令就能在UI上显示
        self.server_manager.log_message.connect(self.on_server_log_message)
        
        # log_manager不再直接使用GUI控件，只负责文件日志
        # 如果需要在GUI显示系统日志，通过专门的方法调用
        # 连接mod加载信号
        self.server_manager.mod_loaded.connect(self.on_mod_loaded)
        
        # 创建定时器定期更新服务器状态（运行时间和内存）
        from PySide6.QtCore import QTimer
        self.status_update_timer = QTimer()
        self.status_update_timer.timeout.connect(self.update_server_status_display)
        self.status_update_timer.start(1000)  # 每秒更新一次
        
        # 设置状态栏
        self.status_label = QLabel("就绪")
        self.statusBar().addWidget(self.status_label)
        
        # 版本信息
        version_label = QLabel("V0.1")
        self.statusBar().addPermanentWidget(version_label)
    
    def load_config(self):
        """加载配置"""
        try:
            config = self.config_manager.load_config()
            
            # 首先处理根目录配置
            if config.get('root_dir'):
                # 将根目录应用到paths_manager
                self.paths_manager.set_root_directory(config['root_dir'])
                
                # 更新各管理器的路径（基于新的根目录）
                self.server_manager.set_server_path(self.paths_manager.get_path('game_install_dir'))
                self.steamcmd_manager.set_steamcmd_dir(self.paths_manager.get_path('steamcmd_dir'))
                self.steamcmd_manager.set_server_path(self.paths_manager.get_path('game_install_dir'))
                self.backup_manager.set_server_path(self.paths_manager.get_path('game_install_dir'))
                self.backup_manager.set_backup_dir(self.paths_manager.get_path('backup_dir'))
                self.log_manager.set_log_file_path(self.paths_manager.get_path('log_file'))
            else:
                # 如果没有根目录配置，使用传统方式设置路径
                if config.get('server_path'):
                    self.server_manager.set_server_path(config['server_path'])
                    self.backup_manager.set_server_path(config['server_path'])
                if config.get('steamcmd_path'):
                    self.steamcmd_manager.set_steamcmd_dir(config['steamcmd_path'])
                if config.get('server_path'):
                    self.steamcmd_manager.set_server_path(config['server_path'])
                if config.get('backup_dir'):
                    self.backup_manager.set_backup_dir(config['backup_dir'])
            
            self.config_tab.load_config(config)
            self.backup_tab.load_backup_settings(config)
            
            # 将备份设置应用到备份管理器
            if config.get('auto_backup', False):
                self.backup_manager.set_auto_backup(
                    enabled=True,
                    interval_minutes=config.get('backup_interval', 30)
                )
            else:
                self.backup_manager.set_auto_backup(enabled=False)
            
            # 设置服务器管理器的完整配置
            self.server_manager.set_server_config(config)
            
            # 加载路径配置到路径选项卡
            if hasattr(self, 'paths_tab'):
                self.paths_tab.update_from_config(config)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载配置失败: {e}")
    
    def save_server_config(self, config):
        """保存服务器配置"""
        try:
            self.config_manager.save_config(config)
            # 更新服务器管理器的配置
            self.server_manager.set_server_config(config)
            QMessageBox.information(self, "成功", "配置保存成功！")
        except Exception as e:
            error_msg = f"保存配置失败: {e}"
            self.log_manager.add_error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def save_backup_settings(self, settings):
        """保存备份设置"""
        try:
            current_config = self.config_manager.load_config()
            current_config.update(settings)
            success = self.config_manager.save_config(current_config)
            
            if success:
                # 立即将设置应用到备份管理器
                if settings.get('auto_backup', False):
                    self.backup_manager.set_auto_backup(
                        enabled=True,
                        interval_minutes=settings.get('backup_interval', 30)
                    )
                else:
                    self.backup_manager.set_auto_backup(enabled=False)
                
                # 保存成功后，确保UI显示的是刚保存的值，而不是重新加载配置
                # 不调用load_config，避免UI被重置
                QMessageBox.information(self, "成功", "备份设置保存成功！")
            else:
                QMessageBox.critical(self, "错误", "保存备份设置失败！")
        except Exception as e:
            error_msg = f"保存备份设置失败: {e}"
            self.log_manager.add_error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def save_config(self):
        """保存当前配置"""
        try:
            # 从各个选项卡收集配置
            config = {}
            
            # 从路径选项卡获取SteamCMD路径配置
            if hasattr(self, 'paths_tab'):
                steamcmd_dir = self.paths_tab.steamcmd_dir_edit.text().strip()
                config['steamcmd_dir'] = steamcmd_dir
                config['steamcmd_path'] = steamcmd_dir  # 同时保存steamcmd_path字段
                
                # 记录路径保存到日志
                self.log_manager.add_info(f"保存SteamCMD路径: {steamcmd_dir}")
                
                # 设置游戏安装路径为SteamCMD默认目录
                if steamcmd_dir:
                    import os
                    server_path = os.path.join(steamcmd_dir, "steamapps", "common", "Soulmask Dedicated Server For Windows")
                    # 标准化路径格式，统一使用反斜杠
                    config['server_path'] = os.path.normpath(server_path)
                    self.log_manager.add_info(f"自动设置服务端路径: {config['server_path']}")
            
            self.config_manager.save_config(config, show_message=False)
            self.log_manager.add_info("配置文件保存完成")
        except Exception as e:
            error_msg = f"保存配置失败: {e}"
            self.log_manager.add_error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    # 服务器控制方法
    def start_server(self):
        """启动服务器"""
        try:
            config = self.config_manager.load_config()
            
            # 设置服务器路径
            server_path = config.get('server_path', '')
            if server_path:
                self.server_manager.set_server_path(server_path)
            
            self.server_manager.set_server_config(config)
            
            # 先显示启动消息和设置状态
            self.launch_tab.add_log("正在启动服务器...")
            self.launch_tab.update_status("启动中...")
            self.status_label.setText("服务器状态: 启动中...")
            
            # 检查启动结果
            if not self.server_manager.start_server():
                self.launch_tab.add_log("服务器启动失败，请检查路径设置和日志信息")
                self.launch_tab.update_status("离线")
                self.status_label.setText("服务器状态: 离线")
        except Exception as e:
            error_msg = f"启动服务器失败: {e}"
            self.log_manager.add_error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def stop_server(self):
        """停止服务器"""
        try:
            self.launch_tab.add_log("正在停止服务器...")
            self.server_manager.stop_server()
        except Exception as e:
            error_msg = f"停止服务器失败: {e}"
            self.log_manager.add_error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def restart_server(self):
        """重启服务器"""
        try:
            self.launch_tab.add_log("正在重启服务器...")
            self.server_manager.restart_server()
        except Exception as e:
            error_msg = f"重启服务器失败: {e}"
            self.log_manager.add_error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def reload_server_status(self):
        """重新加载服务器状态"""
        try:
            self.server_manager.reload_server_status()
        except Exception as e:
            error_msg = f"重新加载服务器状态失败: {e}"
            self.log_manager.add_error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def update_server_status(self):
        """更新服务器状态"""
        try:
            status = self.server_manager.get_server_status()
            # 根据服务器状态设置显示文本
            if status.get('starting', False):
                status_text = "启动中"
            elif status['running']:
                status_text = "在线"
            else:
                status_text = "离线"
            
            self.launch_tab.update_status(status_text)
            
            if status['running']:
                # 更新运行时间
                if 'uptime' in status:
                    self.launch_tab.update_uptime(status['uptime'])
                
                # 更新内存使用
                if 'memory' in status:
                    self.launch_tab.update_memory(status['memory'])
        except Exception as e:
            print(f"更新服务器状态失败: {e}")
    
    def update_server_status_display(self):
        """定时更新服务器状态显示（仅在服务器运行时更新运行时间和内存）"""
        if self.server_manager.is_running:
            status = self.server_manager.get_server_status()
            
            # 更新运行时间
            if 'uptime' in status:
                self.launch_tab.update_uptime(status['uptime'])
            
            # 更新内存使用
            if 'memory' in status:
                self.launch_tab.update_memory(status['memory'])
    
    def auto_detect_installations(self):
        """启动时自动检测安装状态（静默检查，不输出日志）"""
        try:
            # 静默检测SteamCMD状态，不输出日志
            if hasattr(self, 'steamcmd_tab') and hasattr(self, 'steamcmd_manager'):
                # 直接调用管理器的检查方法，不通过UI方法（避免日志输出）
                steamcmd_status = self.steamcmd_manager.is_steamcmd_installed()
                status_text = "已安装" if steamcmd_status else "未安装"
                self.steamcmd_tab.update_steamcmd_status(status_text)
                
                server_status = self.steamcmd_manager.is_game_installed()
                server_status_text = "已安装" if server_status else "未安装"
                self.steamcmd_tab.update_server_status(server_status_text)
                
        except Exception as e:
            print(f"自动检测安装状态失败: {e}")
    
    def check_installations(self):
        """定期检查安装状态（静默检查）"""
        self.auto_detect_installations()
    
    # SteamCMD相关方法已移除 - 现在由steamcmd_tab直接调用steamcmd_manager
    
    # 备份相关方法
    def create_backup(self):
        """创建备份"""
        try:
            self.backup_manager.create_backup()
            self.backup_tab.add_backup_log("开始创建备份...")
        except Exception as e:
            error_msg = f"创建备份失败: {e}"
            self.log_manager.add_error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def restore_backup(self, backup_name):
        """恢复备份"""
        try:
            self.backup_manager.restore_backup(backup_name)
            self.backup_tab.add_backup_log(f"开始恢复备份: {backup_name}")
        except Exception as e:
            error_msg = f"恢复备份失败: {e}"
            self.log_manager.add_error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def delete_backup(self, backup_name):
        """删除备份"""
        try:
            self.backup_manager.delete_backup(backup_name)
            self.backup_tab.add_backup_log(f"删除备份: {backup_name}")
            self.refresh_backup_list()
        except Exception as e:
            error_msg = f"删除备份失败: {e}"
            self.log_manager.add_error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def delete_multiple_backups(self, backup_names):
        """批量删除备份"""
        if not backup_names:
            return
        
        # 确认对话框
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除这 {len(backup_names)} 个备份吗？\n\n" + "\n".join(backup_names),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success_count = 0
            failed_backups = []
            
            for backup_name in backup_names:
                try:
                    self.backup_manager.delete_backup(backup_name)
                    success_count += 1
                    self.backup_tab.add_backup_log(f"删除备份: {backup_name}")
                except Exception as e:
                    failed_backups.append(f"{backup_name}: {e}")
                    self.log_manager.add_error(f"删除备份失败: {backup_name} - {e}")
            
            # 刷新备份列表
            self.refresh_backup_list()
            
            # 显示结果
            if failed_backups:
                error_msg = f"批量删除完成，成功: {success_count}个，失败: {len(failed_backups)}个\n\n失败详情:\n" + "\n".join(failed_backups)
                QMessageBox.warning(self, "批量删除结果", error_msg)
            else:
                self.backup_tab.add_backup_log(f"批量删除成功: {success_count}个备份")
    
    def refresh_backup_list(self):
        """刷新备份列表"""
        try:
            backups = self.backup_manager.get_backup_list()
            self.backup_tab.update_backup_list(backups)
        except Exception as e:
            error_msg = f"刷新备份列表失败: {e}"
            self.log_manager.add_error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    # 日志相关方法
    def clear_logs(self):
        """清除日志"""
        try:
            self.log_manager.clear_logs()
            self.launch_tab.clear_log_display()
        except Exception as e:
            error_msg = f"清除日志失败: {e}"
            self.log_manager.add_error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def refresh_players(self):
        """刷新玩家列表"""
        try:
            players = self.server_manager.get_online_players()
            self.launch_tab.update_players_table(players)
            # 使用新的方法添加带玩家信息的日志
            self.launch_tab.add_log_with_players("刷新玩家列表")
        except Exception as e:
            error_msg = f"刷新玩家列表失败: {e}"
            self.log_manager.add_error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    # 信号处理方法
    def on_config_loaded(self, config):
        """配置加载完成"""
        self.status_label.setText("配置加载完成: %s" % config["server_name"])
    
    def on_server_status_changed(self, status):
        """服务器状态改变"""
        # 检查服务器管理器的实际运行状态
        if status:
            if hasattr(self.server_manager, 'is_running') and self.server_manager.is_running:
                # 服务器已启动完成
                self.launch_tab.update_status("在线")
                status_text = "在线"
            else:
                # 服务器进程存在但未启动完成
                self.launch_tab.update_status("启动中")
                status_text = "启动中"
        else:
            self.launch_tab.update_status("离线")
            status_text = "离线"
        
        self.status_label.setText(f"服务器状态: {status_text}")
    
    def on_rcon_connected(self):
        """RCON连接成功处理"""
        if hasattr(self, 'rcon_tab'):
            self.rcon_tab.update_connection_status(True)
            self.rcon_tab.add_output("RCON连接成功", "info")
    
    def on_rcon_disconnected(self):
        """RCON断开连接处理"""
        if hasattr(self, 'rcon_tab'):
            self.rcon_tab.update_connection_status(False)
            self.rcon_tab.add_output("RCON连接已断开", "info")
    
    def on_rcon_error(self, error_message):
        """RCON错误处理"""
        if hasattr(self, 'rcon_tab'):
            self.rcon_tab.add_output(f"RCON错误: {error_message}", "error")
    
    def on_rcon_status_changed(self, connected):
        """RCON连接状态变化处理"""
        if connected:
            self.on_rcon_connected()
        else:
            self.on_rcon_disconnected()
    
    def on_rcon_command_result(self, result):
        """RCON命令结果处理"""
        if hasattr(self, 'rcon_tab'):
            self.rcon_tab.add_output(result, "info")
    
    def on_players_updated(self, players_data):
        """玩家信息更新"""
        self.launch_tab.update_players_table(players_data)
    
    def on_server_started(self):
        """处理服务器启动信号"""
        # 更新左下角状态文字
        self.status_label.setText("服务器状态: 在线")
        # 确保状态标签也更新
        self.launch_tab.update_status("在线")
        # 重置mod状态显示
        self.launch_tab.reset_mod_status()
    
    def on_server_stopped(self):
        """处理服务器停止信号"""
        # 输出日志提示服务器已停止
        self.launch_tab.add_log("🔴 服务器已停止")
        # 更新左下角状态文字
        self.status_label.setText("服务器状态: 离线")
        # 确保状态标签也更新
        self.launch_tab.update_status("离线")
        # 重置运行时间和内存显示到默认状态
        self.launch_tab.update_uptime("--:--:--")
        self.launch_tab.update_memory("-- MB")
        # 重置mod状态显示
        self.launch_tab.reset_mod_status()
    
    def on_mod_loaded(self, mod_name, mod_id):
        """处理mod加载信号"""
        self.launch_tab.update_mod_status(mod_name, mod_id)
    
    def on_server_log_message(self, message):
        """处理服务器日志消息，过滤服务器输出流"""
        # 检查是否为系统重要日志（包含特定关键字的消息）
        important_keywords = [
            '🚀', '✅', '❌', '⚠️', '🔍', '📍', '📋', '⏳', '🔗', '💡',  # 表情符号
            '启动服务器', '停止服务器', '重启服务器', '服务器状态', '离线判断',
            '错误:', '警告:', 'RCON', '进程已创建', '启动完成', '连接成功', '连接失败'
        ]
        
        # 检查是否为重要的系统日志
        is_important_log = any(keyword in message for keyword in important_keywords)
        
        if is_important_log:
            # 重要的系统日志：显示在GUI并记录到文件
            self.launch_tab.add_log(message)
            self.log_manager.add_log(message, save_to_file=True)
        else:
            # 服务器原始输出：只在开关开启时显示在GUI，不记录到文件
            if hasattr(self.server_manager, 'enable_gui_streaming') and self.server_manager.enable_gui_streaming:
                self.launch_tab.add_log(message)
    
    def on_path_changed(self, path_type, new_path):
        """路径变更处理"""
        # 路径更新信息只记录到文件，不显示在GUI
        self.log_manager.add_info(f"路径已更新: {path_type} 变更为 '{new_path}'")
        
        # 根据路径类型更新相应的管理器
        if path_type == 'game_install_dir':
            self.server_manager.set_server_path(new_path)
            self.steamcmd_manager.set_server_path(new_path)
            self.backup_manager.set_server_path(new_path)
        elif path_type == 'backup_dir':
            self.backup_manager.set_backup_dir(new_path)
        elif path_type == 'steamcmd_dir':
            self.steamcmd_manager.set_steamcmd_dir(new_path)
        elif path_type == 'log_file':
            self.log_manager.set_log_file_path(new_path)
    
    # SteamCMD信号处理方法已移除 - 现在由steamcmd_tab直接处理
    
    def on_backup_started(self, backup_name):
        """备份开始"""
        self.backup_tab.update_backup_status("备份中")
        self.backup_tab.add_backup_log(f"开始创建备份: {backup_name}")
    
    def on_backup_finished(self, success, message):
        """备份完成"""
        if success:
            self.backup_tab.update_backup_status("完成")
            self.backup_tab.add_backup_log(message)
            self.refresh_backup_list()
        else:
            self.backup_tab.update_backup_status("失败")
            self.backup_tab.add_backup_log(f"备份失败: {message}")
    
    def on_backup_progress(self, progress):
        """备份进度"""
        self.backup_tab.add_backup_log(f"备份进度: {progress}%")
    
    def on_initialization_complete(self):
        """应用程序初始化完成"""
        # 初始化完成，但不记录日志避免创建logs目录
        # 可以在这里添加初始化完成后的逻辑
        
        # GUI完全初始化后，检查是否有已存在的服务器进程
        self.server_manager._check_existing_process()
        
    def on_initialization_error(self, error_message):
        """应用程序初始化错误"""
        self.log_manager.add_error(f"应用程序初始化失败: {error_message}")
        QMessageBox.critical(self, "初始化错误", f"应用程序初始化失败:\n{error_message}")


def check_first_run_and_setup():
    """检查是否是第一次运行，如果是则提示用户创建工作目录"""
    if not getattr(sys, 'frozen', False):
        # 如果不是打包后的exe，跳过检查
        return True
    
    exe_path = sys.executable
    exe_dir = os.path.dirname(exe_path)
    exe_name = os.path.basename(exe_path)
    
    # 检查是否存在首次运行完成标识文件
    setup_complete_file = os.path.join(exe_dir, ".setup_complete")
    if os.path.exists(setup_complete_file):
        # 已经完成首次设置，正常启动
        return True
    
    # 检查是否已经在一个专门的文件夹中（通过检查是否存在配置文件或其他标识文件）
    config_dir = os.path.join(exe_dir, "configs")
    steamcmd_dir = os.path.join(exe_dir, "steamcmd")
    if os.path.exists(config_dir) or os.path.exists(steamcmd_dir):
        # 已经在工作目录中，创建标识文件并正常启动
        try:
            with open(setup_complete_file, 'w', encoding='utf-8') as f:
                f.write("Setup completed")
            # 设置文件为隐藏属性（Windows）
            if os.name == 'nt':
                ctypes.windll.kernel32.SetFileAttributesW(setup_complete_file, 2)
        except:
            pass  # 如果无法创建文件，忽略错误
        return True
    
    # 检查当前目录是否只有exe文件（或很少文件），判断是否需要创建工作目录
    files_in_dir = os.listdir(exe_dir)
    # 如果目录中文件很少（只有exe和可能的一些系统文件），则认为需要创建工作目录
    if len(files_in_dir) <= 3:
        
        # 弹窗提示用户输入文件夹名
        folder_name, ok = QInputDialog.getText(
            None,
            "首次运行设置",
            "检测到这是首次运行，为了更好地管理文件，\n请输入一个文件夹名称来存放程序和相关文件：",
            text="SoulMask_Server"
        )
        
        if not ok or not folder_name.strip():
            QMessageBox.information(None, "提示", "已取消设置，程序将在当前目录运行。")
            return True
        
        folder_name = folder_name.strip()
        # 验证文件夹名是否合法
        invalid_chars = '<>:"/\\|?*'
        if any(char in folder_name for char in invalid_chars):
            QMessageBox.warning(None, "错误", "文件夹名包含非法字符，程序将在当前目录运行。")
            return True
        
        try:
            # 创建新文件夹
            new_folder_path = os.path.join(exe_dir, folder_name)
            if os.path.exists(new_folder_path):
                reply = QMessageBox.question(
                    None,
                    "文件夹已存在",
                    f"文件夹 '{folder_name}' 已存在，是否继续？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return True
            else:
                os.makedirs(new_folder_path)
            
            # 复制exe到新文件夹
            new_exe_path = os.path.join(new_folder_path, exe_name)
            shutil.copy2(exe_path, new_exe_path)
            
            # 在新文件夹中创建首次运行完成标识文件
            setup_complete_file = os.path.join(new_folder_path, ".setup_complete")
            try:
                with open(setup_complete_file, 'w', encoding='utf-8') as f:
                    f.write("Setup completed")
                # 设置文件为隐藏属性（Windows）
                if os.name == 'nt':
                    ctypes.windll.kernel32.SetFileAttributesW(setup_complete_file, 2)
            except:
                pass  # 如果无法创建文件，忽略错误
            
            # 提示用户
            QMessageBox.information(
                None,
                "设置完成",
                f"程序已复制到文件夹 '{folder_name}' 中。\n\n"
                f"请到该文件夹中运行程序：\n{new_exe_path}\n\n"
                "当前程序将关闭。"
            )
            
            # 关闭当前程序
            return False
            
        except Exception as e:
            QMessageBox.critical(
                None,
                "错误",
                f"创建文件夹或复制文件时出错：\n{str(e)}\n\n程序将在当前目录运行。"
            )
            return True
    
    return True


def main():
    """主函数"""
    # 先创建QApplication实例
    app = QApplication(sys.argv)
    
    # 检查首次运行设置
    if not check_first_run_and_setup():
        app.quit()
        return
    
    # 设置应用程序图标（如果需要图标，请在项目根目录创建assets文件夹并放入icon.png）
    # icon_path = os.path.join(get_app_dir(), 'assets', 'icon.png')
    # if os.path.exists(icon_path):
    #     app_icon = QIcon(icon_path)
    #     app.setWindowIcon(app_icon)
    
    # 创建主窗口
    window = SoulServerLauncher()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()