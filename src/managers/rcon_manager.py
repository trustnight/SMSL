# -*- coding: utf-8 -*-

"""
RCON管理器 - 负责RCON连接和命令执行
"""

import socket
import struct
import threading
import time
from PySide6.QtCore import QObject, Signal
from ..common.constants import DEFAULT_RCON_PORT, DEFAULT_RCON_PASSWORD, RCON_TIMEOUT
from ..common.utils import validate_ip_address, validate_port


class RconManager(QObject):
    """RCON管理器类"""
    
    # 信号定义
    connection_status_changed = Signal(bool)  # 连接状态变化
    command_result = Signal(str)  # 命令执行结果
    error_occurred = Signal(str)  # 错误信息
    
    def __init__(self):
        super().__init__()
        self.host = "127.0.0.1"
        self.port = DEFAULT_RCON_PORT
        self.password = DEFAULT_RCON_PASSWORD
        self.socket = None
        self.connected = False
        self.request_id = 1
        
    def set_connection_info(self, host, port, password):
        """设置连接信息"""
        if not validate_ip_address(host):
            self.error_occurred.emit(f"无效的IP地址: {host}")
            return False
            
        if not validate_port(port):
            self.error_occurred.emit(f"无效的端口号: {port}")
            return False
            
        self.host = host
        self.port = int(port)
        self.password = password
        return True
        
    def connect(self):
        """连接到RCON服务器"""
        try:
            if self.connected:
                self.disconnect()
                
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(RCON_TIMEOUT)
            self.socket.connect((self.host, self.port))
            
            # 发送认证请求
            if self._authenticate():
                self.connected = True
                self.connection_status_changed.emit(True)
                return True
            else:
                self.disconnect()
                self.error_occurred.emit("RCON认证失败")
                return False
                
        except socket.timeout:
            self.error_occurred.emit("连接超时")
            return False
        except ConnectionRefusedError:
            self.error_occurred.emit("连接被拒绝，请检查服务器是否启动")
            return False
        except Exception as e:
            self.error_occurred.emit(f"连接失败: {str(e)}")
            return False
            
    def disconnect(self):
        """断开RCON连接"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            
        if self.connected:
            self.connected = False
            self.connection_status_changed.emit(False)
            
    def send_command(self, command):
        """发送RCON命令"""
        if not self.connected:
            self.error_occurred.emit("未连接到RCON服务器")
            return False
            
        try:
            response = self._send_packet(2, command)  # 2 = SERVERDATA_EXECCOMMAND
            if response:
                self.command_result.emit(response)
                return True
            else:
                self.error_occurred.emit("命令执行失败")
                return False
                
        except Exception as e:
            self.error_occurred.emit(f"发送命令失败: {str(e)}")
            return False
            
    def _authenticate(self):
        """RCON认证"""
        try:
            response = self._send_packet(3, self.password)  # 3 = SERVERDATA_AUTH
            return response is not None
        except:
            return False
            
    def _send_packet(self, packet_type, data):
        """发送RCON数据包"""
        if not self.socket:
            return None
            
        # 构建数据包
        request_id = self.request_id
        self.request_id += 1
        
        # 数据包格式: Size(4) + ID(4) + Type(4) + Body(N) + Null(2)
        body = data.encode('utf-8') + b'\x00\x00'
        packet_size = 4 + 4 + len(body)  # ID + Type + Body
        
        packet = struct.pack('<i', packet_size)
        packet += struct.pack('<i', request_id)
        packet += struct.pack('<i', packet_type)
        packet += body
        
        try:
            self.socket.send(packet)
            return self._receive_packet()
        except Exception as e:
            raise e
            
    def _receive_packet(self):
        """接收RCON响应数据包"""
        try:
            # 读取数据包大小
            size_data = self.socket.recv(4)
            if len(size_data) < 4:
                return None
                
            packet_size = struct.unpack('<i', size_data)[0]
            
            # 读取完整数据包
            packet_data = b''
            while len(packet_data) < packet_size:
                chunk = self.socket.recv(packet_size - len(packet_data))
                if not chunk:
                    return None
                packet_data += chunk
                
            # 解析数据包
            if len(packet_data) >= 8:
                response_id = struct.unpack('<i', packet_data[0:4])[0]
                response_type = struct.unpack('<i', packet_data[4:8])[0]
                response_body = packet_data[8:-2].decode('utf-8', errors='ignore')
                
                # 认证响应检查
                if response_type == 2 and response_id == -1:
                    return None  # 认证失败
                    
                return response_body
                
        except Exception:
            return None
            
    def is_connected(self):
        """检查是否已连接"""
        return self.connected
        
    def get_connection_info(self):
        """获取连接信息"""
        return {
            'host': self.host,
            'port': self.port,
            'password': self.password,
            'connected': self.connected
        }
        
    def get_common_commands(self):
        """获取常用RCON命令列表"""
        return [
            "help",
            "list",
            "kick <player>",
            "ban <player>",
            "unban <player>",
            "save",
            "stop",
            "say <message>",
            "weather <type>",
            "time <value>"
        ]