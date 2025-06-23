#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
服务器管理模块
"""

import os
import time
import datetime
import subprocess
import threading
import socket
import struct
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QObject, Signal
from ..common.constants import DEFAULT_SERVER_CONFIG, DEFAULT_SERVER_EXE


class ServerManager(QObject):
    # 信号定义
    status_changed = Signal(bool)  # 状态变化信号
    log_message = Signal(str)     # 日志消息信号
    server_started = Signal()     # 服务器启动信号
    server_stopped = Signal()     # 服务器停止信号
    rcon_connected = Signal()     # RCON连接成功信号
    rcon_disconnected = Signal()  # RCON断开连接信号
    rcon_error = Signal(str)      # RCON错误信号
    players_updated = Signal(str) # 玩家数量更新信号
    mod_loaded = Signal(str, str) # mod加载信号(mod_name, mod_id)

    gui_streaming_changed = Signal(bool)   # GUI流式输出状态变化信号
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self.server_path = ""
        self.server_process = None
        self.real_server_pid = None
        self.monitor_thread = None
        self.is_running = False
        self.server_config = DEFAULT_SERVER_CONFIG.copy()
        
        # RCON相关
        self.rcon_client = None
        self.is_rcon_connected = False
        self.current_players = 0
        self.max_players = DEFAULT_SERVER_CONFIG['max_players']
        
        # GUI流式输出控制开关
        self.enable_gui_streaming = False  # 默认关闭GUI流式输出
        
        # 服务器日志显示开关
        self.show_server_logs = False  # 默认关闭服务器日志显示
        
        # RCON自动连接开关
        self.auto_rcon_enabled = False  # 默认关闭RCON自动连接
        
        # 注意：不在初始化时检查已有进程，等待GUI完全加载后再检查
        # self._check_existing_process()  # 移到GUI初始化完成后调用
    
    def set_server_path(self, path):
        """设置服务器路径"""
        self.server_path = path
    
    def set_server_config(self, config):
        """设置服务器配置"""
        self.server_config = config
        # 更新最大玩家数
        if 'max_players' in config:
            self.max_players = config['max_players']
    
    def set_gui_streaming(self, enabled):
        """设置GUI流式输出开关"""
        self.enable_gui_streaming = enabled
        if enabled:
            self.log_message.emit("✅ GUI流式输出已开启")

        else:
            self.log_message.emit("❌ GUI流式输出已关闭，日志仅保存到文件")
    
    def set_server_logs_display(self, enabled):
        """设置服务器日志显示开关"""
        self.show_server_logs = enabled
        if enabled:
            self.log_message.emit("✅ 服务器日志显示已开启，将实时显示WS.log内容")
            # 如果日志监控还没有启动，则启动它
            if not hasattr(self, 'log_monitor_running') or not self.log_monitor_running:
                self._start_log_file_monitor()
        else:
            self.log_message.emit("❌ 服务器日志显示已关闭")
            # 如果服务器没有运行，可以停止日志监控
            if not self.is_running:
                self.log_monitor_running = False
    

    
    def start_server(self):
        """启动服务器"""
        if not self.server_path:
            self.log_message.emit("错误: 请先选择服务器路径！")
            return False
        
        if self.is_running:
            self.log_message.emit("⚠️ 检测到服务器已在运行，无需重复启动")
            return True
        
        self.log_message.emit("🚀 开始启动服务器进程...")
        self.log_message.emit(f"📍 服务器状态: is_running={self.is_running}")
        
        try:
            # 重置启动状态标志
            self.startup_in_progress = True
            
            # 立即锁定状态为启动中，让GUI显示"启动中"
            self.log_message.emit("🔒 服务器状态已锁定为启动中")
            self.status_changed.emit(True)
            
            # 使用正确的服务器可执行文件名
            server_exe = os.path.join(self.server_path, DEFAULT_SERVER_EXE)
            
            # 检查服务器可执行文件是否存在
            if not os.path.exists(server_exe):
                self.log_message.emit(f"错误: 服务器可执行文件不存在: {server_exe}")
                return False
            
            # 构建启动命令 - 按照用户正常工作的命令顺序
            cmd = [
                server_exe,
                "Level01_Main",
                "-server",
                "-log",
                "-UTF8Output",
                f"-MULTIHOME={self.server_config.get('multihome', DEFAULT_SERVER_CONFIG['multihome'])}",
                "-EchoPort=18888",
                "-forcepassthrough",
                f"-PORT={self.server_config.get('port', DEFAULT_SERVER_CONFIG['port'])}",
                f"-MaxPlayers={self.server_config.get('max_players', DEFAULT_SERVER_CONFIG['max_players'])}",
                f"-SteamServerName=\"{self.server_config.get('server_name', DEFAULT_SERVER_CONFIG['server_name'])}\"",
                "-QueryPort=27015"
            ]
            
            # 添加游戏模式参数
            game_mode = self.server_config.get('game_mode', DEFAULT_SERVER_CONFIG['game_mode'])
            cmd.append(f"-{game_mode}")
            
            # 添加额外启动参数（包含gamedistindex和mod等重要参数）
            extra_args = self.server_config.get('extra_args', '')
            if extra_args:
                # 分割额外参数并添加到命令行
                for arg in extra_args.split():
                    cmd.append(arg)
            
            # 添加RCON参数（放在最后，与用户命令顺序一致）
            if self.server_config.get("rcon_enabled", DEFAULT_SERVER_CONFIG['rcon_enabled']):
                cmd.append(f"-rconpsw={self.server_config.get('rcon_password', DEFAULT_SERVER_CONFIG['rcon_password'])}")
                cmd.append(f"-rconport={self.server_config.get('rcon_port', DEFAULT_SERVER_CONFIG['rcon_port'])}")
                cmd.append(f"-rconaddr={self.server_config.get('rcon_addr', DEFAULT_SERVER_CONFIG['rcon_addr'])}")
            
            # 打印完整启动命令到服务器日志区
            cmd_str = ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in cmd)
            self.log_message.emit(f"启动命令: {cmd_str}")
            
            # 启动服务器进程
            self.server_process = subprocess.Popen(
                cmd,
                cwd=self.server_path,
                stdout=None,
                stderr=None,
                creationflags=subprocess.CREATE_NO_WINDOW  # 不显示cmd窗口
            )
            
            self.log_message.emit(f"📋 服务器进程已创建，PID: {self.server_process.pid}")
            self.log_message.emit("⏳ 服务器状态已锁定为启动中，等待进程检测...")
            
            # 注意：这里不设置 is_running = True，等待关键字符串检测
            # self.is_running = True  # 注释掉，等待关键字符串检测
            # 记录启动时间
            self.start_time = datetime.datetime.now()
            
            # 启动后等待一段时间，然后尝试查找真正的服务器进程
            threading.Timer(5.0, self._find_real_server_process).start()
            self.log_message.emit("✅ WSServer.exe进程启动成功，等待WSServer-Win64-Shipping.exe进程...")
            
            # 启动进程监控线程
            threading.Thread(target=self._monitor_process_status, daemon=True).start()
            
            return True
            
        except Exception as e:
            self.log_message.emit(f"启动服务器时出错: {str(e)}")
            self.startup_in_progress = False
            return False
    
    def stop_server(self):
        """停止服务器 - 直接使用RCON关闭，不分状态"""
        self.log_message.emit("正在通过RCON关闭服务器...")
        # 在后台线程中执行关闭操作，避免GUI无响应
        threading.Thread(target=self._stop_server_async, daemon=True).start()
        return True
        
    def _stop_server_async(self):
        """异步停止服务器，避免GUI阻塞 - 统一使用RCON关闭"""
        try:
            import psutil
        except ImportError:
            self.log_message.emit("警告: 未安装psutil模块，部分进程管理功能可能受限")
            return False
        
        # 停止日志监控
        if hasattr(self, 'log_monitor_running'):
            self.log_monitor_running = False
            self.log_message.emit("📋 停止日志文件监控")
        
        # 检查RCON连接状态，如果未连接则尝试连接
        if not self.is_rcon_connected or not self.rcon_client:
            self.log_message.emit("RCON未连接，尝试连接RCON...")
            if not self.connect_rcon():
                self.log_message.emit("❌ RCON连接失败，无法通过RCON关闭服务器")
                self._reset_server_state()
                return False
            self.log_message.emit("✅ RCON连接成功")
        
        # 通过RCON发送关闭命令
        try:
            self.log_message.emit("📤 正在通过RCON发送关闭命令: close 10")
            result = self.execute_rcon_command("close 10")
            self.log_message.emit(f"📥 RCON关闭命令结果: {result}")
            
            # 等待服务器进程结束
            self.log_message.emit("⏳ 等待服务器进程结束...")
            for i in range(30):  # 最多等待30秒
                if not self._check_server_status_with_psutil():
                    # 进程已结束
                    self.log_message.emit(f"✅ 服务器进程已在 {i+1} 秒后正常结束")
                    break
                time.sleep(1)
            else:
                # 超时，进程仍在运行
                self.log_message.emit("⚠️ 服务器未在预期时间内关闭，可能需要手动检查")
            
            # 重置服务器状态
            self._reset_server_state()
            self.log_message.emit("🔴 服务器已停止")
            return True
            
        except Exception as e:
            self.log_message.emit(f"❌ 通过RCON关闭服务器时出错: {str(e)}")
            self._reset_server_state()
            return False
    
    def _reset_server_state(self):
        """重置服务器状态"""
        self.is_running = False
        self.server_process = None
        # 清除启动标志
        if hasattr(self, 'startup_in_progress'):
            self.startup_in_progress = False
        # 断开RCON连接
        if self.is_rcon_connected:
            self.disconnect_rcon()
        # 发送状态更新信号
        self.status_changed.emit(False)
        self.server_stopped.emit()
    
    def reload_server_status(self):
        """重新加载服务器状态 - 重新检测服务器进程"""
        self.log_message.emit("🔄 正在重新加载服务器状态...")
        
        # 重置当前状态
        self.is_running = False
        self.server_process = None
        if hasattr(self, 'real_server_pid'):
            self.real_server_pid = None
        
        # 断开RCON连接
        if self.is_rcon_connected:
            self.disconnect_rcon()
        
        # 重新检测服务器状态
        self._check_existing_process()
        
        self.log_message.emit("✅ 服务器状态重新加载完成")
    
    def restart_server(self):
        """重启服务器"""
        self.log_message.emit("正在重启服务器...")
        
        # 保存当前进程ID，用于后续检查
        old_process_pid = None
        real_server_pid = None
        
        # 获取所有需要关闭的进程PID
        if self.server_process:
            try:
                old_process_pid = self.server_process.pid
            except:
                old_process_pid = None
                
        if hasattr(self, 'real_server_pid') and self.real_server_pid:
            real_server_pid = self.real_server_pid
        
        # 先尝试通过RCON优雅停止
        stop_result = self.stop_server()
        if stop_result:
            self.log_message.emit("服务器已通过RCON停止，等待进程结束...")
        else:
            self.log_message.emit("RCON停止失败，将强制终止进程...")
            # 强制终止进程
            self._force_stop_server_processes()
            
        # 只有在成功停止服务器后才继续
            
        # 创建一个线程来等待进程结束并启动服务器
        def wait_and_start():
            try:
                import psutil
                # 等待所有相关进程结束
                processes_to_wait = []
                if old_process_pid:
                    processes_to_wait.append(old_process_pid)
                if real_server_pid and real_server_pid != old_process_pid:
                    processes_to_wait.append(real_server_pid)
                
                if processes_to_wait:
                    self.log_message.emit(f"等待进程结束: {processes_to_wait}")
                    # 检查进程是否真正结束
                    for _ in range(30):  # 最多等待30秒
                        all_stopped = True
                        for pid in processes_to_wait:
                            try:
                                process = psutil.Process(pid)
                                if process.is_running():
                                    all_stopped = False
                                    break
                            except psutil.NoSuchProcess:
                                # 进程已结束，这是我们想要的
                                continue
                        
                        if all_stopped:
                            self.log_message.emit("✅ 所有服务器进程已完全结束")
                            break
                        time.sleep(1)
                    else:
                        self.log_message.emit("⚠️ 部分进程可能仍在运行，继续启动")
                
                # 等待10秒后启动服务器
                self.log_message.emit("等待10秒后重新启动服务器...")
                time.sleep(10)
                
                # 在主线程中启动服务器
                from PySide6.QtCore import QMetaObject, Qt
                QMetaObject.invokeMethod(self, "_restart_server_impl", 
                                       Qt.QueuedConnection)
            except Exception as e:
                self.log_message.emit(f"等待并启动服务器时出错: {str(e)}")
        
        # 启动等待线程
        threading.Thread(target=wait_and_start, daemon=True).start()
        return True
    
    def _force_stop_server_processes(self):
        """强制终止所有服务器相关进程"""
        try:
            import psutil
            terminated_processes = []
            
            # 终止启动进程
            if self.server_process:
                try:
                    self.server_process.terminate()
                    terminated_processes.append(f"启动进程 PID: {self.server_process.pid}")
                except:
                    pass
            
            # 查找并终止所有WSServer相关进程
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'WSServer' in proc.info['name']:
                        proc.terminate()
                        terminated_processes.append(f"{proc.info['name']} PID: {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if terminated_processes:
                self.log_message.emit(f"已强制终止进程: {', '.join(terminated_processes)}")
            else:
                self.log_message.emit("未找到需要终止的服务器进程")
                
            # 重置状态
            self.is_running = False
            self.server_process = None
            if hasattr(self, 'real_server_pid'):
                delattr(self, 'real_server_pid')
            self.status_changed.emit(False)
            
        except Exception as e:
            self.log_message.emit(f"强制终止进程时出错: {str(e)}")
        
    def _restart_server_impl(self):
        """在主线程中实际启动服务器的实现"""
        try:
            result = self.start_server()
            if result:
                self.log_message.emit("✅ 服务器重启成功")
            else:
                self.log_message.emit("❌ 重启服务器失败")
        except Exception as e:
            self.log_message.emit(f"❌ 重启服务器时出错: {str(e)}")
    
    def _monitor_process_status(self):
        """监控服务器进程状态"""
        if not self.server_process:
            return
        
        try:
            # 启动日志文件监控线程
            self._start_log_file_monitor()
            
            # 在独立线程中等待进程结束
            self.server_process.wait()
            
            # 进程结束
            if self.is_running:
                self.is_running = False
                self.server_process = None
                self.log_message.emit("🔍 [离线判断] 服务器进程已退出")
                self.status_changed.emit(False)
                self.log_message.emit("服务器已停止")
                self.server_stopped.emit()
                
        except Exception as e:
            self.log_message.emit(f"监控服务器进程时出错: {str(e)}")
    
    def connect_rcon(self):
        """连接到RCON服务器"""
        # 如果已经连接，先断开
        if self.is_rcon_connected and self.rcon_client:
            self.log_message.emit("已有RCON连接，先断开...")
            self.disconnect_rcon()
        
        # 移除服务器运行状态检查，允许RCON独立连接
        # 这样用户可以连接到任何支持RCON的服务器，不仅限于本启动器启动的服务器
            
        try:
            # 获取RCON配置
            rcon_addr = self.server_config.get('rcon_addr', DEFAULT_SERVER_CONFIG['rcon_addr'])
            rcon_port = self.server_config.get('rcon_port', DEFAULT_SERVER_CONFIG['rcon_port'])
            rcon_password = self.server_config.get('rcon_password', DEFAULT_SERVER_CONFIG['rcon_password'])
            
            # 检查密码是否为空
            if not rcon_password:
                self.log_message.emit("错误: RCON密码不能为空")
                self.rcon_error.emit("RCON密码不能为空")
                return False
            
            # 创建RCON客户端
            self.rcon_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.rcon_client.settimeout(5)  # 设置超时时间
            
            try:
                # 尝试连接
                self.rcon_client.connect((rcon_addr, int(rcon_port)))
                # TCP连接成功，但还需要进行RCON认证
            except ConnectionRefusedError:
                self.rcon_error.emit("连接被拒绝")
                if self.rcon_client:
                    self.rcon_client.close()
                    self.rcon_client = None
                return False
            except socket.timeout:
                self.rcon_error.emit("连接超时")
                if self.rcon_client:
                    self.rcon_client.close()
                    self.rcon_client = None
                return False
            except socket.gaierror:
                self.rcon_error.emit("地址解析失败")
                if self.rcon_client:
                    self.rcon_client.close()
                    self.rcon_client = None
                return False
            
            # 发送认证请求（不记录密码到日志）
            if not self._send_rcon_packet(3, rcon_password, log_command=False):
                self.rcon_error.emit("发送认证请求失败")
                self.rcon_client.close()
                self.rcon_client = None
                return False
                
            # 接收认证响应
            auth_response = self._receive_rcon_packet()
            
            if not auth_response:
                self.rcon_error.emit("未收到服务器响应")
                self.rcon_client.close()
                self.rcon_client = None
                return False
            
            # 直接根据第一个认证响应判断是否成功，不等待第二个响应包
            # 如果认证响应ID与请求ID匹配，则认证成功
            request_id = 1  # 与_send_rcon_packet中的request_id保持一致
            if auth_response and auth_response['id'] == request_id:
                self.log_message.emit("RCON认证成功，连接已建立")
                self.is_rcon_connected = True
                self.rcon_connected.emit()
                
                # RCON连接验证已完成，无需发送额外命令
                
                # 不再自动启动线程获取玩家数量，改为手动点击"在线玩家"按钮获取
                # threading.Thread(target=self._update_players_count, daemon=True).start()
                
                return True
            else:
                self.rcon_error.emit("认证失败")
                self.rcon_client.close()
                self.rcon_client = None
                return False
                
        except Exception as e:
            # RCON连接错误不记录到日志
            self.rcon_error.emit(str(e))
            if self.rcon_client:
                self.rcon_client.close()
                self.rcon_client = None
            return False
    
    def disconnect_rcon(self):
        """断开RCON连接"""
        if not self.is_rcon_connected or not self.rcon_client:
            return False
            
        try:
            self.rcon_client.close()
            self.rcon_client = None
            self.is_rcon_connected = False
            self.log_message.emit("RCON已断开连接")
            self.rcon_disconnected.emit()
            return True
        except Exception as e:
            return False
    
    def _send_rcon_packet(self, packet_type, payload, timeout=5, log_command=True):
        """发送RCON数据包
        
        Args:
            packet_type (int): 数据包类型，2=命令，3=认证
            payload (str): 数据包载荷，如命令内容或密码
            timeout (int): 发送超时时间，单位为秒
            log_command (bool): 是否记录命令到日志，默认为True
            
        Returns:
            bool: 发送成功返回True，否则返回False
        """
        if not self.rcon_client:
            return False
            
        # 保存原始超时设置
        original_timeout = self.rcon_client.gettimeout()
        
        try:
            # 设置新的超时时间
            self.rcon_client.settimeout(timeout)
            
            # 生成随机请求ID
            request_id = 1  # 简化处理，使用固定ID
            
            # 确保payload是字符串
            if not isinstance(payload, str):
                payload = str(payload)
            
            # 编码payload
            try:
                payload_bytes = payload.encode('utf-8')
                if log_command:
                    self.log_message.emit(f"RCON已发送: {payload}")
            except UnicodeEncodeError as e:
                return False
            
            # 构建数据包
            # 数据包格式: [长度(4)][请求ID(4)][类型(4)][载荷(变长)][0(1)][0(1)]
            # 注意：长度是指从请求ID开始到结尾的长度，不包括长度字段本身
            packet_size = 4 + 4 + len(payload_bytes) + 2  # 4(ID) + 4(类型) + payload长度 + 2(两个结尾空字节)
            packet = struct.pack('<III', packet_size, request_id, packet_type) + payload_bytes + b'\x00\x00'
            
            # 发送数据包
            self.rcon_client.sendall(packet)
            return True
        except socket.timeout:
            # 发送超时
            return False
        except Exception as e:
            # 发送RCON数据包时出错
            return False
        finally:
            # 恢复原始超时设置
            try:
                self.rcon_client.settimeout(original_timeout)
            except:
                pass
    
    def _receive_rcon_packet(self, timeout=5, log_response=True):
        """接收RCON数据包
        
        Args:
            timeout (int): 接收超时时间，单位为秒
            log_response (bool): 是否记录响应到日志，默认为True
            
        Returns:
            dict or None: 解析后的数据包，如果接收失败则返回None
        """
        if not self.rcon_client:
            return None
            
        # 保存原始超时设置
        original_timeout = self.rcon_client.gettimeout()
        
        try:
            # 设置新的超时时间
            self.rcon_client.settimeout(timeout)
            
            # 接收数据包大小
            size_data = self.rcon_client.recv(4)
            if not size_data or len(size_data) < 4:
                return None
                
            packet_size = struct.unpack('<i', size_data)[0]
            
            # 验证数据包大小是否合理，防止恶意数据
            if packet_size < 8 or packet_size > 4096:  # 4KB是一个合理的上限
                return None
            
            # 接收剩余数据
            packet_data = b''
            remaining = packet_size
            
            # 分块接收数据，避免大数据包问题
            while remaining > 0:
                chunk = self.rcon_client.recv(min(remaining, 1024))
                if not chunk:
                    # 连接已关闭
                    return None
                packet_data += chunk
                remaining -= len(chunk)
            
            # 确保接收到足够的数据进行解析
            if len(packet_data) < 8:  # 至少需要ID和类型字段
                return None
            
            # 解析数据包
            response_id = struct.unpack('<I', packet_data[0:4])[0]  # 使用无符号整数格式
            response_type = struct.unpack('<I', packet_data[4:8])[0]  # 使用无符号整数格式
            
            # 解析负载（去除末尾的两个空字节）
            response_body = ""
            if len(packet_data) > 8:
                try:
                    # 直接去除末尾的两个空字节
                    response_body = packet_data[8:-2].decode('utf-8')
                    
                    # 记录响应体（如果需要）
                    if response_body and log_response:
                        # 清理响应中可能包含的表格格式
                        cleaned_response = response_body.strip()
                        self.log_message.emit(f"RCON已接收: {cleaned_response}")
                except UnicodeDecodeError as e:
                    try:
                        # 尝试使用latin-1编码，它可以解码任何字节序列
                        response_body = packet_data[8:-2].decode('latin-1')  # 同样去除末尾两个空字节
                    except Exception:
                        response_body = ""
            
            return {
                'id': response_id,
                'type': response_type,
                'body': response_body
            }
        except socket.timeout:
            # 接收超时
            return None
        except Exception as e:
            # 接收RCON数据包时出错
            return None
        finally:
            # 恢复原始超时设置
            try:
                self.rcon_client.settimeout(original_timeout)
            except:
                pass
    
    def get_players_count(self, log_command=True, log_response=True):
        """通过RCON获取玩家数量
        
        Args:
            log_command (bool): 是否记录发送的命令到日志，默认为True
            log_response (bool): 是否记录接收的响应到日志，默认为True
            
        Returns:
            tuple: (当前玩家数, 最大玩家数)
        """
        if not self.is_rcon_connected or not self.rcon_client:
            # RCON未连接不记录到日志
            return (0, int(self.server_config.get('max_players', DEFAULT_SERVER_CONFIG['max_players'])))
            
        try:
            # 发送lp命令获取在线玩家
            self._send_rcon_packet(2, "lp", log_command=log_command)
            response = self._receive_rcon_packet(log_response=log_response)
            
            if response and response['body']:
                # 解析响应获取玩家数量
                players_info = response['body']
                # 玩家信息不记录到日志
                
                # 计算玩家数量 - 通过表格行数计算
                if '|' in players_info and 'Account' in players_info:
                    lines = players_info.strip().split('\n')
                    # 计算表格中的玩家行数（排除表头和分隔行）
                    player_count = 0
                    for line in lines:
                        if line.strip().startswith('|') and 'Account' not in line and '---' not in line:
                            player_count += 1
                    
                    self.current_players = player_count
                    self.max_players = int(self.server_config.get('max_players', DEFAULT_SERVER_CONFIG['max_players']))
                    return (self.current_players, self.max_players)
                else:
                    # 尝试使用正则表达式解析
                    import re
                    match = re.search(r'\((\d+)/(\d+)\)', players_info)
                    if match:
                        self.current_players = int(match.group(1))
                        self.max_players = int(match.group(2))
                        return (self.current_players, self.max_players)
                    
                    return (0, int(self.server_config.get('max_players', DEFAULT_SERVER_CONFIG['max_players'])))
            else:
                return (0, int(self.server_config.get('max_players', DEFAULT_SERVER_CONFIG['max_players'])))
                
        except Exception as e:
            # 获取玩家数量时出错不记录到日志
            return (0, int(self.server_config.get('max_players', DEFAULT_SERVER_CONFIG['max_players'])))
            
    def get_registered_players(self):
        """通过RCON获取注册玩家列表"""
        if not self.is_rcon_connected or not self.rcon_client:
            # RCON未连接不记录到日志
            return "无法获取注册玩家信息：RCON未连接"
            
        try:
            # 发送lap命令获取注册玩家
            self._send_rcon_packet(2, "lap")
            response = self._receive_rcon_packet()
            
            if response and response['body']:
                return response['body']
            else:
                return "无法获取注册玩家信息：未收到响应"
                
        except Exception as e:
            # 获取注册玩家时出错不记录到日志
            return f"获取注册玩家信息失败：{str(e)}"
    
    def _update_players_count(self):
        """定期更新玩家数量 - 已禁用自动发送lp命令"""
        while self.is_rcon_connected and self.rcon_client:
            try:
                # 不再自动发送lp命令获取玩家数量
                # 仅显示最大玩家数，当前玩家数由在线玩家按钮获取
                max_players = int(self.server_config.get('max_players', DEFAULT_SERVER_CONFIG['max_players']))
                players_count = f"0/{max_players}"
                self.players_updated.emit(players_count)
                time.sleep(30)  # 每30秒更新一次
            except Exception as e:
                # 更新玩家数量时出错不记录到日志
                time.sleep(30)  # 出错后等待30秒再尝试
    

    

    
    def _find_real_server_process(self, attempt_count=1):
        """查找真正的服务器进程PID，找到后立即设置状态为启动中"""
        try:
            import psutil
            # 查找WSServer-Win64-Shipping.exe进程
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name']
                    if proc_name == 'WSServer-Win64-Shipping.exe':
                        real_pid = proc.info['pid']
                        # 不替换self.server_process，保持原始的subprocess.Popen对象用于进程管理
                        # 只记录真实进程的PID用于其他操作
                        self.real_server_pid = real_pid
                        
                        # 更新启动时间为真实进程的创建时间
                        try:
                            real_process = psutil.Process(real_pid)
                            self.start_time = datetime.datetime.fromtimestamp(real_process.create_time())
                            self.log_message.emit(f"🔍 找到WSServer-Win64-Shipping.exe进程 PID: {real_pid}")
                            self.log_message.emit(f"⏰ 更新服务器启动时间为: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        except Exception as e:
                            self.log_message.emit(f"⚠️ 获取进程创建时间失败: {str(e)}，使用当前时间")
                            # 如果获取失败，保持原有的启动时间
                        

                            # 正常流程：等待关键字检测
                            # 保持启动标志为True，等待关键字检测
                            # 不在这里清除startup_in_progress，让它保持启动中状态
                            
                            # 立即设置状态为启动中
                            self.log_message.emit("⏳ 服务器状态锁定为启动中")
                            self.status_changed.emit(True)
                            
                            # 等待关键字检测来设置为在线
                            self.log_message.emit("⏰ 等待检测到关键字'Create Dungeon Successed: DiXiaChengLv50, Index = 2'后设置为在线")
                            
                            # 启动日志文件监控
                            self._start_log_file_monitor()
                        
                        return
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 如果没有找到WSServer-Win64-Shipping.exe进程
            if attempt_count <= 12:  # 最多尝试12次（60秒）
                self.log_message.emit(f"⏳ 第{attempt_count}次尝试：未找到WSServer-Win64-Shipping.exe进程，继续等待...")
                # 5秒后再次尝试查找
                threading.Timer(5.0, lambda: self._find_real_server_process(attempt_count + 1)).start()
            else:
                # 超过12次尝试（60秒）仍未找到进程，判断为启动失败
                self.log_message.emit("🔍 [离线判断] 60秒内未找到WSServer-Win64-Shipping.exe进程，判断为启动失败")
                self.log_message.emit("❌ 服务器启动失败：WSServer-Win64-Shipping.exe进程未启动")
                self.log_message.emit("💡 建议检查服务器配置或查看完整日志排查问题")
                
                # 清除启动标志
                if hasattr(self, 'startup_in_progress'):
                    self.startup_in_progress = False
        except Exception as e:
            self.log_message.emit(f"❌ 查找服务器进程时发生错误: {str(e)}")
            # 清除启动标志
            if hasattr(self, 'startup_in_progress'):
                self.startup_in_progress = False
    
    def _check_server_status_with_psutil(self):
        """使用psutil检查服务器进程状态"""
        try:
            import psutil
            # 检查WSServer-Win64-Shipping.exe进程是否存在
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] == 'WSServer-Win64-Shipping.exe':
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            self.log_message.emit(f"检查进程状态时出错: {str(e)}")
            return False
             
    def _force_kill_server_processes(self):
        """强制终止所有服务器相关进程"""
        try:
            import psutil
            killed_processes = []
            
            # 查找并终止所有WSServer相关进程
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'WSServer' in proc.info['name']:
                        proc.terminate()
                        killed_processes.append(f"{proc.info['name']} (PID: {proc.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            if killed_processes:
                self.log_message.emit(f"强制终止进程: {', '.join(killed_processes)}")
            else:
                self.log_message.emit("未找到需要强制终止的服务器进程")
                
        except Exception as e:
             self.log_message.emit(f"强制终止进程时出错: {str(e)}")
                 
    def _start_log_file_monitor(self):
        """启动日志文件监控线程（等待WSServer-Win64-Shipping.exe进程启动后）"""
        if hasattr(self, 'log_monitor_running') and self.log_monitor_running:
            return  # 避免重复启动
        
        # 等待WSServer-Win64-Shipping.exe进程启动后再开始监控日志
        def wait_for_shipping_process():
            import psutil
            import time
            
            self.log_message.emit("⏳ 等待WSServer-Win64-Shipping.exe进程启动...")
            
            # 最多等待60秒
            for _ in range(60):
                try:
                    # 查找WSServer-Win64-Shipping.exe进程
                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'] == 'WSServer-Win64-Shipping.exe':
                             self.log_message.emit(f"✅ 检测到WSServer-Win64-Shipping.exe进程 PID: {proc.info['pid']}")
                             self.log_message.emit("⏳ 等待10秒后开始监控日志文件...")
                             time.sleep(10)  # 等待10秒
                             self.log_message.emit("🚀 开始监控日志文件")
                             # 启动日志监控
                             if not hasattr(self, 'log_monitor_running') or not self.log_monitor_running:
                                 self.log_monitor_running = True
                                 # 自动开启日志显示
                                 self.show_server_logs = True
                                 threading.Thread(target=self._monitor_server_log_file, daemon=True).start()
                                 self.log_message.emit("📋 启动服务器日志文件监控...")
                                 self.log_message.emit("✅ 自动开启服务器日志显示")
                             return
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
                time.sleep(1)
            
            # 超时后仍然启动日志监控
            self.log_message.emit("⚠️ 等待WSServer-Win64-Shipping.exe进程超时，直接启动日志监控")
            if not hasattr(self, 'log_monitor_running') or not self.log_monitor_running:
                self.log_monitor_running = True
                self.show_server_logs = True
                threading.Thread(target=self._monitor_server_log_file, daemon=True).start()
                self.log_message.emit("📋 启动服务器日志文件监控...")
                self.log_message.emit("✅ 自动开启服务器日志显示")
        
        # 在后台线程中等待
        threading.Thread(target=wait_for_shipping_process, daemon=True).start()
    
    def _monitor_server_log_file(self):
        """监控服务器日志文件WS.log"""
        try:
            # 使用self.server_path而不是从配置中获取
            server_path = self.server_path
            if not server_path:
                self.log_message.emit("❌ 服务器路径未配置，无法监控日志文件")
                return
            
            ws_log_path = os.path.join(server_path, 'WS', 'Saved', 'Logs', 'WS.log')
            self.log_message.emit(f"📋 监控日志文件: {ws_log_path}")
            self.log_message.emit(f"📋 日志显示开关状态: {self.show_server_logs}")
            
            server_started_emitted = False
            last_position = 0
            
            while self.log_monitor_running:
                try:
                    if os.path.exists(ws_log_path):
                        # 使用非阻塞方式读取文件，避免锁定
                        new_lines = []
                        try:
                            # 快速读取文件内容，立即关闭以避免锁定
                            with open(ws_log_path, 'r', encoding='utf-8', errors='ignore') as temp_f:
                                temp_f.seek(last_position)
                                file_content = temp_f.read()
                                new_position = temp_f.tell()
                            
                            # 处理读取的内容
                            if file_content:
                                new_lines = file_content.splitlines(keepends=True)
                                last_position = new_position
                        except (PermissionError, IOError) as e:
                            # 如果文件被锁定，跳过这次读取
                            time.sleep(0.1)
                            continue
                        except Exception as e:
                            # 其他错误，跳过这次读取
                            continue
                        
                        # 处理读取到的新行
                        if new_lines:
                            for line in new_lines:
                                line_text = line.strip()
                                if line_text:
                                    # 如果启用了服务器日志显示开关，输出日志内容到GUI
                                    if self.show_server_logs:
                                        self.log_message.emit(f"[WS.log] {line_text}")
                                    
                                    # 检测MOD加载日志
                                    import re
                                    mod_pattern = r'LogUGCRegistry: Display: LoadModulesForEnabledPluginsBegin: ModName:([^,]+), ModID:(\d+)\.?'
                                    mod_match = re.search(mod_pattern, line_text)
                                    if mod_match:
                                        mod_name = mod_match.group(1).strip()
                                        mod_id = mod_match.group(2).strip()
                                        self.mod_loaded.emit(mod_name, mod_id)
                                        self.log_message.emit(f"🔧 检测到MOD加载: {mod_name} (ID: {mod_id})")
                                    
                                    # 检测服务器启动完成关键字符串（仅在启动过程中检测，已有进程时跳过）
                                    if (not server_started_emitted and 
                                        hasattr(self, 'startup_in_progress') and self.startup_in_progress and 
                                        'Create Dungeon Successed: DiXiaChengLv50, Index = 2' in line_text):
                                        self.log_message.emit("✅ 从WS.log检测到服务器启动完成信号：Create Dungeon Successed: DiXiaChengLv50, Index = 2")
                                        
                                        # 清除启动标志，设置为正式在线状态
                                        if hasattr(self, 'startup_in_progress'):
                                            self.startup_in_progress = False
                                        
                                        self.is_running = True
                                        self.status_changed.emit(True)
                                        self.server_started.emit()
                                        server_started_emitted = True
                                        self.log_message.emit("🎉 服务器已正式上线！")
                                        
                                        # 启动完成后，尝试连接RCON
                                        self._auto_connect_rcon_after_startup()
                                        break
                    else:
                        # 文件不存在时的调试信息，每10秒提示一次
                        if self.show_server_logs and int(time.time()) % 10 == 0:
                            self.log_message.emit(f"⚠️ WS.log文件不存在: {ws_log_path}")
                            # 检查服务器路径是否存在
                            ws_dir = os.path.join(server_path, 'WS')
                            if not os.path.exists(ws_dir):
                                self.log_message.emit(f"⚠️ 服务器WS目录不存在: {ws_dir}")
                            else:
                                saved_dir = os.path.join(ws_dir, 'Saved')
                                if not os.path.exists(saved_dir):
                                    self.log_message.emit(f"⚠️ 服务器Saved目录不存在: {saved_dir}")
                                else:
                                    logs_dir = os.path.join(saved_dir, 'Logs')
                                    if not os.path.exists(logs_dir):
                                        self.log_message.emit(f"⚠️ 服务器Logs目录不存在: {logs_dir}")
                    
                    time.sleep(1)  # 每秒检查一次
                    
                except Exception as e:
                    self.log_message.emit(f"读取WS.log文件时出错: {str(e)}")
                    time.sleep(5)  # 出错时等待5秒再重试
                    
        except Exception as e:
            self.log_message.emit(f"监控WS.log文件时出错: {str(e)}")
        finally:
            self.log_monitor_running = False
    
    def set_auto_rcon_enabled(self, enabled):
        """设置RCON自动连接开关"""
        self.auto_rcon_enabled = enabled
        if enabled:
            self.log_message.emit("✅ RCON自动连接已开启，服务器启动完成后将自动连接")
        else:
            self.log_message.emit("❌ RCON自动连接已关闭，需要手动连接")
    
    def _auto_connect_rcon_after_startup(self):
        """服务器启动完成后自动连接RCON"""
        if self.auto_rcon_enabled and self.server_config.get("rcon_enabled", DEFAULT_SERVER_CONFIG['rcon_enabled']):
            self.log_message.emit("🔗 服务器在线，尝试自动连接RCON...")
            threading.Timer(3.0, self._auto_connect_rcon).start()
        else:
            if not self.auto_rcon_enabled:
                self.log_message.emit("ℹ️ RCON自动连接已关闭，请手动连接")
            else:
                self.log_message.emit("ℹ️ RCON未启用，无法自动连接")
    
    def _auto_connect_rcon(self):
        """自动连接RCON（在服务器启动完成后调用）"""
        try:
            if self.connect_rcon():
                self.log_message.emit("🎉 RCON自动连接成功")
            else:
                self.log_message.emit("⚠️ RCON自动连接失败，请手动连接")
        except Exception as e:
            self.log_message.emit(f"⚠️ RCON自动连接出错: {str(e)}")
    
    def _check_existing_process(self, silent_mode=False):
        """检查是否有已存在的服务器进程（仅监控 WSServer-Win64-Shipping.exe）
        
        Args:
            silent_mode (bool): 静默模式，不输出"检测到已有进程"相关日志
        """
        try:
            import psutil
            shipping_pid = None
            
            # 查找服务器进程
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name']
                    if proc_name == 'WSServer-Win64-Shipping.exe':
                        shipping_pid = proc.info['pid']
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 检查服务器进程状态
            if shipping_pid:
                # 服务器进程存在，直接设置为在线状态
                process = psutil.Process(shipping_pid)
                self.real_server_pid = shipping_pid
                self.is_running = True  # 直接设置为在线状态
                self.start_time = datetime.datetime.fromtimestamp(process.create_time())
                
                if not silent_mode:
                    self.log_message.emit("🔍 检测到已有进程，准备加载...")
                    self.log_message.emit(f"   - WSServer-Win64-Shipping.exe PID: {shipping_pid}")
                    self.log_message.emit("✅ 加载成功")
                    self.log_message.emit("✅ 服务器状态：在线（检测到已有进程）")
                
                # 发射 status_changed(True) 信号，让GUI显示"在线"状态
                self.status_changed.emit(True)
                # 发射服务器启动信号
                self.server_started.emit()
                
                # 启动持续日志监控
                threading.Thread(target=self._monitor_existing_process_logs, daemon=True).start()
                
                # 启动WS.log文件监控来读取mod信息
                self.log_monitor_running = True
                threading.Thread(target=self._monitor_server_log_file, daemon=True).start()
                
                if not silent_mode:
                    # 检测到已有进程时，不自动尝试连接RCON，避免在RCON未启动时显示连接成功
                    # 用户可以手动点击连接RCON按钮进行连接
                    self.log_message.emit("💡 检测到已运行的服务器，如需使用RCON功能请手动连接")
            else:
                # 检查是否正在启动过程中，如果是则不发送离线信号
                if hasattr(self, 'startup_in_progress') and self.startup_in_progress:
                    self.log_message.emit("🔍 启动过程中暂未找到WSServer-Win64-Shipping.exe进程，继续等待...")
                    return
                
                # 没有找到服务器进程且不在启动过程中
                if not silent_mode:
                    self.log_message.emit("🔍 [离线判断] 检查现有进程时未找到WSServer-Win64-Shipping.exe进程")
                    self.log_message.emit("❌ 未检测到服务器进程，状态：离线")
                self.is_running = False
                self.status_changed.emit(False)
                return
        except Exception as e:
            # 检查服务器进程失败，但不记录日志避免创建logs目录
            pass
    
    def _monitor_existing_process_logs(self):
        """监控已存在进程的日志输出（仅监控 WSServer-Win64-Shipping.exe）"""
        try:
            import os
            import time
            from datetime import datetime
            
            # 创建专门的监控日志文件
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
            monitor_log = os.path.join(log_dir, "process_monitor.log")
            os.makedirs(log_dir, exist_ok=True)
            
            with open(monitor_log, 'a', encoding='utf-8') as log_file:
                log_file.write(f"\n=== 开始监控已存在进程（仅监控 WSServer-Win64-Shipping.exe） {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                log_file.flush()
                
                # 持续监控服务器进程状态
                import psutil
                while True:
                    try:
                        shipping_running = False
                        
                        # 检查服务器进程是否在运行
                        for proc in psutil.process_iter(['pid', 'name']):
                            try:
                                proc_name = proc.info['name']
                                if proc_name == 'WSServer-Win64-Shipping.exe':
                                    shipping_running = True
                                    break
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                        
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        log_file.write(f"[{timestamp}] [MONITOR] WSServer-Win64-Shipping.exe: {'运行' if shipping_running else '停止'}\n")
                        log_file.flush()
                        
                        # 根据服务器进程状态更新服务器状态
                        if shipping_running:
                            # 进程重新出现，清理宽容期标记
                            if hasattr(self, 'process_missing_start_time'):
                                self.log_message.emit("✅ WSServer-Win64-Shipping.exe进程已恢复，取消宽容期")
                                delattr(self, 'process_missing_start_time')
                            
                            # 服务器进程在运行，但不自动设置为在线
                            # 只有通过关键字符串检测才能设置为在线状态
                            if not self.is_running:
                                # 只有在真正启动过程中才显示启动计时和超时检查
                                if hasattr(self, 'startup_in_progress') and self.startup_in_progress and hasattr(self, 'start_time'):
                                    running_time = datetime.now() - self.start_time.replace(tzinfo=None)
                                    # 如果超过10分钟仍未检测到启动关键字，则认为启动失败
                                    if running_time.total_seconds() > 600:  # 10分钟 = 600秒
                                        self.log_message.emit("❌ 服务器启动超时（10分钟），未检测到启动完成信号，启动失败")
                                        self.log_message.emit("💡 建议检查服务器配置或查看完整日志排查问题")
                                        # 设置为离线状态
                                        self.log_message.emit("🔍 [离线判断] 服务器启动超时（超过10分钟未检测到启动完成）")
                                        
                                        # 清除启动标志
                                        self.startup_in_progress = False
                                        
                                        self.is_running = False
                                        self.status_changed.emit(False)
                                        log_file.write(f"[{timestamp}] [MONITOR] 服务器启动超时，设置为离线状态\n")
                                        log_file.flush()
                                        break  # 退出监控循环
                                    else:
                                        # 仍在等待启动完成，保持启动中状态
                                        elapsed_minutes = int(running_time.total_seconds() // 60)
                                        if elapsed_minutes > 0 and running_time.total_seconds() % 60 < 5:  # 每分钟提示一次
                                            self.log_message.emit(f"⏳ 服务器启动中...已等待 {elapsed_minutes} 分钟，最多等待10分钟")
                        else:
                            # 服务器进程缺失 - 增加宽容期，避免误判
                            if self.is_running:
                                # 检查是否已经记录了进程缺失的时间
                                if not hasattr(self, 'process_missing_start_time'):
                                    self.process_missing_start_time = datetime.now()
                                    self.log_message.emit("⚠️ 检测到WSServer-Win64-Shipping.exe进程缺失，开始30秒宽容期...")
                                    log_file.write(f"[{timestamp}] [MONITOR] 进程缺失，开始宽容期\n")
                                    log_file.flush()
                                else:
                                    # 检查宽容期是否已过
                                    missing_duration = datetime.now() - self.process_missing_start_time
                                    if missing_duration.total_seconds() > 30:  # 30秒宽容期
                                        self.log_message.emit("🔍 [离线判断] WSServer-Win64-Shipping.exe进程缺失超过30秒，判断为服务器停止")
                                        self.log_message.emit(f"❌ 服务器进程已停止")
                                        self.log_message.emit("💡 如果服务器仍在运行但进程名不同，请检查服务器配置")
                                        self.is_running = False
                                        self.status_changed.emit(False)
                                        log_file.write(f"[{timestamp}] [MONITOR] 进程缺失超过宽容期，设置为离线\n")
                                        log_file.flush()
                                        # 清理宽容期标记
                                        if hasattr(self, 'process_missing_start_time'):
                                            delattr(self, 'process_missing_start_time')
                                        break
                                    else:
                                        # 仍在宽容期内
                                        remaining_seconds = 30 - int(missing_duration.total_seconds())
                                        if int(missing_duration.total_seconds()) % 10 == 0:  # 每10秒提示一次
                                            self.log_message.emit(f"⏳ 进程缺失宽容期：还有 {remaining_seconds} 秒")
                            else:
                                # 服务器本来就不在运行状态，清理宽容期标记
                                if hasattr(self, 'process_missing_start_time'):
                                    delattr(self, 'process_missing_start_time')
                        
                        time.sleep(5)  # 每5秒检查一次
                        
                    except Exception as e:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        log_file.write(f"[{timestamp}] [MONITOR] 监控出错: {str(e)}\n")
                        log_file.flush()
                        time.sleep(5)
                
                log_file.write(f"=== 监控结束 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                
        except Exception as e:
            self.log_message.emit(f"监控已存在进程时出错: {str(e)}")
    
    # 已删除 _monitor_server_log_file 方法，改用日志文件监控
    
    def get_server_status(self):
        """获取服务器状态"""
        # 检查是否正在启动中
        is_starting = hasattr(self, 'startup_in_progress') and self.startup_in_progress
        
        status = {
            'running': self.is_running,
            'starting': is_starting,  # 添加启动中状态
            'process': self.server_process is not None,
            'path': self.server_path,
            'rcon_connected': self.is_rcon_connected
        }
        
        # 如果服务器正在运行，添加更多状态信息
        if self.is_running:
            # 计算运行时间
            if hasattr(self, 'start_time') and self.start_time:
                try:
                    # 确保时间计算正确，处理时区问题
                    current_time = datetime.datetime.now()
                    start_time = self.start_time
                    
                    # 如果start_time有时区信息，移除它
                    if hasattr(start_time, 'tzinfo') and start_time.tzinfo is not None:
                        start_time = start_time.replace(tzinfo=None)
                    
                    uptime_seconds = int((current_time - start_time).total_seconds())
                    
                    # 确保运行时间不为负数
                    if uptime_seconds < 0:
                        uptime_seconds = 0
                    
                    hours, remainder = divmod(uptime_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    status['uptime'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                except Exception as e:
                    # 如果计算出错，显示错误信息
                    status['uptime'] = "计算错误"
            else:
                status['uptime'] = "--:--:--"
                
            # 获取在线玩家数量
            # 不再自动通过RCON获取玩家数量，避免频繁发送lp命令
            # 使用保存的玩家数量或默认值
            if hasattr(self, 'current_players') and hasattr(self, 'max_players'):
                status['players'] = f"{self.current_players}/{self.max_players}"
            else:
                # 使用配置中的最大玩家数
                try:
                    max_players = self.server_config.get('max_players', DEFAULT_SERVER_CONFIG['max_players'])
                    # 使用默认值
                    current_players = 0
                    status['players'] = f"{current_players}/{max_players}"
                except Exception as e:
                    self.log_message.emit(f"获取玩家数量时出错: {str(e)}")
                    status['players'] = "0/0"
            
            # 获取内存使用情况
            try:
                import psutil
                # 优先使用真实服务器进程PID，如果没有则使用启动进程PID
                target_pid = getattr(self, 'real_server_pid', None) or (self.server_process.pid if self.server_process else None)
                
                if target_pid:
                    try:
                        process = psutil.Process(target_pid)
                        # 检查进程是否仍然存在且正在运行
                        if process.is_running():
                            memory_info = process.memory_info()
                            memory_mb = memory_info.rss / 1024 / 1024  # 转换为MB
                            status['memory'] = f"{memory_mb:.2f} MB"
                            status['memory_percent'] = min(int((memory_mb / 1000) * 100), 100)  # 假设最大内存为1000MB，确保不超过100%
                        else:
                            # 进程已停止
                            status['memory'] = "-- MB"
                            status['memory_percent'] = 0
                    except psutil.NoSuchProcess:
                        # 进程不存在
                        status['memory'] = "-- MB"
                        status['memory_percent'] = 0
                    except psutil.AccessDenied:
                        # 权限不足
                        status['memory'] = "权限不足"
                        status['memory_percent'] = 0
                    except Exception as e:
                        # 其他异常
                        status['memory'] = f"错误: {str(e)[:20]}"
                        status['memory_percent'] = 0
                else:
                    status['memory'] = "-- MB"
                    status['memory_percent'] = 0
            except ImportError:
                # psutil未安装
                status['memory'] = "-- MB"
                status['memory_percent'] = 0
            except Exception:
                # 其他异常
                status['memory'] = "-- MB"
                status['memory_percent'] = 0
        else:
            status['uptime'] = "--:--:--"
            status['players'] = "--"
            status['memory'] = "-- MB"
            status['memory_percent'] = 0
            
        return status
    

    
    def execute_rcon_command(self, command, log_command=True, log_response=True):
        """执行RCON命令并返回结果
        
        Args:
            command (str): 要执行的RCON命令
            log_command (bool): 是否记录发送的命令到日志，默认为True
            log_response (bool): 是否记录接收的响应到日志，默认为True
            
        Returns:
            str: 命令执行结果或错误信息
        """
        if not self.is_rcon_connected or not self.rcon_client:
            return "错误: RCON未连接"
            
        try:
            # 发送命令
            if log_command:
                self.log_message.emit(f"RCON已发送: {command}")
            self._send_rcon_packet(2, command, log_command=False)  # 避免重复日志输出
            response = self._receive_rcon_packet(log_response=log_response)
            
            if response:
                # 处理响应内容，确保返回正确的命令结果
                response_body = response['body'].strip()
                
                # 直接返回服务器的响应，不进行特殊处理
                # 这样用户输入的命令会直接发送到服务器，并显示服务器返回的原始响应
                
                return response_body
            else:
                return "命令执行失败，未收到响应"
                
        except Exception as e:
            return f"错误: {str(e)}"
    
    def get_online_players(self):
        """获取在线玩家列表（GUI调用的方法）"""
        if not self.is_rcon_connected:
            return []
        
        try:
            # 使用RCON命令获取玩家列表，不记录到服务器日志区
            response = self.execute_rcon_command("lp", log_command=False, log_response=False)
            if response and "错误" not in response:
                # 解析玩家列表响应，不输出调试信息到服务器日志区
                players = []
                lines = response.split('\n')
                for i, line in enumerate(lines):
                    line = line.strip()
                    # 跳过空行、表头行和分隔行
                    if (line and '|' in line and 
                        not 'Account' in line and 
                        not 'PlayerName' in line and
                        not line.replace('|', '').replace('-', '').replace(' ', '').strip() == ''):
                        # 解析玩家信息行
                        parts = [part.strip() for part in line.split('|')]
                        # 过滤掉空的parts
                        parts = [part for part in parts if part]
                        if len(parts) >= 4:  # 确保有足够的字段
                            # 根据RCON响应格式: | Account | PlayerName | PawnID | Position |
                            # 过滤空parts后: [Account, PlayerName, PawnID, Position]
                            account_id = parts[0].strip()
                            player_name = parts[1].strip().strip("'\"")
                            pawn_id = parts[2].strip() if len(parts) > 2 else ''
                            position = parts[3].strip() if len(parts) > 3 else ''
                            # 确保玩家名称不为空
                            if player_name and account_id:
                                player_info = {
                                    'name': player_name,  # PlayerName (真正的玩家名)
                                    'account_id': account_id, # Account ID
                                    'pawn_id': pawn_id,  # PawnID
                                    'status': 'online'  # 在线状态
                                }
                                players.append(player_info)
                return players
            else:
                return []
        except Exception as e:
            # 获取玩家列表失败时不记录到服务器日志区
            return []