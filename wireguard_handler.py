"""
WireGuard VPN Connection Handler
Manages WireGuard VPN connections with support for proxy routing
"""

import asyncio
import subprocess
import json
import os
import tempfile
import logging
import platform
import socket
from typing import Optional, Dict, List
import ipaddress
import configparser

logger = logging.getLogger(__name__)

class WireGuardHandler:
    """
    Handles WireGuard VPN connections with support for:
    - Direct WireGuard connections
    - WireGuard over obfs4 proxy
    - WireGuard over SOCKS5 proxy
    """
    
    def __init__(self):
        self.config_file: Optional[str] = None
        self.interface_name: Optional[str] = None
        self.is_connected = False
        self.original_routes: List[Dict] = []
        self.proxy_settings: Optional[Dict] = None
        
        # WireGuard configuration
        self.config = {
            'Interface': {
                'PrivateKey': '',
                'Address': '',
                'DNS': '1.1.1.1,8.8.8.8'
            },
            'Peer': {
                'PublicKey': '',
                'Endpoint': '',
                'AllowedIPs': '0.0.0.0/0,::/0',
                'PersistentKeepalive': '25'
            }
        }
        
        # Platform-specific settings
        self.platform = platform.system()
        if self.platform == 'Windows':
            self.wg_binary = 'wg.exe'
            self.wg_quick_binary = 'wg-quick.exe'
        else:
            self.wg_binary = 'wg'
            self.wg_quick_binary = 'wg-quick'
    
    async def load_config(self, config_path: str):
        """
        Load WireGuard configuration from file
        
        Args:
            config_path: Path to WireGuard configuration file
        """
        try:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            # Parse WireGuard configuration
            config = configparser.ConfigParser()
            config.read(config_path)
            
            # Extract configuration
            if 'Interface' in config:
                interface_section = config['Interface']
                self.config['Interface'].update({
                    'PrivateKey': interface_section.get('PrivateKey', ''),
                    'Address': interface_section.get('Address', ''),
                    'DNS': interface_section.get('DNS', '1.1.1.1,8.8.8.8')
                })
            
            if 'Peer' in config:
                peer_section = config['Peer']
                self.config['Peer'].update({
                    'PublicKey': peer_section.get('PublicKey', ''),
                    'Endpoint': peer_section.get('Endpoint', ''),
                    'AllowedIPs': peer_section.get('AllowedIPs', '0.0.0.0/0,::/0'),
                    'PersistentKeepalive': peer_section.get('PersistentKeepalive', '25')
                })
            
            logger.info(f"WireGuard configuration loaded from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load WireGuard configuration: {e}")
            raise
    
    async def start(self, interface_name: str = 'wg0'):
        """
        Start WireGuard VPN connection
        
        Args:
            interface_name: WireGuard interface name
        """
        logger.info(f"Starting WireGuard VPN connection on interface {interface_name}")
        
        self.interface_name = interface_name
        
        try:
            # Validate configuration
            await self._validate_config()
            
            # Create temporary configuration file
            self.config_file = await self._create_config_file()
            
            # Backup current routes
            await self._backup_routes()
            
            # Start WireGuard interface
            await self._start_interface()
            
            # Verify connection
            await self._verify_connection()
            
            self.is_connected = True
            logger.info("WireGuard VPN connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to start WireGuard VPN: {e}")
            await self.stop()
            raise
    
    async def start_over_obfs4(self, obfs4_port: int, obfs4_host: str = '127.0.0.1'):
        """
        Start WireGuard VPN over obfs4 proxy
        
        Args:
            obfs4_port: obfs4 proxy port
            obfs4_host: obfs4 proxy host
        """
        logger.info(f"Starting WireGuard over obfs4 proxy {obfs4_host}:{obfs4_port}")
        
        self.proxy_settings = {
            'type': 'obfs4',
            'host': obfs4_host,
            'port': obfs4_port
        }
        
        try:
            # Modify endpoint to use obfs4 proxy
            await self._configure_proxy_endpoint()
            
            # Start WireGuard with proxy configuration
            await self.start()
            
            logger.info("WireGuard over obfs4 connection established")
            
        except Exception as e:
            logger.error(f"Failed to start WireGuard over obfs4: {e}")
            raise
    
    async def start_over_proxy(self, proxy_port: int, proxy_host: str = '127.0.0.1', proxy_type: str = 'socks5'):
        """
        Start WireGuard VPN over SOCKS5 proxy
        
        Args:
            proxy_port: SOCKS5 proxy port
            proxy_host: SOCKS5 proxy host
            proxy_type: Proxy type (socks5, http)
        """
        logger.info(f"Starting WireGuard over {proxy_type} proxy {proxy_host}:{proxy_port}")
        
        self.proxy_settings = {
            'type': proxy_type,
            'host': proxy_host,
            'port': proxy_port
        }
        
        try:
            # Configure WireGuard to use proxy
            await self._configure_proxy_endpoint()
            
            # Start WireGuard with proxy configuration
            await self.start()
            
            logger.info(f"WireGuard over {proxy_type} connection established")
            
        except Exception as e:
            logger.error(f"Failed to start WireGuard over {proxy_type}: {e}")
            raise
    
    async def _validate_config(self):
        """Validate WireGuard configuration"""
        try:
            # Check required fields
            if not self.config['Interface']['PrivateKey']:
                raise ValueError("Interface PrivateKey is required")
            
            if not self.config['Interface']['Address']:
                raise ValueError("Interface Address is required")
            
            if not self.config['Peer']['PublicKey']:
                raise ValueError("Peer PublicKey is required")
            
            if not self.config['Peer']['Endpoint']:
                raise ValueError("Peer Endpoint is required")
            
            # Validate IP addresses
            addresses = self.config['Interface']['Address'].split(',')
            for addr in addresses:
                ipaddress.ip_interface(addr.strip())
            
            # Validate allowed IPs
            allowed_ips = self.config['Peer']['AllowedIPs'].split(',')
            for ip in allowed_ips:
                if ip.strip() != '::/0':  # Skip IPv6 all
                    ipaddress.ip_network(ip.strip(), strict=False)
            
            logger.info("WireGuard configuration validated successfully")
            
        except Exception as e:
            logger.error(f"WireGuard configuration validation failed: {e}")
            raise
    
    async def _create_config_file(self) -> str:
        """Create temporary WireGuard configuration file"""
        try:
            # Create temporary file
            fd, config_path = tempfile.mkstemp(suffix='.conf', prefix='wg_')
            
            with os.fdopen(fd, 'w') as f:
                # Write Interface section
                f.write("[Interface]\n")
                f.write(f"PrivateKey = {self.config['Interface']['PrivateKey']}\n")
                f.write(f"Address = {self.config['Interface']['Address']}\n")
                f.write(f"DNS = {self.config['Interface']['DNS']}\n")
                
                # Add platform-specific interface settings
                if self.platform == 'Linux':
                    f.write("PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth+ -j MASQUERADE\n")
                    f.write("PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth+ -j MASQUERADE\n")
                
                f.write("\n")
                
                # Write Peer section
                f.write("[Peer]\n")
                f.write(f"PublicKey = {self.config['Peer']['PublicKey']}\n")
                f.write(f"Endpoint = {self.config['Peer']['Endpoint']}\n")
                f.write(f"AllowedIPs = {self.config['Peer']['AllowedIPs']}\n")
                f.write(f"PersistentKeepalive = {self.config['Peer']['PersistentKeepalive']}\n")
            
            logger.info(f"WireGuard configuration file created: {config_path}")
            return config_path
            
        except Exception as e:
            logger.error(f"Failed to create WireGuard configuration file: {e}")
            raise
    
    async def _configure_proxy_endpoint(self):
        """Configure WireGuard endpoint to use proxy"""
        try:
            if not self.proxy_settings:
                return
            
            # For proxy connections, we need to modify how WireGuard connects
            # This is a simplified approach - in practice, you might need
            # a proxy tunnel or socat for WireGuard over SOCKS5
            
            proxy_type = self.proxy_settings['type']
            proxy_host = self.proxy_settings['host']
            proxy_port = self.proxy_settings['port']
            
            if proxy_type == 'obfs4':
                # For obfs4, the obfs4 handler should have set up a local proxy
                # We can modify the endpoint to use the local proxy
                original_endpoint = self.config['Peer']['Endpoint']
                
                # Extract original endpoint host and port
                if ':' in original_endpoint:
                    endpoint_host, endpoint_port = original_endpoint.rsplit(':', 1)
                else:
                    endpoint_host = original_endpoint
                    endpoint_port = '51820'  # Default WireGuard port
                
                # Set endpoint to use obfs4 proxy
                self.config['Peer']['Endpoint'] = f"{proxy_host}:{proxy_port}"
                
                logger.info(f"Configured WireGuard to use obfs4 proxy endpoint: {proxy_host}:{proxy_port}")
            
            elif proxy_type == 'socks5':
                # For SOCKS5, we need to set up a tunnel
                # This would typically require socat or similar tool
                await self._setup_socks5_tunnel()
            
        except Exception as e:
            logger.error(f"Failed to configure proxy endpoint: {e}")
            raise
    
    async def _setup_socks5_tunnel(self):
        """Setup SOCKS5 tunnel for WireGuard traffic"""
        try:
            proxy_host = self.proxy_settings['host']
            proxy_port = self.proxy_settings['port']
            
            # Extract original endpoint
            original_endpoint = self.config['Peer']['Endpoint']
            if ':' in original_endpoint:
                endpoint_host, endpoint_port = original_endpoint.rsplit(':', 1)
            else:
                endpoint_host = original_endpoint
                endpoint_port = '51820'
            
            # Find available local port for tunnel
            tunnel_port = await self._find_available_port()
            
            # Create socat tunnel command
            if platform.system() == 'Windows':
                # For Windows, you might need a different approach
                # This is simplified - real implementation would need proper Windows tools
                logger.warning("SOCKS5 tunnel setup not fully implemented for Windows")
                return
            else:
                # Linux/macOS socat command
                socat_cmd = [
                    'socat',
                    f'UDP-LISTEN:{tunnel_port},reuseaddr,fork',
                    f'SOCKS5:{proxy_host}:{endpoint_host}:{endpoint_port},socksport={proxy_port}'
                ]
                
                # Start socat process
                self.socat_process = await asyncio.create_subprocess_exec(
                    *socat_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Update WireGuard endpoint to use local tunnel
                self.config['Peer']['Endpoint'] = f"127.0.0.1:{tunnel_port}"
                
                logger.info(f"SOCKS5 tunnel established: 127.0.0.1:{tunnel_port} -> {endpoint_host}:{endpoint_port}")
            
        except Exception as e:
            logger.error(f"Failed to setup SOCKS5 tunnel: {e}")
            raise
    
    async def _find_available_port(self, start_port: int = 51821) -> int:
        """Find an available local port"""
        for port in range(start_port, start_port + 100):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind(('127.0.0.1', port))
                sock.close()
                return port
            except OSError:
                continue
        
        raise RuntimeError("No available ports found for tunnel")
    
    async def _backup_routes(self):
        """Backup current routing table"""
        try:
            if self.platform == 'Windows':
                result = await self._run_command(['route', 'print'])
                self.original_routes.append({
                    'platform': 'windows',
                    'data': result.stdout
                })
            else:
                # Linux/macOS
                result = await self._run_command(['ip', 'route', 'show'])
                self.original_routes.append({
                    'platform': 'unix',
                    'data': result.stdout
                })
            
            logger.info("Current routes backed up")
            
        except Exception as e:
            logger.warning(f"Failed to backup routes: {e}")
    
    async def _start_interface(self):
        """Start WireGuard interface"""
        try:
            if self.platform == 'Windows':
                await self._start_windows_interface()
            else:
                await self._start_unix_interface()
            
        except Exception as e:
            logger.error(f"Failed to start WireGuard interface: {e}")
            raise
    
    async def _start_windows_interface(self):
        """Start WireGuard interface on Windows"""
        try:
            # Use wg-quick to start interface
            await self._run_command([
                self.wg_quick_binary, 'up', self.config_file
            ])
            
            logger.info(f"WireGuard interface {self.interface_name} started on Windows")
            
        except Exception as e:
            logger.error(f"Failed to start WireGuard interface on Windows: {e}")
            raise
    
    async def _start_unix_interface(self):
        """Start WireGuard interface on Unix systems"""
        try:
            # Use wg-quick to start interface
            await self._run_command([
                'sudo', self.wg_quick_binary, 'up', self.config_file
            ])
            
            logger.info(f"WireGuard interface {self.interface_name} started on Unix")
            
        except Exception as e:
            logger.error(f"Failed to start WireGuard interface on Unix: {e}")
            raise
    
    async def _verify_connection(self):
        """Verify WireGuard connection is working"""
        try:
            # Check if interface exists
            if self.platform == 'Windows':
                result = await self._run_command([self.wg_binary, 'show'])
            else:
                result = await self._run_command(['sudo', self.wg_binary, 'show'])
            
            if self.interface_name not in result.stdout:
                raise RuntimeError("WireGuard interface not found")
            
            # Test connectivity through VPN
            await self._test_vpn_connectivity()
            
            logger.info("WireGuard connection verified successfully")
            
        except Exception as e:
            logger.error(f"WireGuard connection verification failed: {e}")
            raise
    
    async def _test_vpn_connectivity(self):
        """Test VPN connectivity"""
        try:
            # Simple connectivity test
            proc = await asyncio.create_subprocess_exec(
                'ping', '-c', '3', '8.8.8.8',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                logger.warning("VPN connectivity test failed, but continuing...")
            else:
                logger.info("VPN connectivity test passed")
            
        except Exception as e:
            logger.warning(f"VPN connectivity test error: {e}")
    
    async def stop(self):
        """Stop WireGuard VPN connection"""
        logger.info("Stopping WireGuard VPN connection")
        
        try:
            # Stop WireGuard interface
            if self.is_connected and self.interface_name:
                if self.platform == 'Windows':
                    await self._run_command([
                        self.wg_quick_binary, 'down', self.interface_name
                    ], ignore_errors=True)
                else:
                    await self._run_command([
                        'sudo', self.wg_quick_binary, 'down', self.interface_name
                    ], ignore_errors=True)
            
            # Stop socat process if running
            if hasattr(self, 'socat_process') and self.socat_process:
                self.socat_process.terminate()
                await self.socat_process.wait()
            
            # Clean up configuration file
            if self.config_file and os.path.exists(self.config_file):
                os.unlink(self.config_file)
                self.config_file = None
            
            # Restore routes if needed
            await self._restore_routes()
            
            self.is_connected = False
            self.interface_name = None
            
            logger.info("WireGuard VPN connection stopped")
            
        except Exception as e:
            logger.error(f"Error stopping WireGuard VPN: {e}")
    
    async def _restore_routes(self):
        """Restore original routing table"""
        try:
            # Route restoration is typically handled by wg-quick
            # Additional restoration logic can be added here if needed
            logger.info("Routes restoration handled by wg-quick")
            
        except Exception as e:
            logger.warning(f"Failed to restore routes: {e}")
    
    async def _run_command(self, cmd: List[str], ignore_errors: bool = False) -> subprocess.CompletedProcess:
        """
        Run a system command asynchronously
        
        Args:
            cmd: Command and arguments
            ignore_errors: Whether to ignore command errors
            
        Returns:
            CompletedProcess result
        """
        try:
            logger.debug(f"Running command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            result = subprocess.CompletedProcess(
                cmd, process.returncode, stdout.decode(), stderr.decode()
            )
            
            if result.returncode != 0 and not ignore_errors:
                logger.error(f"Command failed: {' '.join(cmd)}")
                logger.error(f"Error: {result.stderr}")
                raise subprocess.CalledProcessError(
                    result.returncode, cmd, result.stdout, result.stderr
                )
            
            return result
            
        except Exception as e:
            if not ignore_errors:
                logger.error(f"Failed to run command {' '.join(cmd)}: {e}")
                raise
            return subprocess.CompletedProcess(cmd, 1, "", str(e))
    
    def is_running(self) -> bool:
        """Check if WireGuard connection is running"""
        return self.is_connected
    
    def get_interface_name(self) -> Optional[str]:
        """Get WireGuard interface name"""
        return self.interface_name
    
    def set_config(self, private_key: str, address: str, peer_public_key: str, 
                   endpoint: str, allowed_ips: str = "0.0.0.0/0,::/0", 
                   dns: str = "1.1.1.1,8.8.8.8"):
        """
        Set WireGuard configuration programmatically
        
        Args:
            private_key: Interface private key
            address: Interface IP address
            peer_public_key: Peer public key
            endpoint: Peer endpoint (host:port)
            allowed_ips: Allowed IP ranges
            dns: DNS servers
        """
        self.config['Interface'].update({
            'PrivateKey': private_key,
            'Address': address,
            'DNS': dns
        })
        
        self.config['Peer'].update({
            'PublicKey': peer_public_key,
            'Endpoint': endpoint,
            'AllowedIPs': allowed_ips
        })
        
        logger.info("WireGuard configuration updated")
    
    async def get_status(self) -> Dict:
        """
        Get WireGuard connection status
        
        Returns:
            Dictionary with connection status information
        """
        try:
            if not self.is_connected:
                return {
                    'connected': False,
                    'interface': None,
                    'endpoint': None,
                    'transfer': None
                }
            
            # Get WireGuard status
            if self.platform == 'Windows':
                result = await self._run_command([self.wg_binary, 'show', self.interface_name])
            else:
                result = await self._run_command(['sudo', self.wg_binary, 'show', self.interface_name])
            
            # Parse status information
            status = {
                'connected': True,
                'interface': self.interface_name,
                'endpoint': self.config['Peer']['Endpoint'],
                'raw_status': result.stdout
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get WireGuard status: {e}")
            return {
                'connected': False,
                'error': str(e)
            }