import subprocess
import os
from scapy.all import *
from scapy.layers.dot11 import Dot11, Dot11Beacon, Dot11Elt
from collections import defaultdict
import csv
from datetime import datetime

def set_monitor_mode(interface):
    """ Set the network interface to monitor mode. """
    print(f"Setting {interface} to monitor mode...")
    try:
        subprocess.run(["sudo", "ip", "link", "set", interface, "down"], check=True)
        subprocess.run(["sudo", "iwconfig", interface, "mode", "monitor"], check=True)
        subprocess.run(["sudo", "ip", "link", "set", interface, "up"], check=True)
        print(f"{interface} is now in monitor mode.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to set {interface} to monitor mode: {e}")
        raise

def capture_network(interface, pcap_file, capture_time=10):
    """ Capture network traffic using TShark for a given duration and save it to a file. """
    print(f"Starting network capture on {interface} for {capture_time} seconds...")
    try:
        result = subprocess.run([
            "sudo", "tshark", 
            "-i", interface,  
            "-a", f"duration:{capture_time}",
            "-w", pcap_file
        ], check=True)
        print(f"Capture complete. Saved to {pcap_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during capture: {e}")
        raise

def extract_beacon_features(pcap_file, csv_file):
    """ Extract beacon frame features from the PCAP file and save them to a CSV file. """
    packets = rdpcap(pcap_file)
    last_beacon_time = defaultdict(float)
    
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["SSID", "BSSID", "Channel", "Signal Strength", "Encryption", 
                             "Supported Rates", "Beacon Interval", "Estimated RTT", "Vendor OUI"])
    
        for packet in packets:
            if packet.haslayer(Dot11Beacon):
                beacon = packet[Dot11Beacon]

                ssid = beacon.info.decode('utf-8', errors='ignore')
                bssid = packet[Dot11].addr3

                channel = None
                for elt in packet.iterpayloads():
                    if isinstance(elt, Dot11Elt):
                        if elt.ID == 3:
                            channel = ord(elt.info)
                            break
                        elif elt.ID == 194:
                            channel = ord(elt.info[0])
                            break

                if packet.haslayer(RadioTap):
                    signal_strength = packet[RadioTap].dBm_AntSignal
                else:
                    signal_strength = "N/A"

                encryption = "Open"
                if beacon.cap.privacy:
                    encryption = "WEP/WPA/WPA2"

                supported_rates = []
                extended_supported_rates = []
                for elt in packet.iterpayloads():
                    if isinstance(elt, Dot11Elt):
                        if elt.ID == 1:
                            supported_rates = [rate/2 for rate in elt.info]
                        elif elt.ID == 50:
                            extended_supported_rates = [rate/2 for rate in elt.info]

                all_supported_rates = supported_rates + extended_supported_rates

                current_time = packet.time
                if last_beacon_time[bssid]:
                    beacon_interval = current_time - last_beacon_time[bssid]
                else:
                    beacon_interval = 0
                last_beacon_time[bssid] = current_time

                oui = bssid[:8].upper()

                writer.writerow([ssid, bssid, channel, signal_strength, encryption, 
                                 ','.join(map(str, all_supported_rates)), beacon.beacon_interval, 
                                 f"{beacon_interval:.6f}", oui])

def main():
    interface = "wlx588694fe2ad3"  # Interface name
    pcap_file = 'capture.pcapng'  # pcapng 파일로 설정
    
    # Get the current time for naming the CSV file
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Set the CSV file path to /tmp/ap_data/ with the current time
    csv_file = f'/tmp/ap_data/ap_dataset_{current_time}.csv'
    
    # Step 1: Set interface to monitor mode
    set_monitor_mode(interface)
    
    # Step 2: Capture network traffic (capture time set to 20 seconds)
    capture_network(interface, pcap_file, capture_time=30)
    
    # Step 3: Extract features from the captured data
    extract_beacon_features(pcap_file, csv_file)
    
    print(f"Features have been extracted and saved to {csv_file}")
    
    # Step 4: Change file permissions so it's accessible remotely
    try:
        os.chmod(csv_file, 0o777)  # 모든 사용자에게 읽기, 쓰기 및 실행 권한 부여
        print(f"Changed permissions of {csv_file} to 777")
    except OSError as e:
        print(f"Failed to change file permissions: {e}")

    # Step 5: Schedule file deletion by running a separate script
    deletion_script = "delete_script.py"
    
    # Set the file deletion time (in seconds)
    delay_seconds = 600  # 파일 삭제 시간을 600초 (10분)로 설정
    
    # To change the deletion time, adjust the delay_seconds value above
    subprocess.Popen(["python3", deletion_script, csv_file, str(delay_seconds)])

if __name__ == "__main__":
    main()

