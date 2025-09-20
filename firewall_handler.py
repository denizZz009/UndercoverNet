"""
Firewall Handler with Kill Switch functionality
Prevents traffic leaks when VPN/proxy connections fail
"""

import asyncio
import subprocess
import platform
import logging
import socket
import json
from typing import List, Dict, Optional, Set
import ipaddress

logger = logging.getLogger(__name__)

class FirewallHandler:
    """
    Handles firewall rules and kill switch functionality
    Prevents DNS and traffic leaks when connections fail
    """
    
    def __init__(self):
        self.platform = platform.system()
        self.original_rules: List[Dict] = []
        self.kill_switch_active = False
        self.allowed_ips: Set[str] = set()
        self.allowed_ports: Set[int] = set()
        self.vpn_interface: Optional[str] = None
        
        # Default allowed IPs (local and essential services)
        self.allowed_ips.update([
            '127.0.0.1',
            '::1',
            '169.254.0.0/16',  # Link-local
            '10.0.0.0/8',      # Private networks
            '172.16.0.0/12',
            '192.168.0.0/16'
        ])
    
    async def setup_kill_switch(self, vpn_interface: Optional[str] = None):
        """
        Setup kill switch firewall rules
        
        Args:
            vpn_interface: VPN interface name (e.g., 'wg0', 'tun0')
        """
        logger.info("Setting up kill switch firewall rules")
        
        self.vpn_interface = vpn_interface
        
        try:
            # Backup current firewall rules
            await self._backup_firewall_rules()
            
            # Apply kill switch rules based on platform
            if self.platform == 'Windows':
                await self._setup_windows_kill_switch()
            elif self.platform == 'Linux':
                await self._setup_linux_kill_switch()
            elif self.platform == 'Darwin':  # macOS
                await self._setup_macos_kill_switch()
            else:
                raise ValueError(f"Unsupported platform: {self.platform}")
            
            self.kill_switch_active = True
            logger.info("Kill switch activated successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup kill switch: {e}")
            raise
    
    async def add_allowed_ip(self, ip: str):
        """
        Add an IP address to the allowed list
        
        Args:
            ip: IP address or CIDR range to allow
        """
        try:
            # Validate IP address
            ipaddress.ip_network(ip, strict=False)
            self.allowed_ips.add(ip)
            
            # Update firewall rules if kill switch is active
            if self.kill_switch_active:
                await self._add_firewall_exception(ip)
            
            logger.info(f"Added allowed IP: {ip}")
            
        except Exception as e:
            logger.error(f"Failed to add allowed IP {ip}: {e}")
    
    async def add_allowed_port(self, port: int, protocol: str = 'tcp'):
        """
        Add a port to the allowed list
        
        Args:
            port: Port number to allow
            protocol: Protocol (tcp/udp)
        """
        try:
            self.allowed_ports.add(port)
            
            # Update firewall rules if kill switch is active
            if self.kill_switch_active:
                await self._add_port_exception(port, protocol)
            
            logger.info(f"Added allowed port: {port}/{protocol}")
            
        except Exception as e:
            logger.error(f"Failed to add allowed port {port}: {e}")
    
    async def _backup_firewall_rules(self):
        """Backup current firewall rules"""
        try:
            if self.platform == 'Windows':
                await self._backup_windows_rules()
            elif self.platform == 'Linux':
                await self._backup_linux_rules()
            elif self.platform == 'Darwin':
                await self._backup_macos_rules()
            
            logger.info("Firewall rules backed up successfully")
            
        except Exception as e:
            logger.warning(f"Could not backup firewall rules: {e}")
    
    async def _backup_windows_rules(self):
        """Backup Windows firewall rules"""
        try:
            # Export current firewall configuration
            result = await self._run_command([
                'netsh', 'advfirewall', 'export',
                'firewall_backup.wfw'
            ])
            
            # Get current firewall profiles
            result = await self._run_command([
                'netsh', 'advfirewall', 'show', 'allprofiles'
            ])
            
            self.original_rules.append({
                'type': 'windows_profiles',
                'data': result.stdout
            })
            
        except Exception as e:
            logger.warning(f"Failed to backup Windows firewall rules: {e}")
    
    async def _backup_linux_rules(self):
        """Backup Linux iptables rules"""
        try:
            # Backup iptables rules
            result = await self._run_command(['iptables-save'])
            self.original_rules.append({
                'type': 'iptables',
                'data': result.stdout
            })
            
            # Backup ip6tables rules
            try:
                result = await self._run_command(['ip6tables-save'])
                self.original_rules.append({
                    'type': 'ip6tables',
                    'data': result.stdout
                })
            except:
                pass  # IPv6 might not be available
            
        except Exception as e:
            logger.warning(f"Failed to backup Linux firewall rules: {e}")
    
    async def _backup_macos_rules(self):
        """Backup macOS pfctl rules"""
        try:
            # Backup pfctl rules
            result = await self._run_command(['pfctl', '-s', 'rules'])
            self.original_rules.append({
                'type': 'pfctl',
                'data': result.stdout
            })
            
        except Exception as e:
            logger.warning(f"Failed to backup macOS firewall rules: {e}")
    
    async def _setup_windows_kill_switch(self):
        """Setup kill switch on Windows using netsh"""
        try:
            # Enable Windows Firewall for all profiles
            await self._run_command([
                'netsh', 'advfirewall', 'set', 'allprofiles', 'state', 'on'
            ])
            
            # Set default action to block
            await self._run_command([
                'netsh', 'advfirewall', 'set', 'allprofiles', 
                'firewallpolicy', 'blockinbound,blockoutbound'
            ])
            
            # Allow loopback traffic
            await self._run_command([
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                'name=Kill Switch - Allow Loopback',
                'dir=out', 'action=allow', 'remoteip=127.0.0.1'
            ])
            
            await self._run_command([
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                'name=Kill Switch - Allow Loopback',
                'dir=in', 'action=allow', 'remoteip=127.0.0.1'
            ])
            
            # Allow local network traffic
            for network in ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']:
                await self._run_command([
                    'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                    f'name=Kill Switch - Allow Local {network}',
                    'dir=out', 'action=allow', f'remoteip={network}'
                ])
            
            # Allow VPN interface if specified
            if self.vpn_interface:
                await self._run_command([
                    'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                    f'name=Kill Switch - Allow VPN {self.vpn_interface}',
                    'dir=out', 'action=allow', f'interfacetype={self.vpn_interface}'
                ])
            
            # Allow specific IPs and ports
            for ip in self.allowed_ips:
                await self._add_firewall_exception(ip)
            
            for port in self.allowed_ports:
                await self._add_port_exception(port, 'tcp')
                await self._add_port_exception(port, 'udp')
            
            logger.info("Windows kill switch configured")
            
        except Exception as e:
            logger.error(f"Failed to setup Windows kill switch: {e}")
            raise
    
    async def _setup_linux_kill_switch(self):
        """Setup kill switch on Linux using iptables"""
        try:
            # Flush existing rules
            await self._run_command(['iptables', '-F'])
            await self._run_command(['iptables', '-X'])
            
            # Set default policies to DROP
            await self._run_command(['iptables', '-P', 'INPUT', 'DROP'])
            await self._run_command(['iptables', '-P', 'FORWARD', 'DROP'])
            await self._run_command(['iptables', '-P', 'OUTPUT', 'DROP'])
            
            # Allow loopback traffic
            await self._run_command([
                'iptables', '-A', 'INPUT', '-i', 'lo', '-j', 'ACCEPT'
            ])
            await self._run_command([
                'iptables', '-A', 'OUTPUT', '-o', 'lo', '-j', 'ACCEPT'
            ])
            
            # Allow established and related connections
            await self._run_command([
                'iptables', '-A', 'INPUT', '-m', 'state',
                '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'
            ])
            
            # Allow local network traffic
            for network in ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']:
                await self._run_command([
                    'iptables', '-A', 'OUTPUT', '-d', network, '-j', 'ACCEPT'
                ])
                await self._run_command([
                    'iptables', '-A', 'INPUT', '-s', network, '-j', 'ACCEPT'
                ])
            
            # Allow VPN interface if specified
            if self.vpn_interface:
                await self._run_command([
                    'iptables', '-A', 'OUTPUT', '-o', self.vpn_interface, '-j', 'ACCEPT'
                ])
                await self._run_command([
                    'iptables', '-A', 'INPUT', '-i', self.vpn_interface, '-j', 'ACCEPT'
                ])
            
            # Allow specific IPs and ports
            for ip in self.allowed_ips:
                if '/' in ip:  # CIDR notation
                    await self._run_command([
                        'iptables', '-A', 'OUTPUT', '-d', ip, '-j', 'ACCEPT'
                    ])
                else:
                    await self._run_command([
                        'iptables', '-A', 'OUTPUT', '-d', ip, '-j', 'ACCEPT'
                    ])
            
            for port in self.allowed_ports:
                await self._run_command([
                    'iptables', '-A', 'OUTPUT', '-p', 'tcp', '--dport', str(port), '-j', 'ACCEPT'
                ])
                await self._run_command([
                    'iptables', '-A', 'OUTPUT', '-p', 'udp', '--dport', str(port), '-j', 'ACCEPT'
                ])
            
            # IPv6 rules
            try:
                await self._run_command(['ip6tables', '-P', 'INPUT', 'DROP'])
                await self._run_command(['ip6tables', '-P', 'FORWARD', 'DROP'])
                await self._run_command(['ip6tables', '-P', 'OUTPUT', 'DROP'])
                
                # Allow IPv6 loopback
                await self._run_command([
                    'ip6tables', '-A', 'INPUT', '-i', 'lo', '-j', 'ACCEPT'
                ])
                await self._run_command([
                    'ip6tables', '-A', 'OUTPUT', '-o', 'lo', '-j', 'ACCEPT'
                ])
                
            except:
                pass  # IPv6 might not be available
            
            logger.info("Linux kill switch configured")
            
        except Exception as e:
            logger.error(f"Failed to setup Linux kill switch: {e}")
            raise
    
    async def _setup_macos_kill_switch(self):
        """Setup kill switch on macOS using pfctl"""
        try:
            # Create pfctl configuration
            pf_config = """
# Kill switch configuration
set block-policy drop
set skip on lo0

# Block all traffic by default
block all

# Allow loopback
pass on lo0

# Allow local networks
pass out to 10.0.0.0/8
pass out to 172.16.0.0/12
pass out to 192.168.0.0/16
pass out to 169.254.0.0/16

# Allow established connections
pass out flags S/SA keep state
"""
            
            # Add VPN interface allowance if specified
            if self.vpn_interface:
                pf_config += f"pass on {self.vpn_interface}\n"
            
            # Add allowed IPs
            for ip in self.allowed_ips:
                pf_config += f"pass out to {ip}\n"
            
            # Write configuration to file
            with open('/tmp/killswitch.conf', 'w') as f:
                f.write(pf_config)
            
            # Load pfctl configuration
            await self._run_command(['pfctl', '-f', '/tmp/killswitch.conf'])
            await self._run_command(['pfctl', '-e'])
            
            logger.info("macOS kill switch configured")
            
        except Exception as e:
            logger.error(f"Failed to setup macOS kill switch: {e}")
            raise
    
    async def _add_firewall_exception(self, ip: str):
        """Add firewall exception for specific IP"""
        try:
            if self.platform == 'Windows':
                await self._run_command([
                    'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                    f'name=Kill Switch - Allow {ip}',
                    'dir=out', 'action=allow', f'remoteip={ip}'
                ])
                
            elif self.platform == 'Linux':
                await self._run_command([
                    'iptables', '-A', 'OUTPUT', '-d', ip, '-j', 'ACCEPT'
                ])
                
            elif self.platform == 'Darwin':
                # Update pfctl rules (simplified)
                await self._run_command([
                    'pfctl', '-t', 'allowed_ips', '-T', 'add', ip
                ])
            
        except Exception as e:
            logger.error(f"Failed to add firewall exception for {ip}: {e}")
    
    async def _add_port_exception(self, port: int, protocol: str):
        """Add firewall exception for specific port"""
        try:
            if self.platform == 'Windows':
                await self._run_command([
                    'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                    f'name=Kill Switch - Allow {port}/{protocol}',
                    'dir=out', 'action=allow', 'protocol=' + protocol.upper(),
                    f'localport={port}'
                ])
                
            elif self.platform == 'Linux':
                await self._run_command([
                    'iptables', '-A', 'OUTPUT', '-p', protocol, '--dport', str(port), '-j', 'ACCEPT'
                ])
                
            elif self.platform == 'Darwin':
                # Update pfctl rules (simplified)
                pass  # Port-specific rules would need more complex pfctl configuration
            
        except Exception as e:
            logger.error(f"Failed to add port exception for {port}/{protocol}: {e}")
    
    async def restore_rules(self):
        """Restore original firewall rules"""
        logger.info("Restoring original firewall rules")
        
        try:
            if self.platform == 'Windows':
                await self._restore_windows_rules()
            elif self.platform == 'Linux':
                await self._restore_linux_rules()
            elif self.platform == 'Darwin':
                await self._restore_macos_rules()
            
            self.kill_switch_active = False
            logger.info("Original firewall rules restored")
            
        except Exception as e:
            logger.error(f"Failed to restore firewall rules: {e}")
    
    async def _restore_windows_rules(self):
        """Restore Windows firewall rules"""
        try:
            # Remove kill switch rules
            await self._run_command([
                'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                'name=all'
            ], ignore_errors=True)
            
            # Import backup if available
            try:
                await self._run_command([
                    'netsh', 'advfirewall', 'import', 'firewall_backup.wfw'
                ])
            except:
                # If no backup, reset to defaults
                await self._run_command([
                    'netsh', 'advfirewall', 'reset'
                ])
            
        except Exception as e:
            logger.error(f"Failed to restore Windows firewall rules: {e}")
    
    async def _restore_linux_rules(self):
        """Restore Linux iptables rules"""
        try:
            # Restore from backup
            for rule_backup in self.original_rules:
                if rule_backup['type'] == 'iptables':
                    # Write rules to temporary file
                    with open('/tmp/iptables_restore.rules', 'w') as f:
                        f.write(rule_backup['data'])
                    
                    # Restore rules
                    await self._run_command([
                        'iptables-restore', '/tmp/iptables_restore.rules'
                    ])
                    
                elif rule_backup['type'] == 'ip6tables':
                    # Write rules to temporary file
                    with open('/tmp/ip6tables_restore.rules', 'w') as f:
                        f.write(rule_backup['data'])
                    
                    # Restore rules
                    await self._run_command([
                        'ip6tables-restore', '/tmp/ip6tables_restore.rules'
                    ], ignore_errors=True)
            
            # If no backup, set permissive defaults
            if not self.original_rules:
                await self._run_command(['iptables', '-F'])
                await self._run_command(['iptables', '-P', 'INPUT', 'ACCEPT'])
                await self._run_command(['iptables', '-P', 'FORWARD', 'ACCEPT'])
                await self._run_command(['iptables', '-P', 'OUTPUT', 'ACCEPT'])
            
        except Exception as e:
            logger.error(f"Failed to restore Linux firewall rules: {e}")
    
    async def _restore_macos_rules(self):
        """Restore macOS pfctl rules"""
        try:
            # Disable pfctl
            await self._run_command(['pfctl', '-d'], ignore_errors=True)
            
            # Load default configuration
            await self._run_command(['pfctl', '-f', '/etc/pf.conf'], ignore_errors=True)
            
        except Exception as e:
            logger.error(f"Failed to restore macOS firewall rules: {e}")
    
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
                cmd, process.returncode or 0, stdout.decode(), stderr.decode()
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
    
    def is_kill_switch_active(self) -> bool:
        """Check if kill switch is currently active"""
        return self.kill_switch_active
    
    async def test_connectivity(self, host: str = '8.8.8.8', port: int = 53, timeout: float = 5.0) -> bool:
        """
        Test network connectivity to verify kill switch functionality
        
        Args:
            host: Host to test connectivity to
            port: Port to test
            timeout: Connection timeout
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to connect to the specified host and port
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            
            writer.close()
            await writer.wait_closed()
            
            logger.debug(f"Connectivity test to {host}:{port} successful")
            return True
            
        except Exception as e:
            logger.debug(f"Connectivity test to {host}:{port} failed: {e}")
            return False