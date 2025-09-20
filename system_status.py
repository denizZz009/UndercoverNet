#!/usr/bin/env python3
"""
System Status Checker - Explains Implementation Gaps and Missing Components
This tool shows exactly what's working and what requires additional binaries
"""

import asyncio
import subprocess
import sys
import os
import platform
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class SystemStatusChecker:
    """Comprehensive system status and capability checker"""
    
    def __init__(self):
        self.platform = platform.system()
        self.results = {
            'python_modules': {},
            'external_binaries': {},
            'network_capabilities': {},
            'implementation_status': {}
        }
    
    def display_banner(self):
        """Display status checker banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🔍 SYSTEM STATUS CHECKER                   ║
║           Understanding Implementation Gaps & Missing         ║
║                       Components Analysis                    ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    async def check_python_modules(self):
        """Check Python module availability"""
        print("\n📦 PYTHON MODULES CHECK")
        print("=" * 50)
        
        required_modules = [
            ('asyncio', 'Core async functionality'),
            ('aiohttp', 'HTTP client for DNS-over-HTTPS'),
            ('socket', 'Basic networking'),
            ('subprocess', 'Process management'),
            ('logging', 'Application logging'),
            ('json', 'Configuration handling')
        ]
        
        optional_modules = [
            ('scapy', 'Advanced packet manipulation'),
            ('stem', 'Tor network control'),
            ('pydivert', 'Windows packet interception'),
            ('netfilterqueue', 'Linux packet filtering'),
            ('psutil', 'System monitoring'),
            ('dnspython', 'DNS utilities')
        ]
        
        print("🔧 Required Modules (needed for basic functionality):")
        for module, description in required_modules:
            try:
                __import__(module)
                print(f"   ✅ {module:<15} - {description}")
                self.results['python_modules'][module] = True
            except ImportError:
                print(f"   ❌ {module:<15} - {description} - MISSING!")
                self.results['python_modules'][module] = False
        
        print("\n🔧 Optional Modules (enhance functionality):")
        for module, description in optional_modules:
            try:
                __import__(module)
                print(f"   ✅ {module:<15} - {description}")
                self.results['python_modules'][module] = True
            except ImportError:
                print(f"   ⚠️  {module:<15} - {description} - not available")
                self.results['python_modules'][module] = False
    
    async def check_external_binaries(self):
        """Check external binary availability"""
        print("\n🛠️  EXTERNAL BINARIES CHECK")
        print("=" * 50)
        
        binaries = [
            ('ss-local', 'Shadowsocks client', 'shadowsocks-libev package'),
            ('tor', 'Tor anonymity network', 'tor package'),
            ('obfs4proxy', 'obfs4 traffic obfuscation', 'obfs4proxy package'),
            ('meek-client', 'meek domain fronting', 'tor-pluggable-transports'),
            ('wg', 'WireGuard VPN client', 'wireguard-tools package'),
            ('wg-quick', 'WireGuard quick setup', 'wireguard-tools package')
        ]
        
        print("🔍 Checking for required external binaries...")
        
        for binary, description, package in binaries:
            try:
                # Try to run binary with help/version flag
                if binary in ['ss-local']:
                    result = await self._run_command([binary, '-h'], timeout=3)
                elif binary in ['tor', 'wg']:
                    result = await self._run_command([binary, '--version'], timeout=3)
                elif binary in ['obfs4proxy', 'meek-client']:
                    result = await self._run_command([binary, '-version'], timeout=3)
                elif binary in ['wg-quick']:
                    result = await self._run_command([binary, '--help'], timeout=3)
                
                print(f"   ✅ {binary:<15} - {description}")
                self.results['external_binaries'][binary] = True
                
            except Exception as e:
                print(f"   ❌ {binary:<15} - {description} - NOT FOUND")
                print(f"      💡 Install with: {package}")
                self.results['external_binaries'][binary] = False
    
    async def check_network_capabilities(self):
        """Check network-related capabilities"""
        print("\n🌐 NETWORK CAPABILITIES CHECK")
        print("=" * 50)
        
        capabilities = [
            ('DNS-over-HTTPS', self._test_doh_capability),
            ('Traffic Padding', self._test_padding_capability),
            ('Firewall Control', self._test_firewall_capability),
            ('Admin/Root Access', self._test_admin_access)
        ]
        
        for capability, test_func in capabilities:
            try:
                result = await test_func()
                if result:
                    print(f"   ✅ {capability:<20} - Available")
                    self.results['network_capabilities'][capability] = True
                else:
                    print(f"   ⚠️  {capability:<20} - Limited")
                    self.results['network_capabilities'][capability] = False
            except Exception as e:
                print(f"   ❌ {capability:<20} - Error: {e}")
                self.results['network_capabilities'][capability] = False
    
    async def _test_doh_capability(self):
        """Test DNS-over-HTTPS capability"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get('https://1.1.1.1/dns-query', timeout=5) as response:
                    return response.status in [200, 400]  # 400 is expected without proper DNS query
        except:
            return False
    
    async def _test_padding_capability(self):
        """Test traffic padding capability"""
        try:
            # Test if we can create UDP sockets for dummy traffic
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.close()
            return True
        except:
            return False
    
    async def _test_firewall_capability(self):
        """Test firewall control capability"""
        try:
            if self.platform == 'Windows':
                result = await self._run_command(['netsh', 'advfirewall', 'show', 'allprofiles'], timeout=5)
                return 'Windows Defender Firewall' in result
            else:
                # Try iptables
                result = await self._run_command(['iptables', '--version'], timeout=3)
                return 'iptables' in result.lower()
        except:
            return False
    
    async def _test_admin_access(self):
        """Test administrator/root access"""
        if self.platform == 'Windows':
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                return False
        else:
            return os.geteuid() == 0
    
    async def analyze_implementation_status(self):
        """Analyze what's working and what has implementation gaps"""
        print("\n🔍 IMPLEMENTATION STATUS ANALYSIS")
        print("=" * 50)
        
        architectures = {
            'WireGuard + obfs4': {
                'requires': ['obfs4proxy', 'wg', 'wg-quick'],
                'python_modules': ['aiohttp', 'asyncio'],
                'description': 'VPN with traffic obfuscation'
            },
            'Tor + meek': {
                'requires': ['tor', 'meek-client'],
                'python_modules': ['aiohttp', 'stem'],
                'description': 'Anonymous routing with domain fronting'
            },
            'Multi-layer (Shadowsocks+WireGuard/Tor)': {
                'requires': ['ss-local', 'tor', 'wg'],
                'python_modules': ['aiohttp', 'asyncio'],
                'description': 'Multiple encryption layers'
            },
            'DNS-over-HTTPS': {
                'requires': [],
                'python_modules': ['aiohttp'],
                'description': 'Encrypted DNS queries'
            },
            'Traffic Obfuscation': {
                'requires': [],
                'python_modules': ['asyncio'],
                'description': 'Dummy traffic and padding'
            }
        }
        
        print("📊 Architecture Implementation Status:")
        
        for arch_name, arch_info in architectures.items():
            print(f"\\n🏗️  {arch_name}:")
            print(f"   📝 {arch_info['description']}")
            
            # Check binary requirements
            missing_binaries = []
            for binary in arch_info['requires']:
                if not self.results['external_binaries'].get(binary, False):
                    missing_binaries.append(binary)
            
            # Check Python module requirements
            missing_modules = []
            for module in arch_info['python_modules']:
                if not self.results['python_modules'].get(module, False):
                    missing_modules.append(module)
            
            if not missing_binaries and not missing_modules:
                print("   ✅ FULLY WORKING - All requirements met")
                self.results['implementation_status'][arch_name] = 'working'
            elif missing_binaries and not missing_modules:
                print(f"   ⚠️  PARTIAL - Missing binaries: {', '.join(missing_binaries)}")
                print("   🎭 Demo mode available (simulated functionality)")
                self.results['implementation_status'][arch_name] = 'demo'
            else:
                print(f"   ❌ NOT WORKING - Missing: {', '.join(missing_binaries + missing_modules)}")
                self.results['implementation_status'][arch_name] = 'broken'
    
    async def provide_installation_guidance(self):
        """Provide installation guidance for missing components"""
        print("\n💡 INSTALLATION GUIDANCE")
        print("=" * 50)
        
        missing_binaries = [k for k, v in self.results['external_binaries'].items() if not v]
        
        if not missing_binaries:
            print("🎉 All external binaries are available!")
            return
        
        print("📥 To install missing components:")
        
        if self.platform == 'Windows':
            print("\\n🪟 Windows Installation:")
            print("   1. Install Chocolatey package manager:")
            print("      Set-ExecutionPolicy Bypass -Scope Process -Force;")
            print("      [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;")
            print("      iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))")
            print("\\n   2. Install required packages:")
            if 'tor' in missing_binaries:
                print("      choco install tor")
            if 'ss-local' in missing_binaries:
                print("      choco install shadowsocks  # or install shadowsocks-libev manually")
            if 'wg' in missing_binaries:
                print("      choco install wireguard")
            if 'obfs4proxy' in missing_binaries:
                print("      # Download from: https://github.com/Yawning/obfs4")
        
        elif self.platform == 'Linux':
            print("\\n🐧 Linux Installation (Ubuntu/Debian):")
            install_cmd = "sudo apt update && sudo apt install "
            packages = []
            if 'tor' in missing_binaries:
                packages.append('tor')
            if 'ss-local' in missing_binaries:
                packages.append('shadowsocks-libev')
            if 'wg' in missing_binaries:
                packages.append('wireguard-tools')
            if 'obfs4proxy' in missing_binaries:
                packages.append('obfs4proxy')
            
            if packages:
                print(f"   {install_cmd}{' '.join(packages)}")
        
        elif self.platform == 'Darwin':  # macOS
            print("\\n🍎 macOS Installation:")
            print("   1. Install Homebrew:")
            print("      /bin/bash -c '$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)'")
            print("\\n   2. Install packages:")
            if 'tor' in missing_binaries:
                print("      brew install tor")
            if 'ss-local' in missing_binaries:
                print("      brew install shadowsocks-libev")
            if 'wg' in missing_binaries:
                print("      brew install wireguard-tools")
    
    async def explain_multi_layer_issues(self):
        """Specifically explain multi-layer encryption issues"""
        print("\\n🔍 MULTI-LAYER ENCRYPTION ANALYSIS")
        print("=" * 50)
        
        print("❓ WHY 'Multi-layer encryption - Most layers not working'?")
        print("\\n📋 Multi-layer architecture requires chaining multiple proxies:")
        print("   Layer 1: Shadowsocks (HTTPS-like traffic) → requires 'ss-local'")
        print("   Layer 2: WireGuard or Tor over Shadowsocks → requires 'wg' or 'tor'")
        print("   Layer 3: DNS-over-HTTPS proxy → ✅ works (Python only)")
        print("   Layer 4: Traffic obfuscation → ✅ works (Python only)")
        
        # Count working layers
        working_layers = 2  # DNS and traffic always work
        
        if self.results['external_binaries'].get('ss-local', False):
            working_layers += 1
            print("   ✅ Shadowsocks layer: WORKING")
        else:
            print("   ❌ Shadowsocks layer: MISSING ss-local binary")
        
        if self.results['external_binaries'].get('wg', False) or self.results['external_binaries'].get('tor', False):
            working_layers += 1
            available = []
            if self.results['external_binaries'].get('wg', False):
                available.append('WireGuard')
            if self.results['external_binaries'].get('tor', False):
                available.append('Tor')
            print(f"   ✅ Second layer: {'/'.join(available)} available")
        else:
            print("   ❌ Second layer: Missing both 'wg' and 'tor' binaries")
        
        print(f"\\n📊 Current Status: {working_layers}/4 layers working")
        
        if working_layers == 4:
            print("🎉 Full multi-layer encryption available!")
        elif working_layers >= 2:
            print("⚠️  Partial functionality - some layers in demo mode")
            print("💡 Install missing binaries for full multi-layer encryption")
        else:
            print("❌ Limited functionality - mostly demo mode")
    
    async def display_summary(self):
        """Display comprehensive summary"""
        print("\\n📊 COMPREHENSIVE SYSTEM SUMMARY")
        print("=" * 50)
        
        # Count working components
        working_modules = sum(self.results['python_modules'].values())
        total_modules = len(self.results['python_modules'])
        
        working_binaries = sum(self.results['external_binaries'].values())
        total_binaries = len(self.results['external_binaries'])
        
        working_net = sum(self.results['network_capabilities'].values())
        total_net = len(self.results['network_capabilities'])
        
        print(f"📦 Python Modules: {working_modules}/{total_modules} available")
        print(f"🛠️  External Binaries: {working_binaries}/{total_binaries} available")
        print(f"🌐 Network Capabilities: {working_net}/{total_net} available")
        
        print("\\n🎯 WHAT WORKS RIGHT NOW:")
        if self.results['implementation_status'].get('DNS-over-HTTPS') != 'broken':
            print("   ✅ DNS-over-HTTPS encryption (hides website visits from ISP)")
        if self.results['implementation_status'].get('Traffic Obfuscation') != 'broken':
            print("   ✅ Traffic obfuscation (dummy traffic, timing randomization)")
        
        print("\\n⚠️  WHAT HAS IMPLEMENTATION GAPS:")
        gaps = []
        if working_binaries < total_binaries:
            gaps.append(f"Missing {total_binaries - working_binaries} external binaries")
        if working_modules < total_modules:
            gaps.append(f"Missing {total_modules - working_modules} Python modules")
        
        for gap in gaps:
            print(f"   ⚠️  {gap}")
        
        print("\\n💡 RECOMMENDATION:")
        if working_binaries >= total_binaries * 0.5:
            print("   📈 Install remaining binaries for full functionality")
        else:
            print("   🎭 Use demo mode to understand the architecture")
            print("   📥 Install binaries gradually as needed")
        
        print("\\n🎮 NEXT STEPS:")
        print("   1. Run 'python simple_test.py' to test working features")
        print("   2. Run 'python main.py' and try multi-layer with demo mode")
        print("   3. Install missing binaries for full functionality")
        print("   4. Re-run this status checker to verify installations")
    
    async def _run_command(self, cmd, timeout=10):
        """Helper to run system commands with timeout"""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return stdout.decode() + stderr.decode()
        except asyncio.TimeoutError:
            proc.kill()
            raise Exception("Command timeout")
        except FileNotFoundError:
            raise Exception("Binary not found")
    
    async def run_full_check(self):
        """Run comprehensive system check"""
        self.display_banner()
        
        await self.check_python_modules()
        await self.check_external_binaries()
        await self.check_network_capabilities()
        await self.analyze_implementation_status()
        await self.explain_multi_layer_issues()
        await self.provide_installation_guidance()
        await self.display_summary()
        
        print("\\n" + "=" * 60)
        print("🔍 System analysis complete! Use this info to understand gaps.")

def main():
    """Entry point"""
    checker = SystemStatusChecker()
    try:
        asyncio.run(checker.run_full_check())
    except KeyboardInterrupt:
        print("\\n👋 Status check interrupted.")

if __name__ == "__main__":
    main()