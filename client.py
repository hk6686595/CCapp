import socket
import threading
import schedule
import time
import subprocess
import ctypes
import os
from logger_config import setup_logger
from system_info import get_project_name, get_system_info, load_config

logger = setup_logger('client', 'client')

class Client:
    def __init__(self):
        self.config = load_config()
        self.host = self.config.get('server_ip', 'localhost')
        self.port = self.config.get('server_port', 5000)
        self.client_socket = None
        self.connected = False
        self.running = True
        self.client_ip = None
        self.project_name = get_project_name()
        self.shutdown_scheduled = False

        logger.info(f"已加载配置: 服务器 IP {self.host}, 端口 {self.port}, pssoft路径 {self.config.get('pssoft_path', 'D:\\pssoft')}")
        print(f"已加载配置: 服务器 IP {self.host}, 端口 {self.port}, pssoft路径 {self.config.get('pssoft_path', 'D:\\pssoft')}")

    def connect(self):
        while self.running and not self.connected:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.host, self.port))
                self.connected = True
                self.client_ip = self.client_socket.getsockname()[0]  # 获取客户端IP
                logger.info(f"成功连接到服务器，客户端IP: {self.client_ip}")
                print(f"成功连接到服务器，客户端IP: {self.client_ip}")
                
                receive_thread = threading.Thread(target=self.receive_messages)
                receive_thread.start()

                # 设置定时任务，每60秒发送一次状态信息
                schedule.every(30).seconds.do(self.send_status)
            except Exception as e:
                logger.error(f"连接失败: {e}")
                print(f"连接失败: {e}")
                print("5秒后重试...")
                time.sleep(5)

    def receive_messages(self):
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    raise Exception("连接已关闭")
                print('recv from server raw msg :',message)
                
                # 处理特殊指令
                self.handle_command(message)
            except Exception as e:
                logger.error(f"接收消息时出错: {e}")
                print(f"接收消息时出错: {e}")
                self.connected = False
                self.reconnect()
                break

    def handle_command(self, action):
        if action == "shutdown":
            logger.info("收到关机指令，系统将在60秒后关机...")
            print("收到关机指令，系统将在60秒后关机...")
            self.shutdown_scheduled = True
            subprocess.run(["shutdown", "/s", "/t", "60"])
        elif action == "reboot":
                    logger.info("收到重启指令，系统将在60秒后重启...")
                    print("收到重启指令，系统将在60秒后重启...")
                    self.shutdown_scheduled = True
                    subprocess.run(["shutdown", "/r", "/t", "60"])
        elif action == "sleep":
                    logger.info("收到锁屏指令，系统将立即锁屏...")
                    print("收到锁屏指令，系统将立即锁屏...")
                    ctypes.windll.user32.LockWorkStation()
        elif action == "cancel":
                    if self.shutdown_scheduled:
                        logger.info("取消关机/重启指令...")
                        print("取消关机/重启指令...")
                        subprocess.run(["shutdown", "/a"])
                        self.shutdown_scheduled = False
                    else:
                        logger.info("没有待执行的关机/重启指令")
                        print("没有待执行的关机/重启指令")
        elif action == "get":
                    logger.info("收到get指令，立即发送状态信息...")
                    print("收到get指令，立即发送状态信息...")
                    self.send_status()
        elif action == "test":
                    logger.info("收到test指令，立即响应...")
                    print("收到test指令，立即响应...")
                    self.send_message("OK")
        elif action == "hello":
                    logger.info("收到hello指令，立即响应...")
                    print("收到hello指令，立即响应...")
                    self.send_message("OK") 
        else:
            logger.info(f"收到未知指令: {action}")
            print(f"收到未知指令: {action}")

    def reconnect(self):
        logger.info("尝试重新连接...")
        print("尝试重新连接...")
        self.connect()

    def send_message(self, message):
        if self.connected:
            try:
                self.client_socket.send(message.encode('utf-8'))
            except Exception as e:
                logger.error(f"发送消息时出错: {e}")
                print(f"发送消息时出错: {e}")
                self.connected = False
                self.reconnect()

    def get_project_name(self):
        return get_project_name()

    def get_system_info(self):
        return get_system_info(self.client_ip, self.project_name)

    def send_status(self):
        status_info = self.get_system_info()
        logger.info(f"发送状态信息: {status_info}")
        print(f"发送状态信息: {status_info}")
        self.send_message(f"状态信息: {status_info}")


    def run(self):
        self.connect()
        self.send_status()
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def stop(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()
        logger.info("客户端已停止")

if __name__ == "__main__":
    client = Client()
    try:
        client.run()
    except KeyboardInterrupt:
        logger.info("正在关闭客户端...")
        print("正在关闭客户端...")
        client.stop()
