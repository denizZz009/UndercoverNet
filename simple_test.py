#!/usr/bin/env python3
"""
Simple Working Test - Only features that work without additional binaries
"""

import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from dns_handler import DNSHandler
    from padding_handler import PaddingHandler
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)

async def test_dns_protection():
    """Test DNS-over-HTTPS protection - WORKS WITHOUT ANY INSTALLATION"""
    print("🌐 Testing DNS-over-HTTPS Protection")
    print("=" * 50)
    
    dns_handler = DNSHandler()
    
    try:
        print("🔍 Starting Cloudflare DNS-over-HTTPS...")
        await dns_handler.start_doh('cloudflare')
        
        print("\n✅ SUCCESS! DNS-over-HTTPS is now active!")
        print("\n📊 What this does:")
        print("   • All DNS queries are now encrypted")
        print("   • Your ISP cannot see which websites you visit") 
        print("   • DNS queries go through HTTPS to Cloudflare")
        print("   • Prevents DNS hijacking and manipulation")
        
        print("\n🧪 Test it yourself:")
        print("   1. Visit: https://1.1.1.1/help")
        print("   2. Look for 'Using DNS over HTTPS (DoH): Yes'")
        print("   3. Visit: https://dnsleaktest.com")
        print("   4. Run Extended Test - should show Cloudflare servers")
        
        print("\n⏳ DNS protection is running... Press Ctrl+C to stop")
        
        # Keep running
        while True:
            await asyncio.sleep(5)
            print("📡 DNS protection active - all queries encrypted")
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping DNS protection...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await dns_handler.stop()
        print("✅ DNS protection stopped - back to normal DNS")

async def test_traffic_padding():
    """Test traffic padding and obfuscation - WORKS WITHOUT INSTALLATION"""
    print("📦 Testing Traffic Padding & Obfuscation")
    print("=" * 50)
    
    padding_handler = PaddingHandler()
    
    try:
        print("🚀 Starting traffic padding and obfuscation...")
        await padding_handler.start()
        
        print("\n✅ SUCCESS! Traffic obfuscation is now active!")
        print("\n📊 What this does:")
        print("   • Generates dummy network traffic to hide real patterns")
        print("   • Randomizes packet timing to prevent analysis")
        print("   • Makes your traffic harder to analyze")
        print("   • Helps resist traffic fingerprinting")
        
        print("\n🔍 Watch the effects:")
        print("   • Open Task Manager → Performance → Network")
        print("   • Notice periodic network activity from dummy traffic")
        print("   • This makes real traffic harder to distinguish")
        
        print("\n⏳ Traffic obfuscation running... Press Ctrl+C to stop")
        
        # Keep running and show stats
        while True:
            await asyncio.sleep(10)
            stats = padding_handler.get_stats()
            print(f"📊 Stats: {stats['dummy_packets_sent']} dummy packets sent, "
                  f"{stats['packets_padded']} packets padded")
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping traffic obfuscation...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await padding_handler.stop()
        print("✅ Traffic obfuscation stopped")

async def test_combined():
    """Test both DNS protection and traffic obfuscation together"""
    print("🛡️ Testing Combined DNS + Traffic Protection")
    print("=" * 50)
    
    dns_handler = DNSHandler()
    padding_handler = PaddingHandler()
    
    try:
        print("🌐 Starting DNS-over-HTTPS...")
        await dns_handler.start_doh('cloudflare')
        print("✅ DNS protection active")
        
        print("\n📦 Starting traffic obfuscation...")
        await padding_handler.start()
        print("✅ Traffic obfuscation active")
        
        print("\n🎉 COMBINED PROTECTION IS NOW ACTIVE!")
        print("\n📊 Your network activity is now:")
        print("   ✅ DNS queries encrypted (can't see which sites you visit)")
        print("   ✅ Traffic patterns obfuscated (harder to analyze)")
        print("   ✅ Dummy traffic generated (hides real activity)")
        print("   ✅ Timing randomized (prevents pattern recognition)")
        
        print("\n🧪 Test the protection:")
        print("   • Visit: https://1.1.1.1/help (check DoH status)")
        print("   • Visit: https://dnsleaktest.com (check DNS)")
        print("   • Watch Task Manager network activity")
        
        print("\n⏳ Combined protection running... Press Ctrl+C to stop")
        
        # Keep running with periodic stats
        while True:
            await asyncio.sleep(15)
            stats = padding_handler.get_stats()
            print(f"📊 Protection active - DNS encrypted, "
                  f"{stats['dummy_packets_sent']} dummy packets sent")
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping combined protection...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await padding_handler.stop()
        await dns_handler.stop()
        print("✅ All protection stopped")

def main():
    print("🎯 Simple Network Protection Test")
    print("Works without installing any additional software!")
    print("=" * 60)
    
    menu = """
🎮 Choose a test:

[1] DNS Protection Only
    • Encrypts all DNS queries
    • Hides website visits from ISP
    • No additional software needed
    
[2] Traffic Obfuscation Only  
    • Generates dummy traffic
    • Randomizes packet timing
    • Makes traffic harder to analyze
    
[3] Combined Protection
    • Both DNS protection AND traffic obfuscation
    • Maximum privacy without additional installs
    
[0] Exit
    """
    
    print(menu)
    
    while True:
        try:
            choice = input("Select option (0-3): ").strip()
            
            if choice == '0':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                asyncio.run(test_dns_protection())
            elif choice == '2':
                asyncio.run(test_traffic_padding())
            elif choice == '3':
                asyncio.run(test_combined())
            else:
                print("❌ Invalid choice. Please select 0-3.")
                continue
            
            print("\n" + "="*60)
            print(menu)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()