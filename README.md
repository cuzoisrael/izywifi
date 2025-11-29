# IzyWiFi

A Python script for ethical WiFi auditing using tools like Aircrack-ng and Hashcat.  
**WARNING: For educational and authorized security testing only. Unauthorized use violates laws like the Computer Fraud and Abuse Act.**

## Features
- Scan for nearby WiFi networks and save results as CSV.
- Capture WPA/WPA2 handshakes with deauthentication.
- Convert captures to Hashcat format and attempt password cracking.
- Automatic monitor mode management for wireless interfaces.

## Prerequisites
- Linux OS with a compatible wireless adapter (e.g., supporting monitor mode).
- Python 3.6+.
- Aircrack-ng suite: `sudo apt install aircrack-ng` (or equivalent).
- Hashcat: Download from [hashcat.net](https://hashcat.net/hashcat/).
- hcxtools: For capture conversion (`sudo apt install hcxtools`).
- Wordlist (e.g., [rockyou.txt](https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt) – download and unzip).

## Installation
```bash
git clone https://github.com/cuzoisrael/izywifi.git
cd izywifi
pip install -r requirements.txt




##Usage

python izywifi.py -i <interface> [options]


## Examples

# Scan networks for 45 seconds
python izywifi.py -i wlan0 -s -d 45

# Capture handshake (replace with real BSSID/channel from scan)
python izywifi.py -i wlan0 -c AA:BB:CC:DD:EE:FF 6 -d 60

# Crack a captured handshake
python izywifi.py -i wlan0 -k wifi_captures/handshake_AABBCCDD.cap -w rockyou.txt
