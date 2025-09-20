"""
Meek Handler for Domain Fronting with Tor
Implements meek pluggable transport for censorship circumvention
"""

import asyncio
import subprocess
import json
import os
import tempfile
import logging
import socket
import platform
import aiohttp
from typing import Optional, Dict, List, Tuple
import random

logger = logging.getLogger(__name__)

class MeekHandler:
    """
    Handles meek pluggable transport for domain fronting
    Makes Tor traffic appear as regular HTTPS requests to CDNs
    """
    
    def __init__(self):
        self.meek_process: Optional[asyncio.subprocess.Process] = None
        self.tor_process: Optional[asyncio.subprocess.Process] = None
        self.local_port: Optional[int] = None
        self.tor_socks_port: Optional[int] = None
        self.is_running = False
        self.temp_dir: Optional[str] = None
        
        # meek configuration
        self.config = {
            'front_domain': 'cdn.sstatic.net',  # Stack Overflow CDN (common choice)
            'meek_host': 'meek.azureedge.net',  # Azure CDN endpoint
            'local_host': '127.0.0.1',
            'url_path': '/',
            'utls': 'HelloChrome_Auto'  # TLS fingerprint to mimic
        }
        
        # Supported domain fronting providers
        self.fronting_providers = {
            'azure': {
                'front_domain': 'ajax.aspnetcdn.com',
                'meek_host': 'meek.azureedge.net',
                'description': 'Microsoft Azure CDN'
            },
            'cloudflare': {
                'front_domain': 'cdnjs.cloudflare.com',
                'meek_host': 'meek.bamsoftware.com',
                'description': 'Cloudflare CDN'
            },
            'amazon': {
                'front_domain': 'd2zfqthxsdq309.cloudfront.net',
                'meek_host': 'meek.bamsoftware.com',
                'description': 'Amazon CloudFront'
            },
            'google': {
                'front_domain': 'www.google.com',
                'meek_host': 'meek.bamsoftware.com',
                'description': 'Google Services'
            }
        }
        
        # Platform-specific binary paths
        self.platform = platform.system()
        if self.platform == 'Windows':
            self.meek_binary = 'meek-client.exe'
            self.tor_binary = 'tor.exe'
        else:
            self.meek_binary = 'meek-client'
            self.tor_binary = 'tor'
    
    async def set_fronting_provider(self, provider: str):
        """
        Set domain fronting provider
        
        Args:
            provider: Provider name (azure, cloudflare, amazon, google)
        """
        if provider not in self.fronting_providers:
            raise ValueError(f"Unknown fronting provider: {provider}")
        
        provider_config = self.fronting_providers[provider]
        self.config.update({
            'front_domain': provider_config['front_domain'],
            'meek_host': provider_config['meek_host']
        })
        
        logger.info(f"Domain fronting provider set to: {provider} ({provider_config['description']})")
    
    async def start(self, provider: str = 'azure'):
        """
        Start meek transport
        
        Args:
            provider: Domain fronting provider to use
        """
        logger.info(f"Starting meek transport with {provider} domain fronting")
        
        try:
            # Set fronting provider
            await self.set_fronting_provider(provider)
            
            # Find available ports
            self.local_port = await self._find_available_port(9050)
            self.tor_socks_port = await self._find_available_port(9051)
            
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix='meek_')
            
            # Start meek client
            await self._start_meek_client()
            
            # Verify meek is working
            await self._verify_meek()
            
            self.is_running = True
            logger.info(f"meek transport started on {self.config['local_host']}:{self.local_port}")
            
        except Exception as e:
            logger.error(f"Failed to start meek transport: {e}")
            await self.stop()
            raise
    
    async def start_tor_over_meek(self):
        """Start Tor using meek as transport"""
        logger.info("Starting Tor over meek transport")
        
        try:
            if not self.is_running:
                raise RuntimeError("meek transport must be started first")
            
            # Create Tor configuration
            tor_config = await self._create_tor_config()
            
            # Start Tor process
            await self._start_tor_process(tor_config)
            
            # Verify Tor connection
            await self._verify_tor_connection()
            
            logger.info(f"Tor over meek started successfully on SOCKS port {self.tor_socks_port}")
            
        except Exception as e:
            logger.error(f"Failed to start Tor over meek: {e}")
            raise
    
    async def start_tor_over_proxy(self, proxy_port: int, proxy_host: str = '127.0.0.1'):
        """
        Start Tor over existing proxy (for multi-layer architecture)
        
        Args:
            proxy_port: Existing proxy port
            proxy_host: Existing proxy host
        """
        logger.info(f"Starting Tor over proxy {proxy_host}:{proxy_port}")
        
        try:
            # Find available port for Tor SOCKS
            self.tor_socks_port = await self._find_available_port(9051)
            
            # Create temporary directory if not exists
            if not self.temp_dir:
                self.temp_dir = tempfile.mkdtemp(prefix='tor_proxy_')
            
            # Create Tor configuration for proxy use
            tor_config = await self._create_tor_proxy_config(proxy_host, proxy_port)
            
            # Start Tor process
            await self._start_tor_process(tor_config)
            
            # Verify Tor connection
            await self._verify_tor_connection()
            
            logger.info(f"Tor over proxy started successfully on SOCKS port {self.tor_socks_port}")
            
        except Exception as e:
            logger.error(f"Failed to start Tor over proxy: {e}")
            raise
    
    async def _find_available_port(self, start_port: int) -> int:
        """Find an available local port"""
        for port in range(start_port, start_port + 1000):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('127.0.0.1', port))
                sock.close()
                return port
            except OSError:
                continue
        
        raise RuntimeError(f"No available ports found starting from {start_port}")
    
    async def _start_meek_client(self):
        """Start meek-client process"""
        try:
            # Prepare meek-client command
            cmd = [
                self.meek_binary,
                '--url', f"https://{self.config['front_domain']}{self.config['url_path']}",
                '--front', self.config['front_domain'],
                '--listen', f"{self.config['local_host']}:{self.local_port}",
                '--log-level', 'INFO'
            ]
            
            # Add platform-specific options
            if self.platform != 'Windows':
                cmd.extend(['--helper', 'meek-server'])
            
            logger.debug(f"Starting meek-client with command: {' '.join(cmd)}")
            
            # Start meek-client process
            self.meek_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.temp_dir
            )
            
            # Wait for initialization
            await asyncio.sleep(3)
            
            # Check if process is still running
            if self.meek_process.returncode is not None:
                stdout, stderr = await self.meek_process.communicate()
                raise RuntimeError(f"meek-client failed to start: {stderr.decode()}")
            
            logger.info("meek-client process started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start meek-client process: {e}")
            raise
    
    async def _verify_meek(self):
        """Verify meek transport is working"""
        try:
            # Test HTTP CONNECT through meek proxy
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    # Try to connect to the meek proxy
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(self.config['local_host'], self.local_port),
                        timeout=3.0
                    )
                    
                    # Send HTTP CONNECT request
                    connect_request = f"CONNECT www.google.com:80 HTTP/1.1\r\nHost: www.google.com:80\r\n\r\n"
                    writer.write(connect_request.encode())
                    await writer.drain()
                    
                    # Read response
                    response = await asyncio.wait_for(reader.read(1024), timeout=5.0)
                    
                    writer.close()
                    await writer.wait_closed()
                    
                    if b"200" in response:
                        logger.info("meek transport verification successful")
                        return
                    
                except (ConnectionRefusedError, asyncio.TimeoutError):
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(1)
                        continue
                    raise
            
            raise RuntimeError("meek transport verification failed")
            
        except Exception as e:
            logger.error(f"meek transport verification failed: {e}")
            raise
    
    async def _create_tor_config(self) -> str:
        """Create Tor configuration file for meek transport"""
        try:
            config_path = os.path.join(self.temp_dir, 'torrc')
            
            config_content = f"""
# Tor configuration for meek transport
DataDirectory {self.temp_dir}/tor_data
Log notice file {self.temp_dir}/tor.log

# SOCKS proxy
SocksPort {self.tor_socks_port}
SocksPolicy accept 127.0.0.1/8
SocksPolicy reject *

# Control port (disabled for security)
ControlPort 0

# Disable automatic circuit building
__DisablePredictedCircuits 1

# Use meek transport
UseBridges 1
ClientTransportPlugin meek exec {self.meek_binary}

# Bridge configuration (using meek)
Bridge meek {self.config['local_host']}:{self.local_port}

# Security settings
AvoidDiskWrites 1
SafeLogging 1
"""
            
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            logger.info(f"Tor configuration created: {config_path}")
            return config_path
            
        except Exception as e:
            logger.error(f"Failed to create Tor configuration: {e}")
            raise
    
    async def _create_tor_proxy_config(self, proxy_host: str, proxy_port: int) -> str:
        """Create Tor configuration for use over existing proxy"""
        try:
            config_path = os.path.join(self.temp_dir, 'torrc')
            
            config_content = f"""
# Tor configuration for proxy use
DataDirectory {self.temp_dir}/tor_data
Log notice file {self.temp_dir}/tor.log

# SOCKS proxy
SocksPort {self.tor_socks_port}
SocksPolicy accept 127.0.0.1/8
SocksPolicy reject *

# Control port (disabled for security)
ControlPort 0

# Use SOCKS5 proxy for all connections
Socks5Proxy {proxy_host}:{proxy_port}

# Security settings
AvoidDiskWrites 1
SafeLogging 1
"""
            
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            logger.info(f"Tor proxy configuration created: {config_path}")
            return config_path
            
        except Exception as e:
            logger.error(f"Failed to create Tor proxy configuration: {e}")
            raise
    
    async def _start_tor_process(self, config_path: str):
        """Start Tor process with given configuration"""
        try:
            # Prepare Tor command
            cmd = [self.tor_binary, '-f', config_path]
            
            logger.debug(f"Starting Tor with command: {' '.join(cmd)}")
            
            # Start Tor process
            self.tor_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.temp_dir
            )
            
            # Wait for Tor to initialize
            await asyncio.sleep(10)
            
            # Check if process is still running
            if self.tor_process.returncode is not None:
                stdout, stderr = await self.tor_process.communicate()
                raise RuntimeError(f"Tor failed to start: {stderr.decode()}")
            
            logger.info("Tor process started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Tor process: {e}")
            raise
    
    async def _verify_tor_connection(self):
        """Verify Tor SOCKS proxy is working"""
        try:
            # Test SOCKS5 connection
            max_attempts = 15
            for attempt in range(max_attempts):
                try:
                    # Create SOCKS5 connection
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(self.config['local_host'], self.tor_socks_port),
                        timeout=3.0
                    )
                    
                    # Send SOCKS5 handshake
                    # Version 5, 1 method, no auth
                    handshake = b'\x05\x01\x00'
                    writer.write(handshake)
                    await writer.drain()
                    
                    # Read response
                    response = await asyncio.wait_for(reader.read(2), timeout=3.0)
                    
                    writer.close()
                    await writer.wait_closed()
                    
                    if response == b'\x05\x00':
                        logger.info("Tor SOCKS5 proxy verification successful")
                        return
                    
                except (ConnectionRefusedError, asyncio.TimeoutError):
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(2)
                        continue
                    raise
            
            raise RuntimeError("Tor SOCKS5 proxy verification failed")
            
        except Exception as e:
            logger.error(f"Tor SOCKS5 proxy verification failed: {e}")
            raise
    
    async def test_domain_fronting(self, provider: str) -> bool:
        """
        Test domain fronting capability with specific provider
        
        Args:
            provider: Provider to test
            
        Returns:
            True if domain fronting works, False otherwise
        """
        try:
            if provider not in self.fronting_providers:
                return False
            
            provider_config = self.fronting_providers[provider]
            
            # Test HTTP request with domain fronting
            timeout = aiohttp.ClientTimeout(total=10)
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                headers = {
                    'Host': provider_config['meek_host'],
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                url = f"https://{provider_config['front_domain']}/"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"Domain fronting test successful for {provider}")
                        return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Domain fronting test failed for {provider}: {e}")
            return False
    
    async def get_working_providers(self) -> List[str]:
        """
        Test all providers and return list of working ones
        
        Returns:
            List of working provider names
        """
        working_providers = []
        
        for provider in self.fronting_providers:
            if await self.test_domain_fronting(provider):
                working_providers.append(provider)
        
        logger.info(f"Working domain fronting providers: {working_providers}")
        return working_providers
    
    async def stop(self):
        """Stop meek transport and Tor"""
        logger.info("Stopping meek transport and Tor")
        
        try:
            # Stop Tor process
            if self.tor_process:
                self.tor_process.terminate()
                try:
                    await asyncio.wait_for(self.tor_process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Tor process did not terminate gracefully, killing")
                    self.tor_process.kill()
                    await self.tor_process.wait()
                
                self.tor_process = None
            
            # Stop meek process
            if self.meek_process:
                self.meek_process.terminate()
                try:
                    await asyncio.wait_for(self.meek_process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("meek process did not terminate gracefully, killing")
                    self.meek_process.kill()
                    await self.meek_process.wait()
                
                self.meek_process = None
            
            # Clean up temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                self.temp_dir = None
            
            self.is_running = False
            self.local_port = None
            self.tor_socks_port = None
            
            logger.info("meek transport and Tor stopped")
            
        except Exception as e:
            logger.error(f"Error stopping meek transport: {e}")
    
    def get_socks_port(self) -> Optional[int]:
        """Get Tor SOCKS proxy port"""
        return self.tor_socks_port
    
    def get_meek_port(self) -> Optional[int]:
        """Get meek local port"""
        return self.local_port
    
    def is_transport_running(self) -> bool:
        """Check if meek transport is running"""
        return self.is_running
    
    async def get_status(self) -> Dict:
        """
        Get meek transport status
        
        Returns:
            Dictionary with transport status information
        """
        try:
            status = {
                'meek_running': self.is_running,
                'tor_running': self.tor_process is not None and self.tor_process.returncode is None,
                'meek_port': self.local_port,
                'tor_socks_port': self.tor_socks_port,
                'front_domain': self.config['front_domain'],
                'meek_host': self.config['meek_host']
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get meek status: {e}")
            return {
                'meek_running': False,
                'tor_running': False,
                'error': str(e)
            }
    
    async def change_circuit(self):
        """Request new Tor circuit (simplified implementation)"""
        try:
            if not self.tor_process or self.tor_process.returncode is not None:
                logger.warning("Cannot change circuit: Tor is not running")
                return
            
            # In a full implementation, you would use Tor's control protocol
            # For now, we restart Tor to get a new circuit
            logger.info("Requesting new Tor circuit by restarting Tor")
            
            # Stop Tor
            if self.tor_process:
                self.tor_process.terminate()
                await self.tor_process.wait()
            
            # Create new Tor configuration
            tor_config = await self._create_tor_config()
            
            # Start Tor again
            await self._start_tor_process(tor_config)
            await self._verify_tor_connection()
            
            logger.info("New Tor circuit established")
            
        except Exception as e:
            logger.error(f"Failed to change Tor circuit: {e}")
    
    def get_fronting_info(self) -> Dict:
        """
        Get current domain fronting information
        
        Returns:
            Dictionary with fronting configuration
        """
        return {
            'front_domain': self.config['front_domain'],
            'meek_host': self.config['meek_host'],
            'local_port': self.local_port,
            'providers': list(self.fronting_providers.keys())
        }
