#!/usr/bin/env python3
"""
Integration Test Script for Network Obfuscation System
Tests basic functionality and module imports
"""

import sys
import os
import asyncio
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all modules can be imported successfully"""
    logger.info("Testing module imports...")
    
    try:
        from dns_handler import DNSHandler
        logger.info("✓ DNS handler imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import DNS handler: {e}")
        return False
    
    try:
        from firewall_handler import FirewallHandler
        logger.info("✓ Firewall handler imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import Firewall handler: {e}")
        return False
    
    try:
        from padding_handler import PaddingHandler
        logger.info("✓ Padding handler imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import Padding handler: {e}")
        return False
    
    try:
        from wireguard_handler import WireGuardHandler
        logger.info("✓ WireGuard handler imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import WireGuard handler: {e}")
        return False
    
    try:
        from obfs4_handler import Obfs4Handler
        logger.info("✓ obfs4 handler imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import obfs4 handler: {e}")
        return False
    
    try:
        from meek_handler import MeekHandler
        logger.info("✓ Meek handler imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import Meek handler: {e}")
        return False
    
    try:
        from shadowsocks_handler import ShadowsocksHandler
        logger.info("✓ Shadowsocks handler imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import Shadowsocks handler: {e}")
        return False
    
    return True

async def test_basic_functionality():
    """Test basic functionality of handlers"""
    logger.info("Testing basic functionality...")
    
    try:
        # Test DNS handler initialization
        from dns_handler import DNSHandler
        dns_handler = DNSHandler()
        logger.info("✓ DNS handler initialized")
        
        # Test firewall handler initialization  
        from firewall_handler import FirewallHandler
        firewall_handler = FirewallHandler()
        logger.info("✓ Firewall handler initialized")
        
        # Test padding handler initialization
        from padding_handler import PaddingHandler
        padding_handler = PaddingHandler()
        logger.info("✓ Padding handler initialized")
        
        # Test WireGuard handler initialization
        from wireguard_handler import WireGuardHandler
        wireguard_handler = WireGuardHandler()
        logger.info("✓ WireGuard handler initialized")
        
        # Test obfs4 handler initialization
        from obfs4_handler import Obfs4Handler
        obfs4_handler = Obfs4Handler()
        logger.info("✓ obfs4 handler initialized")
        
        # Test meek handler initialization
        from meek_handler import MeekHandler
        meek_handler = MeekHandler()
        logger.info("✓ Meek handler initialized")
        
        # Test Shadowsocks handler initialization
        from shadowsocks_handler import ShadowsocksHandler
        shadowsocks_handler = ShadowsocksHandler()
        logger.info("✓ Shadowsocks handler initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Basic functionality test failed: {e}")
        return False

def test_configuration_files():
    """Test if configuration files exist and are readable"""
    logger.info("Testing configuration files...")
    
    config_files = [
        'config.json',
        'wireguard_example.conf',
        'shadowsocks_example.json',
        'obfs4_bridges.conf'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                    if content:
                        logger.info(f"✓ {config_file} exists and is readable")
                    else:
                        logger.warning(f"⚠ {config_file} exists but is empty")
            except Exception as e:
                logger.error(f"✗ Failed to read {config_file}: {e}")
                return False
        else:
            logger.error(f"✗ Configuration file {config_file} not found")
            return False
    
    return True

def test_dependencies():
    """Test if required dependencies are available"""
    logger.info("Testing dependencies...")
    
    required_modules = [
        'asyncio',
        'aiohttp',
        'logging',
        'socket',
        'subprocess',
        'json',
        'configparser'
    ]
    
    optional_modules = [
        'scapy',
        'stem',
        'pydivert',
        'netfilterqueue'
    ]
    
    # Test required modules
    for module in required_modules:
        try:
            __import__(module)
            logger.info(f"✓ Required module {module} available")
        except ImportError:
            logger.error(f"✗ Required module {module} not available")
            return False
    
    # Test optional modules
    for module in optional_modules:
        try:
            __import__(module)
            logger.info(f"✓ Optional module {module} available")
        except ImportError:
            logger.warning(f"⚠ Optional module {module} not available")
    
    return True

async def main():
    """Main test function"""
    logger.info("Starting integration tests for Network Obfuscation System")
    logger.info("=" * 60)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Module imports
    if test_imports():
        tests_passed += 1
        logger.info("✓ Module import test PASSED")
    else:
        logger.error("✗ Module import test FAILED")
    
    logger.info("-" * 40)
    
    # Test 2: Basic functionality
    if await test_basic_functionality():
        tests_passed += 1
        logger.info("✓ Basic functionality test PASSED")
    else:
        logger.error("✗ Basic functionality test FAILED")
    
    logger.info("-" * 40)
    
    # Test 3: Configuration files
    if test_configuration_files():
        tests_passed += 1
        logger.info("✓ Configuration files test PASSED")
    else:
        logger.error("✗ Configuration files test FAILED")
    
    logger.info("-" * 40)
    
    # Test 4: Dependencies
    if test_dependencies():
        tests_passed += 1
        logger.info("✓ Dependencies test PASSED")
    else:
        logger.error("✗ Dependencies test FAILED")
    
    logger.info("=" * 60)
    logger.info(f"Integration tests completed: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        logger.info("🎉 All tests PASSED! The system is ready to use.")
        return True
    else:
        logger.error("❌ Some tests FAILED. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
