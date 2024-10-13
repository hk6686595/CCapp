import psutil
import datetime
import os
import json

def load_config():
    try:
        with open('client_config.json', 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        print("未找到配置文件，使用默认设置")
        return {"pssoft_path": "D:\\pssoft"}
    except json.JSONDecodeError:
        print("配置文件格式错误，使用默认设置")
        return {"pssoft_path": "D:\\pssoft"}

def get_project_name():
    config = load_config()
    pssoft_path = config.get("pssoft_path", "D:\\pssoft")
    try:
        folders = [f for f in os.listdir(pssoft_path) if os.path.isdir(os.path.join(pssoft_path, f))]
        return folders[0] if folders else "NoProjects"
    except Exception:
        return "NoProjects"

def get_system_info(client_ip, project_name):
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime_str = str(uptime).split('.')[0]

    return f"IP: {client_ip}, 项目名称: {project_name}, CPU: {cpu_percent}%, 内存: {memory_percent}%, 启动时间: {boot_time}, 运行时长: {uptime_str}"
