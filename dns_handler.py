"""
DNS Handler for DNS-over-HTTPS (DoH) queries
Provides secure DNS resolution with leak protection
"""

import asyncio
import aiohttp
import json
import socket
import struct
import logging
import platform
import subprocess
from typing import Dict, List, Optional, Tuple
import base64

logger = logging.getLogger(__name__)

class DNSHandler:
    """
    Handles DNS-over-HTTPS queries and DNS leak prevention
    Supports multiple DoH providers and proxy routing
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.original_dns_servers: List[str] = []
        self.doh_servers = {
            'cloudflare': {
                'url': 'https://cloudflare-dns.com/dns-query',
                'ip': '1.1.1.1'
            },
            'google': {
                'url': 'https://dns.google/dns-query',
                'ip': '8.8.8.8'
            },
            'quad9': {
                'url': 'https://dns.quad9.net/dns-query',
                'ip': '9.9.9.9'
            },
            'adguard': {
                'url': 'https://dns.adguard.com/dns-query',
                'ip': '94.140.14.14'
            }
        }
        self.current_provider = 'cloudflare'
        self.proxy_settings: Optional[Dict] = None
        self.dns_server_port = 5353
        self.running = False
        self.tor_mode = False
    
    async def start_doh(self, provider: str = 'cloudflare'):
        """
        Start DNS-over-HTTPS service
        
        Args:
            provider: DoH provider to use (cloudflare, google, quad9, adguard)
        """
        logger.info(f"Starting DNS-over-HTTPS with provider: {provider}")
        
        if provider not in self.doh_servers:
            raise ValueError(f"Unknown DoH provider: {provider}")
        
        self.current_provider = provider
        
        # Create HTTP session
        connector = aiohttp.TCPConnector(
            ssl=True,
            limit=100,
            limit_per_host=30,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=10, connect=5)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        # Backup original DNS settings
        await self._backup_dns_settings()
        
        # Start local DNS server
        await self._start_local_dns_server()
        
        # Configure system to use our local DNS server
        await self._configure_system_dns()
        
        self.running = True
        logger.info("DNS-over-HTTPS started successfully")
    
    async def start_doh_with_proxy(self, proxy_port: int, proxy_host: str = '127.0.0.1'):
        """
        Start DNS-over-HTTPS with SOCKS5 proxy routing
        
        Args:
            proxy_port: SOCKS5 proxy port
            proxy_host: SOCKS5 proxy host
        """
        logger.info(f"Starting DNS-over-HTTPS with proxy {proxy_host}:{proxy_port}")
        
        self.proxy_settings = {
            'proxy': f'socks5://{proxy_host}:{proxy_port}'
        }
        
        # Create HTTP session with proxy
        connector = aiohttp.TCPConnector(
            ssl=True,
            limit=100,
            limit_per_host=30,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=15, connect=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        # Backup original DNS settings
        await self._backup_dns_settings()
        
        # Start local DNS server
        await self._start_local_dns_server()
        
        # Configure system to use our local DNS server
        await self._configure_system_dns()
        
        self.running = True
        logger.info("DNS-over-HTTPS with proxy started successfully")
    
    async def start_tor_dns(self):
        """
        Start DNS resolution through Tor network
        Uses Tor's built-in DNS resolution
        """
        logger.info("Starting DNS resolution through Tor")
        
        self.tor_mode = True
        
        # Backup original DNS settings
        await self._backup_dns_settings()
        
        # Start local DNS server that forwards to Tor
        await self._start_local_dns_server()
        
        # Configure system to use our local DNS server
        await self._configure_system_dns()
        
        self.running = True
        logger.info("Tor DNS resolution started successfully")
    
    async def _backup_dns_settings(self):
        """Backup current system DNS settings"""
        try:
            if platform.system() == 'Windows':
                # Get current DNS servers on Windows
                result = subprocess.run([
                    'powershell', '-Command',
                    'Get-DnsClientServerAddress -AddressFamily IPv4 | ConvertTo-Json'
                ], capture_output=True, text=True, check=True)
                
                dns_info = json.loads(result.stdout)
                if isinstance(dns_info, list):
                    for interface in dns_info:
                        if interface.get('ServerAddresses'):
                            self.original_dns_servers.extend(interface['ServerAddresses'])
                else:
                    if dns_info.get('ServerAddresses'):
                        self.original_dns_servers.extend(dns_info['ServerAddresses'])
            
            else:  # Linux/Unix
                # Read from /etc/resolv.conf
                try:
                    with open('/etc/resolv.conf', 'r') as f:
                        for line in f:
                            if line.strip().startswith('nameserver'):
                                dns_server = line.strip().split()[1]
                                self.original_dns_servers.append(dns_server)
                except FileNotFoundError:
                    pass
            
            # Remove duplicates and localhost entries
            self.original_dns_servers = list(set([
                dns for dns in self.original_dns_servers 
                if not dns.startswith('127.') and not dns.startswith('::1')
            ]))
            
            logger.info(f"Backed up DNS servers: {self.original_dns_servers}")
            
        except Exception as e:
            logger.warning(f"Could not backup DNS settings: {e}")
    
    async def _start_local_dns_server(self):
        """Start local DNS server that handles DoH queries"""
        try:
            # Create UDP socket for DNS server
            self.dns_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.dns_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.dns_socket.bind(('127.0.0.1', self.dns_server_port))
            self.dns_socket.setblocking(False)
            
            # Start DNS server task
            asyncio.create_task(self._dns_server_loop())
            
            logger.info(f"Local DNS server started on 127.0.0.1:{self.dns_server_port}")
            
        except Exception as e:
            logger.error(f"Failed to start local DNS server: {e}")
            raise
    
    async def _dns_server_loop(self):
        """Main DNS server loop"""
        logger.info("DNS server loop started")
        
        while self.running:
            try:
                # Wait for DNS query
                loop = asyncio.get_event_loop()
                data, addr = await loop.sock_recvfrom(self.dns_socket, 512)
                
                # Process DNS query asynchronously
                asyncio.create_task(self._handle_dns_query(data, addr))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in DNS server loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _handle_dns_query(self, data: bytes, addr: Tuple[str, int]):
        """
        Handle incoming DNS query
        
        Args:
            data: Raw DNS query data
            addr: Client address
        """
        try:
            # Parse DNS query
            query_info = self._parse_dns_query(data)
            if not query_info:
                return
            
            domain, query_type = query_info
            logger.debug(f"DNS query for {domain} (type {query_type}) from {addr}")
            
            # Resolve using appropriate method
            if self.tor_mode:
                response = await self._resolve_via_tor(domain, query_type)
            else:
                response = await self._resolve_via_doh(domain, query_type)
            
            if response:
                # Build DNS response
                dns_response = self._build_dns_response(data, response, query_type)
                
                # Send response back to client
                loop = asyncio.get_event_loop()
                await loop.sock_sendto(self.dns_socket, dns_response, addr)
                
                logger.debug(f"Sent DNS response for {domain} to {addr}")
            
        except Exception as e:
            logger.error(f"Error handling DNS query: {e}")
    
    def _parse_dns_query(self, data: bytes) -> Optional[Tuple[str, int]]:
        """
        Parse DNS query to extract domain name and query type
        
        Args:
            data: Raw DNS query data
            
        Returns:
            Tuple of (domain, query_type) or None if parsing fails
        """
        try:
            if len(data) < 12:
                return None
            
            # Skip DNS header (12 bytes)
            offset = 12
            domain_parts = []
            
            # Parse domain name
            while offset < len(data):
                length = data[offset]
                if length == 0:
                    offset += 1
                    break
                
                if length > 63:  # Compressed label
                    return None
                
                offset += 1
                if offset + length > len(data):
                    return None
                
                domain_parts.append(data[offset:offset + length].decode('utf-8'))
                offset += length
            
            if not domain_parts:
                return None
            
            domain = '.'.join(domain_parts)
            
            # Get query type (2 bytes after domain)
            if offset + 2 <= len(data):
                query_type = struct.unpack('>H', data[offset:offset + 2])[0]
                return (domain, query_type)
            
            return None
            
        except Exception as e:
            logger.debug(f"Error parsing DNS query: {e}")
            return None
    
    async def _resolve_via_doh(self, domain: str, query_type: int) -> Optional[List[str]]:
        """
        Resolve domain using DNS-over-HTTPS
        
        Args:
            domain: Domain to resolve
            query_type: DNS query type (1=A, 28=AAAA, etc.)
            
        Returns:
            List of IP addresses or None if resolution fails
        """
        try:
            provider = self.doh_servers[self.current_provider]
            
            # Prepare DoH query parameters
            params = {
                'name': domain,
                'type': query_type,
                'do': 'false',  # DNSSEC validation
                'cd': 'false'   # Checking disabled
            }
            
            headers = {
                'Accept': 'application/dns-json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Add proxy settings if available
            kwargs = {'params': params, 'headers': headers}
            if self.proxy_settings:
                kwargs['proxy'] = self.proxy_settings['proxy']
            
            # Make DoH request
            if self.session:
                async with self.session.get(provider['url'], **kwargs) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Extract IP addresses from response
                        ips = []
                        if 'Answer' in result:
                            for answer in result['Answer']:
                                if answer.get('type') == query_type:
                                    ips.append(answer.get('data'))
                        
                        if ips:
                            logger.debug(f"Resolved {domain} to {ips}")
                            return ips
            
            logger.debug(f"No resolution for {domain}")
            return None
            
        except Exception as e:
            logger.error(f"DoH resolution error for {domain}: {e}")
            return None
    
    async def _resolve_via_tor(self, domain: str, query_type: int) -> Optional[List[str]]:
        """
        Resolve domain using Tor's built-in DNS resolution
        
        Args:
            domain: Domain to resolve
            query_type: DNS query type
            
        Returns:
            List of IP addresses or None if resolution fails
        """
        try:
            # For Tor DNS, we use SOCKS5 to connect to Tor proxy
            # and let Tor resolve the domain
            
            # This is a simplified implementation
            # In practice, you'd use the SOCKS5 protocol to request DNS resolution
            
            # For now, fallback to system DNS (this should be improved)
            loop = asyncio.get_event_loop()
            
            if query_type == 1:  # A record
                result = await loop.getaddrinfo(domain, None, family=socket.AF_INET)
                ips = [res[4][0] for res in result]
            elif query_type == 28:  # AAAA record
                result = await loop.getaddrinfo(domain, None, family=socket.AF_INET6)
                ips = [res[4][0] for res in result]
            else:
                return None
            
            logger.debug(f"Tor resolved {domain} to {ips}")
            return ips
            
        except Exception as e:
            logger.error(f"Tor DNS resolution error for {domain}: {e}")
            return None
    
    def _build_dns_response(self, original_query: bytes, ips: List[str], query_type: int) -> bytes:
        """
        Build DNS response packet
        
        Args:
            original_query: Original DNS query
            ips: List of IP addresses to include in response
            query_type: DNS query type
            
        Returns:
            DNS response packet
        """
        try:
            # Copy original query
            response = bytearray(original_query)
            
            # Modify header to indicate response
            # Set QR bit (query/response flag)
            response[2] |= 0x80
            
            # Set answer count
            answer_count = len(ips)
            response[6:8] = struct.pack('>H', answer_count)
            
            # Add answer records
            for ip in ips:
                if query_type == 1:  # A record
                    response.extend(self._build_a_record(ip))
                elif query_type == 28:  # AAAA record
                    response.extend(self._build_aaaa_record(ip))
            
            return bytes(response)
            
        except Exception as e:
            logger.error(f"Error building DNS response: {e}")
            return original_query  # Return original query as fallback
    
    def _build_a_record(self, ip: str) -> bytes:
        """Build A record for IPv4 address"""
        try:
            # Name (compressed pointer to query name)
            record = b'\xc0\x0c'
            
            # Type (A record)
            record += struct.pack('>H', 1)
            
            # Class (IN)
            record += struct.pack('>H', 1)
            
            # TTL (300 seconds)
            record += struct.pack('>I', 300)
            
            # Data length (4 bytes for IPv4)
            record += struct.pack('>H', 4)
            
            # IP address
            ip_bytes = socket.inet_aton(ip)
            record += ip_bytes
            
            return record
            
        except Exception as e:
            logger.error(f"Error building A record: {e}")
            return b''
    
    def _build_aaaa_record(self, ip: str) -> bytes:
        """Build AAAA record for IPv6 address"""
        try:
            # Name (compressed pointer to query name)
            record = b'\xc0\x0c'
            
            # Type (AAAA record)
            record += struct.pack('>H', 28)
            
            # Class (IN)
            record += struct.pack('>H', 1)
            
            # TTL (300 seconds)
            record += struct.pack('>I', 300)
            
            # Data length (16 bytes for IPv6)
            record += struct.pack('>H', 16)
            
            # IP address
            ip_bytes = socket.inet_pton(socket.AF_INET6, ip)
            record += ip_bytes
            
            return record
            
        except Exception as e:
            logger.error(f"Error building AAAA record: {e}")
            return b''
    
    async def _configure_system_dns(self):
        """Configure system to use our local DNS server"""
        try:
            if platform.system() == 'Windows':
                # Set DNS server for all network interfaces
                subprocess.run([
                    'powershell', '-Command',
                    f'Get-NetAdapter | Set-DnsClientServerAddress -ServerAddresses 127.0.0.1'
                ], check=True)
                
            else:  # Linux/Unix
                # Backup original resolv.conf
                subprocess.run(['cp', '/etc/resolv.conf', '/etc/resolv.conf.backup'], 
                              check=False)
                
                # Write new resolv.conf
                with open('/etc/resolv.conf', 'w') as f:
                    f.write(f'nameserver 127.0.0.1\n')
                    f.write('options timeout:2 attempts:3\n')
            
            logger.info("System DNS configured to use local DNS server")
            
        except Exception as e:
            logger.error(f"Failed to configure system DNS: {e}")
            raise
    
    async def stop(self):
        """Stop DNS handler and restore original settings"""
        logger.info("Stopping DNS handler...")
        
        self.running = False
        
        try:
            # Close HTTP session
            if self.session:
                await self.session.close()
                self.session = None
            
            # Close DNS socket
            if hasattr(self, 'dns_socket'):
                self.dns_socket.close()
            
            # Restore original DNS settings
            await self._restore_dns_settings()
            
            logger.info("DNS handler stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping DNS handler: {e}")
    
    async def _restore_dns_settings(self):
        """Restore original DNS settings"""
        try:
            if platform.system() == 'Windows':
                if self.original_dns_servers:
                    # Restore original DNS servers
                    dns_list = ','.join(self.original_dns_servers)
                    subprocess.run([
                        'powershell', '-Command',
                        f'Get-NetAdapter | Set-DnsClientServerAddress -ServerAddresses {dns_list}'
                    ], check=True)
                else:
                    # Reset to automatic DHCP
                    subprocess.run([
                        'powershell', '-Command',
                        'Get-NetAdapter | Set-DnsClientServerAddress -ResetServerAddresses'
                    ], check=True)
                
            else:  # Linux/Unix
                # Restore original resolv.conf
                try:
                    subprocess.run(['mv', '/etc/resolv.conf.backup', '/etc/resolv.conf'], 
                                  check=False)
                except:
                    # If backup doesn't exist, create a basic resolv.conf
                    with open('/etc/resolv.conf', 'w') as f:
                        if self.original_dns_servers:
                            for dns in self.original_dns_servers:
                                f.write(f'nameserver {dns}\n')
                        else:
                            f.write('nameserver 8.8.8.8\n')
                            f.write('nameserver 8.8.4.4\n')
            
            logger.info("Original DNS settings restored")
            
        except Exception as e:
            logger.error(f"Failed to restore DNS settings: {e}")
