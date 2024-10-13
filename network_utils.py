import subprocess
import platform

def ping_test(ip):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', ip]
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        for encoding in ['utf-8', 'gbk', 'gb2312', 'ascii']:
            try:
                decoded_output = output.decode(encoding)
                if "TTL=" in decoded_output:
                    return True
                break
            except UnicodeDecodeError:
                continue
        return False
    except subprocess.CalledProcessError:
        return False
