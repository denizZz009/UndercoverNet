"""
Shadowsocks Handler for Multi-layer Architecture
Manages Shadowsocks SOCKS5 proxy for first hop obfuscation
"""

import asyncio
import subprocess
import json
import os
import tempfile
import logging
import socket
import platform
import base64
import hashlib
from typing import Optional, Dict, List
import random

logger = logging.getLogger(__name__)

class ShadowsocksHandler:
    """
    Handles Shadowsocks SOCKS5 proxy for traffic obfuscation
    Provides first hop that makes traffic appear as HTTPS
    """
    
    def __init__(self):
        self.ss_process: Optional[asyncio.subprocess.Process] = None
        self.local_port: Optional[int] = None
        self.is_running = False
        self.temp_dir: Optional[str] = None
        
        # Shadowsocks configuration
        self.config = {
            'server': '',
            'server_port': 8388,
            'local_address': '127.0.0.1',
            'local_port': 1080,
            'password': '',
            'method': 'aes-256-gcm',
            'timeout': 300,
            'plugin': '',
            'plugin_opts': ''
        }
        
        # Supported encryption methods
        self.encryption_methods = [
            'aes-256-gcm',
            'aes-256-cfb',
            'aes-192-gcm',
            'aes-192-cfb',
            'aes-128-gcm',
            'aes-128-cfb',
            'chacha20-ietf-poly1305',
            'xchacha20-ietf-poly1305'
        ]
        
        # Platform-specific binary paths
        self.platform = platform.system()
        if self.platform == 'Windows':
            self.ss_binary = 'ss-local.exe'
        else:
            self.ss_binary = 'ss-local'
    
    async def load_config(self, config_path: str):
        """
        Load Shadowsocks configuration from JSON file
        
        Args:
            config_path: Path to Shadowsocks configuration file
        """
        try:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Update configuration
            self.config.update(config_data)
            
            # Validate required fields
            required_fields = ['server', 'server_port', 'password', 'method']
            for field in required_fields:
                if not self.config.get(field):
                    raise ValueError(f"Required field '{field}' is missing")
            
            logger.info(f"Shadowsocks configuration loaded from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load Shadowsocks configuration: {e}")
            raise
    
    async def set_config(self, server: str, server_port: int, password: str, 
                        method: str = 'aes-256-gcm', plugin: str = '', plugin_opts: str = ''):
        """
        Set Shadowsocks configuration programmatically
        
        Args:
            server: Server address
            server_port: Server port
            password: Password
            method: Encryption method
            plugin: Plugin name (e.g., 'v2ray-plugin')
            plugin_opts: Plugin options
        """
        self.config.update({
            'server': server,
            'server_port': server_port,
            'password': password,
            'method': method,
            'plugin': plugin,
            'plugin_opts': plugin_opts
        })
        
        logger.info(f"Shadowsocks configuration set: {server}:{server_port} with {method}")
    
    async def start(self, local_port: Optional[int] = None):
        """
        Start Shadowsocks client
        
        Args:
            local_port: Local SOCKS5 port (if None, find available port)
        """
        logger.info("Starting Shadowsocks client")
        
        try:
            # Validate configuration
            await self._validate_config()
            
            # Find available local port
            if local_port is None:
                self.local_port = await self._find_available_port()
            else:
                self.local_port = local_port
            
            self.config['local_port'] = self.local_port
            
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix='shadowsocks_')
            
            # Create configuration file
            config_file = await self._create_config_file()
            
            # Start Shadowsocks process
            await self._start_shadowsocks_process(config_file)
            
            # Verify proxy is working
            await self._verify_proxy()
            
            self.is_running = True
            logger.info(f"Shadowsocks client started on {self.config['local_address']}:{self.local_port}")
            
        except Exception as e:
            logger.error(f"Failed to start Shadowsocks client: {e}")
            await self.stop()
            raise
    
    async def _validate_config(self):
        """Validate Shadowsocks configuration"""
        try:
            # Check required fields
            if not self.config['server']:
                raise ValueError("Server address is required")
            
            if not self.config['password']:
                raise ValueError("Password is required")
            
            if self.config['method'] not in self.encryption_methods:
                logger.warning(f"Encryption method {self.config['method']} may not be supported")
            
            # Validate port ranges
            if not (1 <= self.config['server_port'] <= 65535):
                raise ValueError("Invalid server port")
            
            logger.info("Shadowsocks configuration validated successfully")
            
        except Exception as e:
            logger.error(f"Shadowsocks configuration validation failed: {e}")
            raise
    
    async def _find_available_port(self, start_port: int = 1080) -> int:
        """Find an available local port"""
        for port in range(start_port, start_port + 1000):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('127.0.0.1', port))
                sock.close()
                return port
            except OSError:
                continue
        
        raise RuntimeError("No available ports found for Shadowsocks client")
    
    async def _create_config_file(self) -> str:
        """Create Shadowsocks configuration file"""
        try:
            config_path = os.path.join(self.temp_dir, 'shadowsocks.json')
            
            # Prepare configuration data
            config_data = {
                'server': self.config['server'],
                'server_port': self.config['server_port'],
                'local_address': self.config['local_address'],
                'local_port': self.config['local_port'],
                'password': self.config['password'],
                'method': self.config['method'],
                'timeout': self.config['timeout']
            }
            
            # Add plugin configuration if specified
            if self.config['plugin']:
                config_data['plugin'] = self.config['plugin']
                if self.config['plugin_opts']:
                    config_data['plugin_opts'] = self.config['plugin_opts']
            
            # Write configuration file
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Shadowsocks configuration file created: {config_path}")
            return config_path
            
        except Exception as e:
            logger.error(f"Failed to create Shadowsocks configuration file: {e}")
            raise
    
    async def _start_shadowsocks_process(self, config_file: str):
        """Start Shadowsocks client process"""
        try:
            # Prepare command
            cmd = [self.ss_binary, '-c', config_file, '-v']
            
            logger.debug(f"Starting Shadowsocks with command: {' '.join(cmd)}")
            
            # Start Shadowsocks process
            self.ss_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.temp_dir
            )
            
            # Wait for initialization
            await asyncio.sleep(3)
            
            # Check if process is still running
            if self.ss_process.returncode is not None:
                stdout, stderr = await self.ss_process.communicate()
                raise RuntimeError(f"Shadowsocks failed to start: {stderr.decode()}")
            
            logger.info("Shadowsocks client process started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Shadowsocks process: {e}")
            raise
    
    async def _verify_proxy(self):
        """Verify Shadowsocks SOCKS5 proxy is working"""
        try:
            # Test SOCKS5 connection
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    # Try to connect to the SOCKS5 proxy
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(self.config['local_address'], self.local_port),
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
                        logger.info("Shadowsocks SOCKS5 proxy verification successful")
                        return
                    
                except (ConnectionRefusedError, asyncio.TimeoutError):
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(1)
                        continue
                    raise
            
            raise RuntimeError("Shadowsocks SOCKS5 proxy verification failed")
            
        except Exception as e:
            logger.error(f"Shadowsocks proxy verification failed: {e}")
            raise
    
    async def test_server_connectivity(self, server: str, port: int, timeout: float = 10.0) -> bool:
        """
        Test connectivity to Shadowsocks server
        
        Args:
            server: Server address
            port: Server port
            timeout: Connection timeout
            
        Returns:
            True if server is reachable, False otherwise
        """
        try:
            # Test TCP connectivity
            future = asyncio.open_connection(server, port)
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            
            writer.close()
            await writer.wait_closed()
            
            logger.info(f"Shadowsocks server connectivity test passed: {server}:{port}")
            return True
            
        except Exception as e:
            logger.debug(f"Shadowsocks server connectivity test failed: {e}")
            return False
    
    async def generate_config(self, servers: List[Dict]) -> str:
        """
        Generate Shadowsocks configuration from server list
        
        Args:
            servers: List of server configurations
            
        Returns:
            Path to generated configuration file
        """
        try:
            if not servers:
                raise ValueError("No servers provided")
            
            # Select random server
            selected_server = random.choice(servers)
            
            # Update configuration
            await self.set_config(
                server=selected_server['server'],
                server_port=selected_server['server_port'],
                password=selected_server['password'],
                method=selected_server.get('method', 'aes-256-gcm'),
                plugin=selected_server.get('plugin', ''),
                plugin_opts=selected_server.get('plugin_opts', '')
            )
            
            # Create configuration file
            config_file = await self._create_config_file()
            
            logger.info(f"Shadowsocks configuration generated for server: {selected_server['server']}")
            return config_file
            
        except Exception as e:
            logger.error(f"Failed to generate Shadowsocks configuration: {e}")
            raise
    
    async def get_sample_servers(self) -> List[Dict]:
        """
        Get sample Shadowsocks server configurations
        
        Returns:
            List of sample server configurations
        """
        # These are example servers - in practice, you would get real servers
        # from a Shadowsocks provider or run your own servers
        sample_servers = [
            {
                'server': '198.199.101.152',
                'server_port': 8388,
                'password': 'u1rRWTssNv0p',
                'method': 'aes-256-cfb',
                'plugin': '',
                'plugin_opts': '',
                'remarks': 'Sample Server 1'
            },
            {
                'server': '207.148.22.139',
                'server_port': 8388,
                'password': 'u1rRWTssNv0p',
                'method': 'aes-256-cfb',
                'plugin': '',
                'plugin_opts': '',
                'remarks': 'Sample Server 2'
            }
        ]
        
        return sample_servers
    
    async def setup_with_plugin(self, plugin_name: str, plugin_opts: str = ''):
        """
        Setup Shadowsocks with plugin (e.g., v2ray-plugin for additional obfuscation)
        
        Args:
            plugin_name: Plugin name (e.g., 'v2ray-plugin')
            plugin_opts: Plugin options
        """
        try:
            self.config['plugin'] = plugin_name
            self.config['plugin_opts'] = plugin_opts
            
            if plugin_name == 'v2ray-plugin':
                # Common v2ray-plugin options for HTTPS obfuscation
                if not plugin_opts:
                    self.config['plugin_opts'] = 'mode=websocket;host=cloudflare.com;path=/;tls'
            
            logger.info(f"Shadowsocks plugin configured: {plugin_name}")
            
        except Exception as e:
            logger.error(f"Failed to setup Shadowsocks plugin: {e}")
            raise
    
    async def stop(self):
        """Stop Shadowsocks client"""
        logger.info("Stopping Shadowsocks client")
        
        try:
            # Terminate Shadowsocks process
            if self.ss_process:
                self.ss_process.terminate()
                try:
                    await asyncio.wait_for(self.ss_process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Shadowsocks process did not terminate gracefully, killing")
                    self.ss_process.kill()
                    await self.ss_process.wait()
                
                self.ss_process = None
            
            # Clean up temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                self.temp_dir = None
            
            self.is_running = False
            self.local_port = None
            
            logger.info("Shadowsocks client stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Shadowsocks client: {e}")
    
    def get_proxy_port(self) -> Optional[int]:
        """Get the local SOCKS5 proxy port"""
        return self.local_port
    
    def get_proxy_host(self) -> str:
        """Get the local proxy host"""
        return self.config['local_address']
    
    def is_proxy_running(self) -> bool:
        """Check if proxy is running"""
        return self.is_running
    
    async def get_status(self) -> Dict:
        """
        Get Shadowsocks client status
        
        Returns:
            Dictionary with client status information
        """
        try:
            status = {
                'running': self.is_running,
                'local_host': self.config['local_address'],
                'local_port': self.local_port,
                'server': self.config['server'],
                'server_port': self.config['server_port'],
                'method': self.config['method'],
                'plugin': self.config['plugin']
            }
            
            if self.ss_process:
                status['process_running'] = self.ss_process.returncode is None
            else:
                status['process_running'] = False
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get Shadowsocks status: {e}")
            return {
                'running': False,
                'error': str(e)
            }
    
    async def change_server(self, server_configs: List[Dict]):
        """
        Change to a different Shadowsocks server
        
        Args:
            server_configs: List of available server configurations
        """
        try:
            logger.info("Changing Shadowsocks server")
            
            # Stop current connection
            if self.is_running:
                await self.stop()
            
            # Select random server from available ones
            if server_configs:
                selected_server = random.choice(server_configs)
                
                # Update configuration
                await self.set_config(
                    server=selected_server['server'],
                    server_port=selected_server['server_port'],
                    password=selected_server['password'],
                    method=selected_server.get('method', 'aes-256-gcm'),
                    plugin=selected_server.get('plugin', ''),
                    plugin_opts=selected_server.get('plugin_opts', '')
                )
                
                # Start with new server
                await self.start()
                
                logger.info(f"Shadowsocks server changed to: {selected_server['server']}")
            else:
                raise ValueError("No server configurations provided")
            
        except Exception as e:
            logger.error(f"Failed to change Shadowsocks server: {e}")
            raise
    
    def get_server_info(self) -> Dict:
        """
        Get current server information
        
        Returns:
            Dictionary with server information
        """
        return {
            'server': self.config['server'],
            'server_port': self.config['server_port'],
            'method': self.config['method'],
            'plugin': self.config['plugin'],
            'local_port': self.local_port
        }
    
    async def test_proxy_performance(self) -> Dict:
        """
        Test Shadowsocks proxy performance
        
        Returns:
            Dictionary with performance metrics
        """
        try:
            if not self.is_running:
                return {'error': 'Proxy not running'}
            
            import time
            
            # Simple latency test
            start_time = time.time()
            
            # Test connection through proxy
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.config['local_address'], self.local_port),
                timeout=5.0
            )
            
            # Send SOCKS5 handshake
            handshake = b'\x05\x01\x00'
            writer.write(handshake)
            await writer.drain()
            
            # Read response
            response = await asyncio.wait_for(reader.read(2), timeout=5.0)
            
            writer.close()
            await writer.wait_closed()
            
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            
            return {
                'latency_ms': round(latency, 2),
                'status': 'healthy' if latency < 500 else 'slow'
            }
            
        except Exception as e:
            logger.error(f"Proxy performance test failed: {e}")
            return {
                'error': str(e),
                'status': 'error'
            }
