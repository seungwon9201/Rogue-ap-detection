import subprocess
import numpy as np
import time

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
        # WiFi 설정 파일 생성
        wpa_supplicant_conf = f"""
        network={{
            ssid="{ssid}"
            bssid={bssid}
            key_mgmt=NONE
        }}
        """
        with open('/tmp/wpa_supplicant.conf', 'w') as file:
            file.write(wpa_supplicant_conf)
        
        # wpa_supplicant 명령 실행
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

# RTT 측정
def get_rtt_probe(ap_ip, count=10):
    rtt_probe = []
    for _ in range(count):
        try:
            result = subprocess.run(['ping', '-c', '1', ap_ip], capture_output=True, text=True)
            if 'time=' in result.stdout:
                start_idx = result.stdout.find('time=') + len('time=')
                end_idx = result.stdout.find(' ms', start_idx)
                rtt = float(result.stdout[start_idx:end_idx].strip())
                rtt_probe.append(rtt)
            else:
                print("No RTT time found in ping output.")
        except Exception as e:
            print(f"Error during probe RTT: {e}")
    return rtt_probe

# 통계 계산
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

def main():
    file_path = '/tmp/ap_data/1.txt'  # 파일 경로 설정
    interface = 'wlx588694fe2ad3'  # 무선 인터페이스 이름

    ssid_list, bssid_list = read_wifi_info_from_file(file_path)
    
    if len(ssid_list) == 0:
        print("No SSID found in file.")
        return None, None
    
    for ssid, bssid in zip(ssid_list, bssid_list):
        if not connect_to_wifi(ssid, bssid, interface):
            print(f"Could not connect to the WiFi network with SSID: {ssid} and BSSID: {bssid}.")
            continue
        
        time.sleep(10)  # 연결 안정화를 위한 대기 시간

        ap_ip = get_default_gateway()
        if not ap_ip:
            print("Could not determine the gateway IP.")
            continue
        
        print(f"Measuring RTT to AP IP: {ap_ip}")
        rtt_probe = get_rtt_probe(ap_ip)
        print(f"RTT probe results: {rtt_probe}")
        
        rtt_probe_mean, rtt_probe_std = calculate_statistics(rtt_probe)
        
        if np.isnan(rtt_probe_mean):
            print("Error in RTT calculation.")
            continue
        
        print(f"RTT Mean: {rtt_probe_mean:.2f} ms, RTT Std: {rtt_probe_std:.2f} ms")
        
        return rtt_probe_mean, rtt_probe_std

if __name__ == "__main__":
    main()

