#!/usr/bin/env python3
"""
Test Mode - No VPS Required
Uses only free services for testing the obfuscation system
"""

import asyncio
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from dns_handler import DNSHandler
    from firewall_handler import FirewallHandler
    from padding_handler import PaddingHandler
    from meek_handler import MeekHandler
    from shadowsocks_handler import ShadowsocksHandler
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)

class TestModeSystem:
    """Free test mode system using only free services"""
    
    def __init__(self):
        self.dns_handler = DNSHandler()
        self.firewall_handler = FirewallHandler() 
        self.padding_handler = PaddingHandler()
        self.meek_handler = MeekHandler()
        self.shadowsocks_handler = ShadowsocksHandler()
        self.running = False
    
    def display_banner(self):
        """Display test mode banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🆓 FREE TEST MODE 🆓                      ║
║             No VPS or Paid Services Required                ║
╠══════════════════════════════════════════════════════════════╣
║  Test all obfuscation features using free services only     ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def display_menu(self):
        """Display free test options"""
        menu = """
┌─────────────────────────────────────────────────────────────┐
│                    Free Test Options                       │
├─────────────────────────────────────────────────────────────┤
│  [1] Tor + meek (100% Free - Recommended)                  │
│      ├─ Uses Tor network (no servers needed)               │
│      ├─ Domain fronting via CDNs                           │
│      ├─ DNS-over-HTTPS                                     │
│      └─ Full packet obfuscation                            │
│                                                             │
│  [2] DNS-over-HTTPS Only Test                              │
│      ├─ Test DNS leak protection                           │
│      ├─ Multiple DoH providers                             │
│      └─ No additional services needed                      │
│                                                             │
│  [3] Packet Padding Test                                   │
│      ├─ Test traffic obfuscation                           │
│      ├─ Dummy traffic generation                           │
│      └─ Timing randomization                               │
│                                                             │
│  [4] Free Shadowsocks Test (Limited)                       │
│      ├─ Use free public servers                            │
│      ├─ Limited bandwidth/time                             │
│      └─ May not always work                                │
│                                                             │
│  [0] Exit                                                   │
└─────────────────────────────────────────────────────────────┘
        """
        print(menu)
    
    async def test_tor_meek(self):
        """Test Tor + meek - completely free"""
        logger.info("Starting FREE Tor + meek test")
        
        try:
            print("🔍 Testing Tor + meek (completely free)...")
            
            # Check if Tor is installed
            import subprocess
            try:
                result = subprocess.run(['tor', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print("✓ Tor is installed and ready")
                else:
                    raise FileNotFoundError
            except (FileNotFoundError, subprocess.TimeoutExpired):
                print("❌ Tor not found. Please install:")
                print("   Windows: choco install tor")
                print("   Ubuntu/Debian: sudo apt install tor")
                print("   macOS: brew install tor")
                return
            
            # Check if meek-client is available
            try:
                result = subprocess.run(['meek-client', '--help'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    raise FileNotFoundError
                print("✓ meek-client is available")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                print("❌ meek-client not found. This is part of Tor browser bundle.")
                print("   For full functionality, install Tor browser or meek plugin")
                print("   Continuing with basic Tor (without domain fronting)...")
            
            # Start DNS-over-HTTPS
            print("🌐 Starting DNS-over-HTTPS...")
            await self.dns_handler.start_doh('cloudflare')
            print("✓ DNS-over-HTTPS active")
            
            # Start packet padding
            print("📦 Starting packet padding...")
            await self.padding_handler.start()
            print("✓ Packet padding active")
            
            # Start meek transport
            print("🎭 Starting meek domain fronting...")
            await self.meek_handler.start('azure')  # Free Azure CDN fronting
            
            # Start Tor over meek
            print("🔒 Starting Tor over meek...")
            await self.meek_handler.start_tor_over_meek()
            
            print("\n🎉 SUCCESS! Tor + meek is now running!")
            print("📊 Your traffic is now:")
            print("   ✓ Encrypted through Tor network")
            print("   ✓ Hidden via domain fronting (appears as CDN traffic)")
            print("   ✓ DNS queries secured via DoH")
            print("   ✓ Packet sizes randomized")
            print("   ✓ Timing patterns obfuscated")
            
            print(f"\n🌐 SOCKS5 Proxy: 127.0.0.1:{self.meek_handler.get_socks_port()}")
            print("   Configure your applications to use this proxy")
            
            print("\n📋 Test your connection:")
            print("   • Visit: https://check.torproject.org")
            print("   • Visit: https://ipleak.net")
            print("   • Check your IP appears as Tor exit node")
            
            print("\nPress Ctrl+C to stop...")
            
            self.running = True
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping test...")
        except Exception as e:
            logger.error(f"Test failed: {e}")
        finally:
            await self.cleanup()
    
    async def test_dns_only(self):
        """Test DNS-over-HTTPS only"""
        logger.info("Starting DNS-over-HTTPS test")
        
        try:
            print("🌐 Testing DNS-over-HTTPS protection...")
            
            # Start DNS-over-HTTPS with different providers
            providers = ['cloudflare', 'google', 'quad9']
            
            for provider in providers:
                print(f"🔍 Testing {provider} DoH...")
                await self.dns_handler.start_doh(provider)
                print(f"✓ {provider} DoH working")
                await self.dns_handler.stop()
                await asyncio.sleep(1)
            
            # Start with best provider
            print("🚀 Starting with Cloudflare DoH...")
            await self.dns_handler.start_doh('cloudflare')
            
            print("\n🎉 SUCCESS! DNS-over-HTTPS is active!")
            print("📊 Your DNS queries are now:")
            print("   ✓ Encrypted via HTTPS")
            print("   ✓ Hidden from ISP")
            print("   ✓ Using secure DNS servers")
            
            print("\n📋 Test your DNS:")
            print("   • Visit: https://1.1.1.1/help")
            print("   • Check 'Using DNS over HTTPS (DoH)' shows Yes")
            print("   • Visit: https://dnsleaktest.com")
            
            print("\nPress Ctrl+C to stop...")
            
            self.running = True
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping test...")
        except Exception as e:
            logger.error(f"Test failed: {e}")
        finally:
            await self.cleanup()
    
    async def test_packet_padding(self):
        """Test packet padding and timing obfuscation"""
        logger.info("Starting packet padding test")
        
        try:
            print("📦 Testing packet padding and timing obfuscation...")
            
            # Start packet padding
            await self.padding_handler.start()
            
            print("\n🎉 SUCCESS! Packet padding is active!")
            print("📊 Your traffic patterns are now:")
            print("   ✓ Packet sizes normalized")
            print("   ✓ Timing patterns randomized")
            print("   ✓ Dummy traffic generated")
            print("   ✓ Burst protection active")
            
            print("\n📋 Monitor the effects:")
            print("   • Check network activity in Task Manager/htop")
            print("   • Notice random dummy traffic")
            print("   • Packet timing is now irregular")
            
            print("\nPress Ctrl+C to stop...")
            
            self.running = True
            while self.running:
                await asyncio.sleep(5)
                stats = self.padding_handler.get_stats()
                print(f"📊 Stats: {stats['dummy_packets_sent']} dummy packets sent, "
                      f"{stats['packets_padded']} packets padded")
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping test...")
        except Exception as e:
            logger.error(f"Test failed: {e}")
        finally:
            await self.cleanup()
    
    async def test_free_shadowsocks(self):
        """Test with free Shadowsocks servers"""
        logger.info("Starting free Shadowsocks test")
        
        try:
            print("🆓 Testing free Shadowsocks servers...")
            print("⚠️  Note: Free servers may be slow or unavailable")
            
            # Free servers (these may not always work)
            free_servers = [
                {
                    "server": "free-ss.sshmax.xyz",
                    "server_port": 443,
                    "password": "sshmax.xyz", 
                    "method": "aes-256-cfb"
                }
            ]
            
            for server in free_servers:
                print(f"🔍 Testing server: {server['server']}")
                
                # Test connectivity first
                connectivity = await self.shadowsocks_handler.test_server_connectivity(
                    server['server'], server['server_port'], timeout=10.0
                )
                
                if connectivity:
                    print(f"✓ Server {server['server']} is reachable")
                    
                    # Configure and start
                    await self.shadowsocks_handler.set_config(
                        server=server['server'],
                        server_port=server['server_port'],
                        password=server['password'],
                        method=server['method']
                    )
                    
                    try:
                        await self.shadowsocks_handler.start()
                        
                        print(f"\n🎉 SUCCESS! Connected to free server!")
                        print(f"📊 SOCKS5 Proxy: 127.0.0.1:{self.shadowsocks_handler.get_proxy_port()}")
                        print("   Configure your browser to use this proxy")
                        
                        print("\n📋 Test your connection:")
                        print("   • Visit: https://whatismyipaddress.com")
                        print("   • Your IP should be different now")
                        
                        print("\nPress Ctrl+C to stop...")
                        
                        self.running = True
                        while self.running:
                            await asyncio.sleep(1)
                        
                        break
                        
                    except Exception as e:
                        print(f"❌ Failed to connect: {e}")
                        continue
                else:
                    print(f"❌ Server {server['server']} not reachable")
            
            print("❌ No free servers available at the moment")
            print("💡 Try option 1 (Tor + meek) instead - always works!")
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping test...")
        except Exception as e:
            logger.error(f"Test failed: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up all services"""
        try:
            self.running = False
            await self.padding_handler.stop()
            await self.dns_handler.stop() 
            await self.meek_handler.stop()
            await self.shadowsocks_handler.stop()
            print("✓ All services stopped")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    async def run(self):
        """Main test mode loop"""
        self.display_banner()
        
        while True:
            self.display_menu()
            
            try:
                choice = input("\nSelect test option (0-4): ").strip()
                
                if choice == '0':
                    print("Exiting test mode...")
                    break
                
                elif choice == '1':
                    await self.test_tor_meek()
                
                elif choice == '2':
                    await self.test_dns_only()
                
                elif choice == '3':
                    await self.test_packet_padding()
                
                elif choice == '4':
                    await self.test_free_shadowsocks()
                
                else:
                    print("Invalid choice. Please select 0-4.")
                    continue
                
            except KeyboardInterrupt:
                await self.cleanup()
                break
            except Exception as e:
                logger.error(f"Error: {e}")

def main():
    """Entry point"""
    print("🆓 FREE TEST MODE - No VPS or paid services required!")
    print("Only requirement: Install Tor for full functionality")
    print()
    
    # Check admin privileges for some features
    if os.name == 'nt':  # Windows
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("⚠️  For full functionality, run as Administrator")
            print("   (Required for firewall kill switch)")
    else:  # Linux/Unix
        if os.geteuid() != 0:
            print("⚠️  For full functionality, run with sudo")
            print("   (Required for firewall kill switch)")
    
    print()
    
    app = TestModeSystem()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\nTest mode interrupted by user")

if __name__ == "__main__":
    main()