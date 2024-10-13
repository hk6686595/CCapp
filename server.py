import socket
import threading
import json
import time
import logging
import datetime
from logging.handlers import RotatingFileHandler
from network_utils import ping_test
from logger_config import setup_logger
import os
# 配置日志


# 创建日志记录器
logger = setup_logger('server', 'server')

class ControlServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.running = False
        self.client_info = {}  # 用于存储客户端信息的字典
        self.last_seen = {}  # 用于记录客户端最后一次发送消息的时间
        self.client_log_dir = 'clientlog'
        if not os.path.exists(self.client_log_dir):
            os.makedirs(self.client_log_dir)
        self.client_sockets = {}  # 用于存储客户端 IP 和对应的 socket

        # 加载配置文件
        self.load_client_info()

    def load_client_info(self):
        # 从文件加载客户端信息
        try:
            with open('Proj_Ip_table.json', 'r') as f:
                self.client_info = json.load(f)
            
            print("客户端信息已从 Proj_Ip_table.json 加载")
            print(self.client_info)
        except FileNotFoundError:
            print("未找到 Proj_Ip_table.json 文件，使用空的客户端信息")
        except json.JSONDecodeError:
            print("Proj_Ip_table.json 文件格式错误，使用空的客户端信息")

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        logger.info(f"服务器正在监听 {self.host}:{self.port}")
        print(f"服务器正在监听 {self.host}:{self.port}")
        self.running = True

        accept_thread = threading.Thread(target=self.accept_clients)
        accept_thread.start()

    def accept_clients(self):
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"新客户端连接: {addr}")
                self.clients.append(client_socket)
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.start()
            except:
                break

    def handle_client(self, client_socket):
        client_address = client_socket.getpeername()[0]
        logger.info(f"新客户端连接: {client_address}")
        self.client_sockets[client_address] = client_socket  # 存储客户端 socket
        while self.running:
            try:
                data = client_socket.recv(4096)  # 增加接收缓冲区大小
                if not data:
                    break
                try:
                    message = data.decode('utf-8')
                    logger.info(f"收到数据: {message}")
                    if message.startswith("状态信息:"):
                        info = message[5:].strip()
                        self.parse_and_save_client_info(info)
                    
                    self.last_seen[client_address] = time.time()
                    # self.broadcast(f"收到")
                except UnicodeDecodeError:
                    # 如果无法解码，可能是日志文件的开始部分
                    print('开始接收日志（检测到二进制数据）')
        
                        
            except Exception as e:
                logger.error(f"Client {client_address} 异常退出: {e}")
                print(f"Client {client_address} 异常退出: {e}")
                break
        
        del self.client_sockets[client_address]  # 移除断开连接的客户端
        self.clients.remove(client_socket)
        client_socket.close()

    def parse_and_save_client_info(self, info):
        # 解析客户端发送的信息
        info_parts = info.split(', ')
        ip = None
        project_name = None
        for part in info_parts:
            if part.startswith("IP:"):
                ip = part.split(': ')[1]
            elif part.startswith("项目名称:"):
                project_name = part.split(': ')[1]
        
        # 保存或更新客户端信息
        if ip and project_name:
            self.client_info[project_name+'@'+ip] = {
                'ip': ip,
                'project_name': project_name
            }

    def broadcast(self, message):
        for client in self.clients[:]:  # 使用列表的副本进行迭代
            try:
                client.send(message.encode('utf-8'))
            except Exception as e:
                print(f"向客户端发送消息时出错: {e}")
                self.clients.remove(client)

    def send_command(self, command):
        self.broadcast(f"命令: {command}")

    def stop(self):
        self.running = False
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        try:
            self.server_socket.shutdown(socket.SHUT_RDWR)
            self.server_socket.close()
        except:
            pass
        logger.info("服务器已停止")
        print("服务器已停止")

    def save_client_info(self):
        # 将客户端信息保存到文件
        with open('Proj_Ip_table.json', 'w') as f:
            json.dump(self.client_info, f, indent=4)
        print("客户端信息已保存到 Proj_Ip_table.json")

    def test_client_online(self, ip):
        if ip in self.last_seen:
            last_seen_time = self.last_seen[ip]
            if time.time() - last_seen_time < 10:  # 10秒内有消息则认为在线
                print(f"设备 {ip} 在线")
                return True
            else:
                print(f"设备 {ip} 离线")
                return False
        else:
            print(f"未找到设备 {ip} 的记录")
            return False

    def ping_test(self, ip):
        result = ping_test(ip)
        logger.info(f"Ping 测试: 设备 {ip} {'在线' if result else '离线'}")
        print(f"Ping 测试: 设备 {ip} {'在线' if result else '离线'}")

    def show_clients(self):
        print("\n当前客户端信息:")
        print("--------------------")
        for info in self.client_info.values():
            last_seen = self.last_seen.get(info['ip'], 0)
            online = "在线√" if time.time() - last_seen < 10 else "离线×"  # 10秒内有消息则认为在线
            print(f"IP地址: {info['ip']}")
            print(f"展品名称: {info['project_name']}")
            print(f"状态: {online}")
            print("--------------------")

    def save_client_log(self, client_address, log_content):
        log_filename = f"{client_address}_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
        log_path = os.path.join(self.client_log_dir, log_filename)
        with open(log_path, 'wb') as log_file:
            log_file.write(log_content)
        logger.info(f"已保存客户端 {client_address} 的日志文件: {log_filename}")
        print(f"已保存客户端 {client_address} 的日志文件: {log_filename}")

    def send_to_client(self, ip, message):
        """
        向指定 IP 的客户端发送消息
        """
        if ip in self.client_sockets:
            try:
                self.client_sockets[ip].send(message.encode('utf-8'))
                logger.info(f"已发送消息到客户端 {ip}: {message}")
                print(f"已发送消息到客户端 {ip}: {message}")
            except Exception as e:
                logger.error(f"向客户端 {ip} 发送消息时出错: {e}")
                print(f"向客户端 {ip} 发送消息时出错: {e}")
                # 如果发送失败，可能客户端已断开连接，从字典中移除
                del self.client_sockets[ip]
                if self.client_sockets[ip] in self.clients:
                    self.clients.remove(self.client_sockets[ip])
        else:
            logger.warning(f"客户端 {ip} 不在线或未连接")
            print(f"客户端 {ip} 不在线或未连接")

def main():
    server = ControlServer()
    server.start()

    print("输入 'quit' 来停止服务器，输入 'save' 来保存客户端信息，输入 'show' 来显示客户端信息")
    print("输入 'test <IP>' 来测试指定IP的设备是否在线")
    print("输入 'ping <IP>' 来使用 ping 测试指定IP的设备是否在线")
    print("输入 'send <IP> <message>' 来向指定IP的客户端发送消息")
    
    try:
        while True:
            command = input("输入命令: ")
            if command.lower() == 'quit':
                break
            elif command.lower() == 'save':
                server.save_client_info()
            elif command.lower() == 'show':
                server.show_clients()
            elif command.lower().startswith('test '):
                ip = command.split(' ', 1)[1]
                server.test_client_online(ip)
            elif command.lower().startswith('ping '):
                ip = command.split(' ', 1)[1]
                threading.Thread(target=server.ping_test, args=(ip,)).start()
            elif command.lower().startswith('log '):
                ip = command.split(' ', 1)[1]
                server.send_command(f"log {ip}")
            elif command.lower().startswith('send '):
                parts = command.split(' ', 2)
                if len(parts) == 3:
                    ip, message = parts[1], parts[2]
                    server.send_to_client(ip, message)
                else:
                    print("格式错误。正确格式: send <IP> <message>")
            else:
                server.send_command(command)
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在关闭服务器...")
        print("\n接收到中断信号，正在关闭服务器...")
    finally:
        server.stop()

if __name__ == "__main__":
    main()
    logger.info('程序退出')
