import subprocess
import numpy as np
import time
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import dns.resolver
import watchdog.events
import watchdog.observers

# 글로벌 변수
current_wifi_ip = None
new_wifi_ip = None
rtt_ping_current = []
rtt_dns_current = []
rtt_ping_new = []
rtt_dns_new = []

# 파일로부터 SSID와 BSSID 읽기
def read_wifi_info_from_file(file_path):
    ssid_list = []
    bssid_list = []

    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line:
                parts = line.split()
                if len(parts) == 2:
                    ssid_list.append(parts[0])
                    bssid_list.append(parts[1])

    if not ssid_list or not bssid_list:
        raise ValueError("SSID 또는 BSSID 정보를 파일에서 찾을 수 없습니다.")

    return ssid_list, bssid_list

# WiFi 연결
def connect_to_wifi(ssid, bssid, interface):
    try:
        wpa_supplicant_conf = f"""
        network={{
            ssid="{ssid}"
            bssid={bssid}
            key_mgmt=NONE
        }}
        """
        with open('/tmp/wpa_supplicant.conf', 'w') as file:
            file.write(wpa_supplicant_conf)

        subprocess.run(['sudo', 'wpa_supplicant', '-B', '-i', interface, '-c', '/tmp/wpa_supplicant.conf'])
        subprocess.run(['sudo', 'dhclient', interface])

        print(f"Connected to WiFi: {ssid} with BSSID: {bssid}")
        return True
    except Exception as e:
        print(f"Error connecting to WiFi: {e}")
        return False

# 기본 게이트웨이 IP 얻기
def get_default_gateway():
    try:
        result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        for line in lines:
            if 'default via' in line:
                gateway_ip = line.split()[2]
                return gateway_ip
        print("Default gateway not found.")
        return None
    except Exception as e:
        print(f"Error getting default gateway: {e}")
        return None

# ICMP ping을 사용한 RTT 측정
def get_ping_rtt(ip, count=10):
    rtt_ping = []
    for _ in range(count):
        try:
            result = subprocess.run(['ping', '-c', '1', ip], capture_output=True, text=True)
            if 'time=' in result.stdout:
                start_idx = result.stdout.find('time=') + len('time=')
                end_idx = result.stdout.find(' ms', start_idx)
                rtt = float(result.stdout[start_idx:end_idx].strip())
                rtt_ping.append(rtt)
            else:
                print("No RTT time found in ping output.")
        except Exception as e:
            print(f"Error during ping RTT: {e}")
    return rtt_ping

# DNS 쿼리를 사용한 RTT 측정
def get_dns_rtt(dns_server, count=10):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server]
    
    rtt_dns = []
    
    for _ in range(count):
        try:
            start_time = time.time()
            resolver.resolve('google.com', 'A')
            end_time = time.time()
            rtt = (end_time - start_time) * 1000  # ms로 변환
            rtt_dns.append(rtt)
        except Exception as e:
            print(f"DNS query failed: {e}")
    return rtt_dns

# RTT 측정 및 통계 계산
def calculate_statistics(rtt_list):
    if not rtt_list:
        print("RTT list is empty, cannot calculate statistics.")
        return np.nan, np.nan

    rtt_sorted = sorted(rtt_list)
    discard_count = len(rtt_sorted) // 10
    rtt_trimmed = rtt_sorted[discard_count:-discard_count]

    if len(rtt_trimmed) < 2:
        print("Trimmed RTT list is too small to calculate statistics.")
        return np.nan, np.nan

    rtt_mean = np.mean(rtt_trimmed)
    rtt_std = np.std(rtt_trimmed)
    return rtt_mean, rtt_std

# 실시간 그래프를 업데이트하는 함수
def update_plot(frame):
    global rtt_ping_current, rtt_dns_current, rtt_ping_new, rtt_dns_new, current_wifi_ip, new_wifi_ip, ax1, ax2

    # 현재 연결된 WiFi에 대해 RTT 측정
    if current_wifi_ip:
        ping_rtts = get_ping_rtt(current_wifi_ip, count=1)
        dns_rtts = get_dns_rtt(current_wifi_ip, count=1)
        
        if ping_rtts:
            rtt_ping_current.append(ping_rtts[0])
            if len(rtt_ping_current) > 100:  # 제한된 데이터 수
                rtt_ping_current.pop(0)
        
        if dns_rtts:
            rtt_dns_current.append(dns_rtts[0])
            if len(rtt_dns_current) > 100:  # 제한된 데이터 수
                rtt_dns_current.pop(0)

    # 새로 연결된 WiFi에 대해 RTT 측정
    if new_wifi_ip:
        ping_rtts = get_ping_rtt(new_wifi_ip, count=1)
        dns_rtts = get_dns_rtt(new_wifi_ip, count=1)
        
        if ping_rtts:
            rtt_ping_new.append(ping_rtts[0])
            if len(rtt_ping_new) > 100:  # 제한된 데이터 수
                rtt_ping_new.pop(0)
        
        if dns_rtts:
            rtt_dns_new.append(dns_rtts[0])
            if len(rtt_dns_new) > 100:  # 제한된 데이터 수
                rtt_dns_new.pop(0)

    # 데이터 플로팅
    ax1.clear()
    ax2.clear()

    ax1.plot(rtt_ping_current, label='Current WiFi Ping RTT (ms)', color='blue')
    ax1.plot(rtt_ping_new, label='New WiFi Ping RTT (ms)', color='green')
    ax2.plot(rtt_dns_current, label='Current WiFi DNS RTT (ms)', color='orange')
    ax2.plot(rtt_dns_new, label='New WiFi DNS RTT (ms)', color='red')

    ax1.set_title('Ping RTT')
    ax1.set_ylabel('RTT (ms)')
    ax1.set_xlabel('Sample')
    ax1.legend(loc='upper right')

    ax2.set_title('DNS RTT')
    ax2.set_ylabel('RTT (ms)')
    ax2.set_xlabel('Sample')
    ax2.legend(loc='upper right')

    plt.tight_layout()

# 파일 시스템 감시 이벤트 핸들러
class FileChangeHandler(watchdog.events.FileSystemEventHandler):
    def on_created(self, event):
        global new_wifi_ip
        if event.src_path.endswith('1.txt'):
            print(f"File {event.src_path} has been created.")
            ssid_list, bssid_list = read_wifi_info_from_file(event.src_path)
            if ssid_list and bssid_list:
                ssid = ssid_list[0]
                bssid = bssid_list[0]
                if connect_to_wifi(ssid, bssid, interface):
                    new_wifi_ip = get_default_gateway()
                    if new_wifi_ip:
                        print(f"New AP IP: {new_wifi_ip}")
                    else:
                        print("Could not determine the new gateway IP.")

def main():
    global current_wifi_ip, new_wifi_ip, interface, ax1, ax2

    file_path_normal = '/tmp/ap_data/normal.txt'
    interface = 'wlx588694fe2ad3'

    # Initialize the connection with normal.txt
    ssid_list, bssid_list = read_wifi_info_from_file(file_path_normal)
    if ssid_list and bssid_list:
        ssid = ssid_list[0]
        bssid = bssid_list[0]
        if connect_to_wifi(ssid, bssid, interface):
            current_wifi_ip = get_default_gateway()
            if current_wifi_ip:
                print(f"Current AP IP: {current_wifi_ip}")
            else:
                print("Could not determine the gateway IP.")
        else:
            print("Could not connect to the WiFi network from normal.txt.")

    # Setup the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))
    ani = FuncAnimation(fig, update_plot, interval=1000)
    
    # Setup file system observer
    event_handler = FileChangeHandler()
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, path='/tmp/ap_data', recursive=False)
    observer.start()

    try:
        plt.show()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()

