#!/usr/bin/env python3
"""
Advanced Network Traffic Obfuscation System
Multi-layer privacy protection with three distinct architectures
"""

import sys
import asyncio
import signal
import os
import logging
from typing import Optional

# Import our custom handlers
try:
    from dns_handler import DNSHandler
    from firewall_handler import FirewallHandler
    from padding_handler import PaddingHandler
    from wireguard_handler import WireGuardHandler
    from obfs4_handler import Obfs4Handler
    from meek_handler import MeekHandler
    from shadowsocks_handler import ShadowsocksHandler
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all module files are in the same directory as main.py")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('network_obfuscation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NetworkObfuscationSystem:
    """
    Main system orchestrator for network traffic obfuscation
    Manages three different privacy architectures
    """
    
    def __init__(self):
        self.active_architecture = None
        self.running = False
        self.dns_handler = DNSHandler()
        self.firewall_handler = FirewallHandler()
        self.padding_handler = PaddingHandler()
        
        # Architecture-specific handlers
        self.wireguard_handler = WireGuardHandler()
        self.obfs4_handler = Obfs4Handler()
        self.meek_handler = MeekHandler()
        self.shadowsocks_handler = ShadowsocksHandler()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C and termination signals"""
        logger.info("Received shutdown signal, cleaning up...")
        asyncio.create_task(self.shutdown())
    
    def display_banner(self):
        """Display application banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║            Advanced Network Traffic Obfuscation              ║
║                   Privacy Protection System                  ║
╠══════════════════════════════════════════════════════════════╣
║  Multi-layer encryption • Traffic masking • ISP evasion     ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def display_menu(self):
        """Display architecture selection menu"""
        menu = """
┌─────────────────────────────────────────────────────────────┐
│                  Select Protection Architecture             │
├─────────────────────────────────────────────────────────────┤
│  [1] WireGuard + obfs4                                      │
│      ├─ obfs4 traffic obfuscation layer                    │
│      ├─ WireGuard VPN over obfs4                           │
│      ├─ DNS-over-HTTPS (DoH)                               │
│      └─ Packet padding + timing obfuscation                │
│                                                             │
│  [2] Tor + meek (domain fronting)                          │
│      ├─ meek domain fronting (appears as CDN traffic)      │
│      ├─ Tor anonymity network                              │
│      ├─ DNS through Tor network                            │
│      └─ Packet padding + timing obfuscation                │
│                                                             │
│  [3] Multi-layer (Shadowsocks + WireGuard/Tor + DoH)       │
│      ├─ Shadowsocks first hop (HTTPS-like traffic)         │
│      ├─ WireGuard or Tor over Shadowsocks                  │
│      ├─ DNS-over-HTTPS proxy                               │
│      └─ Advanced packet padding + jitter                   │
│                                                             │
│  [0] Exit                                                   │
└─────────────────────────────────────────────────────────────┘
        """
        print(menu)
    
    async def architecture_wireguard_obfs4(self):
        """
        Architecture A: WireGuard + obfs4
        - obfs4 obfuscation layer
        - WireGuard VPN over obfs4
        - DoH DNS queries
        - Packet padding and timing obfuscation
        """
        logger.info("Starting Architecture A: WireGuard + obfs4")
        
        try:
            # 1. Setup firewall kill switch
            await self.firewall_handler.setup_kill_switch()
            
            # 2. Start obfs4 obfuscation layer
            await self.obfs4_handler.start()
            
            # 3. Configure and start WireGuard over obfs4
            await self.wireguard_handler.start_over_obfs4(self.obfs4_handler.get_proxy_port())
            
            # 4. Setup DNS-over-HTTPS
            await self.dns_handler.start_doh()
            
            # 5. Start packet padding and timing obfuscation
            await self.padding_handler.start()
            
            logger.info("Architecture A active - WireGuard + obfs4 running")
            print("✓ WireGuard + obfs4 architecture is now active")
            print("✓ Traffic is being obfuscated and encrypted")
            print("✓ DNS queries are secure via DoH")
            print("✓ Kill switch is active")
            print("\nPress Ctrl+C to stop the connection")
            
            # Keep running until interrupted
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in WireGuard + obfs4 architecture: {e}")
            await self.shutdown()
            raise
    
    async def architecture_tor_meek(self):
        """
        Architecture B: Tor + meek (domain fronting)
        - meek domain fronting (traffic appears as CDN requests)
        - Tor anonymity network
        - DNS through Tor
        - Packet padding and timing obfuscation
        """
        logger.info("Starting Architecture B: Tor + meek")
        
        try:
            # 1. Setup firewall kill switch
            await self.firewall_handler.setup_kill_switch()
            
            # 2. Start meek domain fronting
            await self.meek_handler.start()
            
            # 3. Start Tor over meek bridge
            await self.meek_handler.start_tor_over_meek()
            
            # 4. Configure DNS through Tor
            await self.dns_handler.start_tor_dns()
            
            # 5. Start packet padding and timing obfuscation
            await self.padding_handler.start()
            
            logger.info("Architecture B active - Tor + meek running")
            print("✓ Tor + meek architecture is now active")
            print("✓ Traffic appears as CDN requests")
            print("✓ Anonymous routing through Tor network")
            print("✓ DNS queries through Tor")
            print("✓ Kill switch is active")
            print("\nPress Ctrl+C to stop the connection")
            
            # Keep running until interrupted
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in Tor + meek architecture: {e}")
            await self.shutdown()
            raise
    
    async def architecture_multilayer(self):
        """
        Architecture C: Multi-layer (Shadowsocks + WireGuard/Tor + DoH + Padding)
        - Shadowsocks first hop (HTTPS-like traffic)
        - WireGuard or Tor over Shadowsocks
        - DNS-over-HTTPS proxy
        - Advanced packet padding with jitter
        """
        logger.info("Starting Architecture C: Multi-layer")
        
        try:
            # 1. Setup firewall kill switch
            await self.firewall_handler.setup_kill_switch()
            
            # 2. Start Shadowsocks first hop
            await self.shadowsocks_handler.start()
            
            # 3. Ask user for second layer preference
            print("\nSelect second layer for multi-layer architecture:")
            print("[1] WireGuard over Shadowsocks")
            print("[2] Tor over Shadowsocks")
            
            while True:
                choice = input("Enter choice (1 or 2): ").strip()
                if choice in ['1', '2']:
                    break
                print("Invalid choice. Please enter 1 or 2.")
            
            if choice == '1':
                # WireGuard over Shadowsocks
                await self.wireguard_handler.start_over_proxy(
                    self.shadowsocks_handler.get_proxy_port()
                )
                logger.info("Using WireGuard as second layer")
            else:
                # Tor over Shadowsocks
                await self.meek_handler.start_tor_over_proxy(
                    self.shadowsocks_handler.get_proxy_port()
                )
                logger.info("Using Tor as second layer")
            
            # 4. Setup DNS-over-HTTPS with proxy
            await self.dns_handler.start_doh_with_proxy(
                self.shadowsocks_handler.get_proxy_port()
            )
            
            # 5. Start advanced packet padding and jitter
            await self.padding_handler.start_advanced()
            
            logger.info("Architecture C active - Multi-layer running")
            print("✓ Multi-layer architecture is now active")
            print("✓ Shadowsocks first hop (HTTPS-like traffic)")
            print(f"✓ {'WireGuard' if choice == '1' else 'Tor'} second layer")
            print("✓ DNS-over-HTTPS with proxy")
            print("✓ Advanced packet padding active")
            print("✓ Kill switch is active")
            print("\nPress Ctrl+C to stop the connection")
            
            # Keep running until interrupted
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in multi-layer architecture: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """Graceful shutdown of all components"""
        logger.info("Shutting down network obfuscation system...")
        self.running = False
        
        try:
            # Stop padding handler
            await self.padding_handler.stop()
            
            # Stop DNS handler
            await self.dns_handler.stop()
            
            # Stop architecture-specific handlers
            await self.wireguard_handler.stop()
            await self.obfs4_handler.stop()
            await self.meek_handler.stop()
            await self.shadowsocks_handler.stop()
            
            # Restore firewall rules (disable kill switch)
            await self.firewall_handler.restore_rules()
            
            logger.info("System shutdown completed")
            print("\n✓ All connections stopped")
            print("✓ Firewall rules restored")
            print("✓ System shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def run(self):
        """Main application loop"""
        self.display_banner()
        
        while True:
            self.display_menu()
            
            try:
                choice = input("\nEnter your choice (0-3): ").strip()
                
                if choice == '0':
                    print("Exiting...")
                    break
                
                elif choice == '1':
                    self.active_architecture = 'wireguard_obfs4'
                    self.running = True
                    await self.architecture_wireguard_obfs4()
                
                elif choice == '2':
                    self.active_architecture = 'tor_meek'
                    self.running = True
                    await self.architecture_tor_meek()
                
                elif choice == '3':
                    self.active_architecture = 'multilayer'
                    self.running = True
                    await self.architecture_multilayer()
                
                else:
                    print("Invalid choice. Please enter 0, 1, 2, or 3.")
                    continue
                
                # Reset after architecture stops
                self.running = False
                self.active_architecture = None
                
            except KeyboardInterrupt:
                if self.running:
                    await self.shutdown()
                else:
                    print("\nExiting...")
                    break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if self.running:
                    await self.shutdown()

def main():
    """Entry point for the application"""
    # Check if running as administrator (required for firewall operations)
    if os.name == 'nt':  # Windows
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("Error: This application requires administrator privileges.")
            print("Please run as administrator.")
            sys.exit(1)
    else:  # Linux/Unix
        if os.geteuid() != 0:
            print("Error: This application requires root privileges.")
            print("Please run with sudo.")
            sys.exit(1)
    
    # Create and run the main application
    app = NetworkObfuscationSystem()
    
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()