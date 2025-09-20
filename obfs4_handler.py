"""
obfs4 Obfuscation Handler
Manages obfs4 transport for traffic obfuscation and censorship resistance
"""

import asyncio
import subprocess
import json
import os
import tempfile
import logging
import socket
import platform
from typing import Optional, Dict, List
import base64
import random

logger = logging.getLogger(__name__)

class Obfs4Handler:
    """
    Handles obfs4 transport protocol for traffic obfuscation
    Provides pluggable transport that makes traffic look like random data
    """
    
    def __init__(self):
        self.obfs4_process: Optional[asyncio.subprocess.Process] = None
        self.local_port: Optional[int] = None
        self.bridge_config: Dict = {}
        self.is_running = False
        self.temp_dir: Optional[str] = None
        
        # obfs4 configuration
        self.config = {
            'bridge_line': '',
            'cert': '',
            'iat-mode': '0',  # Inter-arrival time obfuscation mode
            'local_host': '127.0.0.1',
            'remote_host': '',
            'remote_port': 443,
            'node_id': '',
            'public_key': ''
        }
        
        # Platform-specific binary paths
        self.platform = platform.system()
        if self.platform == 'Windows':
            self.obfs4proxy_binary = 'obfs4proxy.exe'
        else:
            self.obfs4proxy_binary = 'obfs4proxy'
    
    async def load_bridge_config(self, bridge_line: str):
        """
        Load obfs4 bridge configuration
        
        Args:
            bridge_line: Bridge line in format "obfs4 IP:PORT cert=... iat-mode=..."
        """
        try:
            self.config['bridge_line'] = bridge_line
            
            # Parse bridge line
            parts = bridge_line.split()
            
            if len(parts) < 3 or parts[0] != 'obfs4':
                raise ValueError("Invalid obfs4 bridge line format")
            
            # Extract IP and port
            endpoint = parts[1]
            if ':' in endpoint:
                self.config['remote_host'], port_str = endpoint.rsplit(':', 1)
                self.config['remote_port'] = int(port_str)
            else:
                raise ValueError("Invalid endpoint format in bridge line")
            
            # Extract parameters
            for part in parts[2:]:
                if '=' in part:
                    key, value = part.split('=', 1)
                    if key == 'cert':
                        self.config['cert'] = value
                    elif key == 'iat-mode':
                        self.config['iat-mode'] = value
                    elif key == 'node-id':
                        self.config['node_id'] = value
                    elif key == 'public-key':
                        self.config['public_key'] = value
            
            if not self.config['cert']:
                raise ValueError("Certificate not found in bridge line")
            
            logger.info(f"obfs4 bridge configuration loaded: {self.config['remote_host']}:{self.config['remote_port']}")
            
        except Exception as e:
            logger.error(f"Failed to load obfs4 bridge configuration: {e}")
            raise
    
    async def set_bridge_config(self, host: str, port: int, cert: str, iat_mode: str = '0'):
        """
        Set obfs4 bridge configuration programmatically
        
        Args:
            host: Bridge host
            port: Bridge port
            cert: Bridge certificate
            iat_mode: Inter-arrival time mode
        """
        self.config.update({
            'remote_host': host,
            'remote_port': port,
            'cert': cert,
            'iat-mode': iat_mode
        })
        
        # Construct bridge line
        self.config['bridge_line'] = f"obfs4 {host}:{port} cert={cert} iat-mode={iat_mode}"
        
        logger.info(f"obfs4 bridge configuration set: {host}:{port}")
    
    async def start(self, local_port: Optional[int] = None):
        """
        Start obfs4 proxy
        
        Args:
            local_port: Local port to bind to (if None, find available port)
        """
        logger.info("Starting obfs4 proxy")
        
        try:
            # Validate configuration
            if not self.config['cert']:
                raise ValueError("obfs4 bridge configuration not loaded")
            
            # Find available local port
            if local_port is None:
                self.local_port = await self._find_available_port()
            else:
                self.local_port = local_port
            
            # Create temporary directory for obfs4 state
            self.temp_dir = tempfile.mkdtemp(prefix='obfs4_')
            
            # Start obfs4proxy process
            await self._start_obfs4proxy()
            
            # Verify proxy is working
            await self._verify_proxy()
            
            self.is_running = True
            logger.info(f"obfs4 proxy started on {self.config['local_host']}:{self.local_port}")
            
        except Exception as e:
            logger.error(f"Failed to start obfs4 proxy: {e}")
            await self.stop()
            raise
    
    async def _find_available_port(self, start_port: int = 9050) -> int:
        """Find an available local port"""
        for port in range(start_port, start_port + 1000):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('127.0.0.1', port))
                sock.close()
                return port
            except OSError:
                continue
        
        raise RuntimeError("No available ports found for obfs4 proxy")
    
    async def _start_obfs4proxy(self):
        """Start obfs4proxy process"""
        try:
            # Prepare environment variables
            env = os.environ.copy()
            env['TOR_PT_MANAGED_TRANSPORT_VER'] = '1'
            env['TOR_PT_CLIENT_TRANSPORTS'] = 'obfs4'
            env['TOR_PT_STATE_LOCATION'] = self.temp_dir
            env['TOR_PT_EXIT_ON_STDIN_CLOSE'] = '1'
            
            # Prepare command arguments
            cmd = [self.obfs4proxy_binary, '-enableLogging', '-logLevel', 'INFO']
            
            logger.debug(f"Starting obfs4proxy with command: {' '.join(cmd)}")
            
            # Start obfs4proxy process
            self.obfs4_process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.temp_dir
            )
            
            # Send configuration to obfs4proxy via stdin
            config_data = self._generate_pt_config()
            self.obfs4_process.stdin.write(config_data.encode())
            await self.obfs4_process.stdin.drain()
            
            # Wait for initialization
            await asyncio.sleep(2)
            
            # Check if process is still running
            if self.obfs4_process.returncode is not None:
                stdout, stderr = await self.obfs4_process.communicate()
                raise RuntimeError(f"obfs4proxy failed to start: {stderr.decode()}")
            
            logger.info("obfs4proxy process started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start obfs4proxy process: {e}")
            raise
    
    def _generate_pt_config(self) -> str:
        """Generate pluggable transport configuration"""
        config_lines = [
            "VERSION 1",
            f"CMETHOD obfs4 socks5 {self.config['local_host']}:{self.local_port}",
            "CMETHODS DONE"
        ]
        
        return '\n'.join(config_lines) + '\n'
    
    async def _verify_proxy(self):
        """Verify obfs4 proxy is working"""
        try:
            # Test SOCKS5 connection
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    # Try to connect to the SOCKS5 proxy
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(self.config['local_host'], self.local_port),
                        timeout=2.0
                    )
                    
                    writer.close()
                    await writer.wait_closed()
                    
                    logger.info("obfs4 proxy verification successful")
                    return
                    
                except (ConnectionRefusedError, asyncio.TimeoutError):
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(1)
                        continue
                    raise
            
            raise RuntimeError("obfs4 proxy verification failed")
            
        except Exception as e:
            logger.error(f"obfs4 proxy verification failed: {e}")
            raise
    
    async def create_bridge_config(self, bridges: List[str]) -> str:
        """
        Create bridge configuration file
        
        Args:
            bridges: List of bridge lines
            
        Returns:
            Path to created bridge configuration file
        """
        try:
            # Create temporary bridge configuration file
            fd, bridge_file = tempfile.mkstemp(suffix='.conf', prefix='bridges_')
            
            with os.fdopen(fd, 'w') as f:
                f.write("# obfs4 bridge configuration\n")
                f.write("# Generated automatically\n\n")
                
                for bridge in bridges:
                    f.write(f"Bridge {bridge}\n")
                
                f.write("\n# End of configuration\n")
            
            logger.info(f"Bridge configuration file created: {bridge_file}")
            return bridge_file
            
        except Exception as e:
            logger.error(f"Failed to create bridge configuration: {e}")
            raise
    
    async def get_sample_bridges(self) -> List[str]:
        """
        Get sample obfs4 bridges for testing
        
        Returns:
            List of sample bridge lines
        """
        # These are example bridges - in practice, you would get real bridges
        # from the Tor Project's bridge distribution system
        sample_bridges = [
            "obfs4 192.95.36.142:443 CDF2E852BF539B82BD10E27E9115A31734E378C2 cert=qUVQ0srL1JI/vO6V6m/24anYXiJD3QP2HgzUKQtQ7GRqqUvs7P+tG43RtAqdhLOALP7DJQ iat-mode=1",
            "obfs4 37.218.245.14:38224 D9A82D2F9C2F65A18407B1D2B764F130847F8B5D cert=bjRaMrr1BRiAW8IE9U5z27fQaYgOdD1XfFAqJmWI2ncgQn8iP/y8TGjTCbFeEfC3gSj7GQ iat-mode=0",
            "obfs4 85.31.186.98:443 00DC6C8430AB8FED9A5D0F9F3E8E4F0BB7E9B9BB cert=4R7xAx9LBK8AKFnIXmQ8F7QPqAoMJ7Q8D+TCzbT8zVmkM7/vGkwm5KS9z1gkZL4zFzXWAA iat-mode=0"
        ]
        
        return sample_bridges
    
    async def test_bridge_connectivity(self, bridge_line: str) -> bool:
        """
        Test connectivity to a specific bridge
        
        Args:
            bridge_line: Bridge line to test
            
        Returns:
            True if bridge is reachable, False otherwise
        """
        try:
            # Parse bridge line to get host and port
            parts = bridge_line.split()
            if len(parts) < 2:
                return False
            
            endpoint = parts[1]
            if ':' not in endpoint:
                return False
            
            host, port_str = endpoint.rsplit(':', 1)
            port = int(port_str)
            
            # Test TCP connectivity
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=10.0)
            
            writer.close()
            await writer.wait_closed()
            
            logger.info(f"Bridge connectivity test passed: {host}:{port}")
            return True
            
        except Exception as e:
            logger.debug(f"Bridge connectivity test failed: {e}")
            return False
    
    async def stop(self):
        """Stop obfs4 proxy"""
        logger.info("Stopping obfs4 proxy")
        
        try:
            # Terminate obfs4proxy process
            if self.obfs4_process:
                self.obfs4_process.terminate()
                try:
                    await asyncio.wait_for(self.obfs4_process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("obfs4proxy process did not terminate gracefully, killing")
                    self.obfs4_process.kill()
                    await self.obfs4_process.wait()
                
                self.obfs4_process = None
            
            # Clean up temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                self.temp_dir = None
            
            self.is_running = False
            self.local_port = None
            
            logger.info("obfs4 proxy stopped")
            
        except Exception as e:
            logger.error(f"Error stopping obfs4 proxy: {e}")
    
    def get_proxy_port(self) -> Optional[int]:
        """Get the local proxy port"""
        return self.local_port
    
    def get_proxy_host(self) -> str:
        """Get the local proxy host"""
        return self.config['local_host']
    
    def is_proxy_running(self) -> bool:
        """Check if proxy is running"""
        return self.is_running
    
    async def get_status(self) -> Dict:
        """
        Get obfs4 proxy status
        
        Returns:
            Dictionary with proxy status information
        """
        try:
            status = {
                'running': self.is_running,
                'local_host': self.config['local_host'],
                'local_port': self.local_port,
                'remote_host': self.config['remote_host'],
                'remote_port': self.config['remote_port'],
                'bridge_line': self.config['bridge_line']
            }
            
            if self.obfs4_process:
                status['process_running'] = self.obfs4_process.returncode is None
            else:
                status['process_running'] = False
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get obfs4 status: {e}")
            return {
                'running': False,
                'error': str(e)
            }
    
    async def reload_bridges(self, bridge_lines: List[str]):
        """
        Reload bridge configuration with new bridges
        
        Args:
            bridge_lines: List of new bridge lines
        """
        try:
            logger.info("Reloading obfs4 bridges")
            
            # Stop current proxy
            if self.is_running:
                await self.stop()
            
            # Select random bridge from the list
            if bridge_lines:
                selected_bridge = random.choice(bridge_lines)
                await self.load_bridge_config(selected_bridge)
                
                # Start with new bridge
                await self.start()
                
                logger.info(f"obfs4 bridges reloaded, using: {selected_bridge}")
            else:
                raise ValueError("No bridge lines provided")
            
        except Exception as e:
            logger.error(f"Failed to reload obfs4 bridges: {e}")
            raise
    
    def get_bridge_info(self) -> Dict:
        """
        Get current bridge information
        
        Returns:
            Dictionary with bridge information
        """
        return {
            'host': self.config['remote_host'],
            'port': self.config['remote_port'],
            'cert': self.config['cert'][:20] + '...' if self.config['cert'] else '',
            'iat_mode': self.config['iat-mode'],
            'bridge_line': self.config['bridge_line']
        }