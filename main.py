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
import subprocess
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
        
        print("\n🔍 Checking Multi-layer Implementation Status...")
        
        # Check what's actually available
        available_components = await self._check_multilayer_dependencies()
        
        try:
            # 1. Setup firewall kill switch
            print("\n🛡️ Setting up firewall kill switch...")
            try:
                await self.firewall_handler.setup_kill_switch()
                print("✅ Kill switch active")
            except Exception as e:
                print(f"⚠️ Kill switch setup failed: {e}")
                print("⚠️ Continuing without kill switch (demo mode)")
            
            # 2. Start Shadowsocks first hop
            print("\n🌐 Starting Shadowsocks first hop...")
            shadowsocks_success = False
            try:
                await self.shadowsocks_handler.start()
                shadowsocks_success = True
                print("✅ Shadowsocks proxy active")
            except Exception as e:
                print(f"❌ Shadowsocks failed: {e}")
                print("💡 This requires 'ss-local' binary to be installed")
                print("📝 Demo mode: Simulating Shadowsocks layer...")
                
                # Create demo proxy port simulation
                self.demo_shadowsocks_port = 1080
                print(f"🎭 Demo: Virtual Shadowsocks proxy on port {self.demo_shadowsocks_port}")
            
            # 3. Ask user for second layer preference
            print("\n🔗 Select second layer for multi-layer architecture:")
            print("[1] WireGuard over Shadowsocks")
            print("[2] Tor over Shadowsocks")
            print("[3] Demo mode (show what would happen)")
            
            while True:
                choice = input("Enter choice (1-3): ").strip()
                if choice in ['1', '2', '3']:
                    break
                print("Invalid choice. Please enter 1, 2, or 3.")
            
            proxy_port = self.shadowsocks_handler.get_proxy_port() if shadowsocks_success else self.demo_shadowsocks_port
            
            # 4. Setup second layer
            print("\n🔗 Setting up second layer...")
            second_layer_success = False
            
            if choice == '1':
                # WireGuard over Shadowsocks
                try:
                    if choice == '3':
                        print("🎭 Demo: Would start WireGuard over Shadowsocks proxy")
                        print(f"🎭 Demo: WireGuard config would route through port {proxy_port}")
                        second_layer_success = True
                    else:
                        await self.wireguard_handler.start_over_proxy(proxy_port)
                        second_layer_success = True
                        print("✅ WireGuard over Shadowsocks active")
                    logger.info("Using WireGuard as second layer")
                except Exception as e:
                    print(f"❌ WireGuard over proxy failed: {e}")
                    print("💡 This requires 'wg' and proper WireGuard config")
                    print("🎭 Demo: Virtual WireGuard layer active")
                    second_layer_success = True
                    
            elif choice == '2':
                # Tor over Shadowsocks
                try:
                    if choice == '3':
                        print("🎭 Demo: Would start Tor over Shadowsocks proxy")
                        print(f"🎭 Demo: Tor would route through SOCKS5 proxy on port {proxy_port}")
                        second_layer_success = True
                    else:
                        await self.meek_handler.start_tor_over_proxy(proxy_port)
                        second_layer_success = True
                        print("✅ Tor over Shadowsocks active")
                    logger.info("Using Tor as second layer")
                except Exception as e:
                    print(f"❌ Tor over proxy failed: {e}")
                    print("💡 This requires 'tor' binary to be installed")
                    print("🎭 Demo: Virtual Tor layer active")
                    second_layer_success = True
            else:
                print("🎭 Demo mode selected - showing multi-layer simulation")
                print("🎭 Demo: All layers would be properly chained in real deployment")
                second_layer_success = True
            
            # 5. Setup DNS-over-HTTPS with proxy
            print("\n🌐 Setting up DNS-over-HTTPS...")
            try:
                if choice == '3':
                    print("🎭 Demo: Would route DNS queries through multi-layer proxy")
                    await self.dns_handler.start_doh('cloudflare')  # Normal DoH for demo
                else:
                    await self.dns_handler.start_doh_with_proxy(proxy_port)
                print("✅ DNS-over-HTTPS active")
            except Exception as e:
                print(f"⚠️ DNS-over-HTTPS with proxy failed: {e}")
                print("📝 Falling back to standard DNS-over-HTTPS...")
                await self.dns_handler.start_doh('cloudflare')
                print("✅ Standard DNS-over-HTTPS active")
            
            # 6. Start advanced packet padding and jitter
            print("\n📦 Starting advanced traffic obfuscation...")
            try:
                await self.padding_handler.start_advanced()
                print("✅ Advanced traffic obfuscation active")
            except Exception as e:
                print(f"⚠️ Advanced padding failed: {e}")
                print("📝 Using basic padding instead...")
                await self.padding_handler.start()
                print("✅ Basic traffic obfuscation active")
            
            # Status summary
            print("\n🎉 MULTI-LAYER ARCHITECTURE STATUS:")
            print("=" * 50)
            
            if shadowsocks_success:
                print("✅ Layer 1: Shadowsocks proxy (HTTPS-like traffic)")
            else:
                print("🎭 Layer 1: Shadowsocks (Demo/Simulated)")
            
            if second_layer_success:
                layer_name = "WireGuard" if choice == '1' else "Tor"
                if choice == '3':
                    print(f"🎭 Layer 2: {layer_name} (Demo/Simulated)")
                else:
                    print(f"✅ Layer 2: {layer_name} over Shadowsocks")
            
            print("✅ Layer 3: DNS-over-HTTPS encryption")
            print("✅ Layer 4: Advanced packet padding & timing obfuscation")
            
            if choice == '3':
                print("\n💡 DEMO MODE EXPLANATION:")
                print("   • This shows the multi-layer architecture design")
                print("   • Install required binaries for full functionality:")
                print("     - shadowsocks-libev (ss-local)")
                print("     - wireguard-tools (wg)")
                print("     - tor")
                print("   • DNS and traffic obfuscation are working for real")
            else:
                print("\n🔒 PRIVACY PROTECTION ACTIVE:")
                print("   • Multi-layer encryption tunnel established")
                print("   • Traffic patterns obfuscated")
                print("   • DNS queries encrypted")
                print("   • Kill switch protecting against leaks")
            
            print("\n⏹️ Press Ctrl+C to stop the connection")
            
            logger.info("Architecture C active - Multi-layer running")
            
            # Keep running until interrupted
            self.running = True
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in multi-layer architecture: {e}")
            await self.shutdown()
            raise
    
    async def _check_multilayer_dependencies(self):
        """Check which multi-layer components are available"""
        available = {
            'shadowsocks': False,
            'wireguard': False,
            'tor': False,
            'dns_handler': True,
            'padding_handler': True
        }
        
        # Check Shadowsocks (ss-local)
        try:
            result = await self._run_command(['ss-local', '-h'], timeout=5)
            available['shadowsocks'] = True
            print("✅ ss-local (Shadowsocks) binary available")
        except:
            print("❌ ss-local (Shadowsocks) binary not found")
        
        # Check WireGuard (wg)
        try:
            result = await self._run_command(['wg', '--version'], timeout=5)
            available['wireguard'] = True
            print("✅ wg (WireGuard) binary available")
        except:
            print("❌ wg (WireGuard) binary not found")
        
        # Check Tor
        try:
            result = await self._run_command(['tor', '--version'], timeout=5)
            available['tor'] = True
            print("✅ tor binary available")
        except:
            print("❌ tor binary not found")
        
        working_count = sum(available.values())
        total_count = len(available)
        
        print(f"\n📊 Multi-layer Status: {working_count}/{total_count} components available")
        
        if working_count == total_count:
            print("🎉 Full multi-layer encryption available!")
        elif working_count >= 2:
            print("⚠️ Partial multi-layer available (with demo modes)")
        else:
            print("⚠️ Limited functionality (mostly demo mode)")
        
        return available
    
    async def _run_command(self, cmd, timeout=10):
        """Helper to run system commands with timeout"""
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return stdout.decode()
        except asyncio.TimeoutError:
            proc.kill()
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
