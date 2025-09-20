#!/usr/bin/env python3
"""
Web-based Protection Monitor
Visual dashboard to see protection status in real-time
"""

import asyncio
import json
import time
import logging
import socket
import subprocess
import platform
from datetime import datetime
from aiohttp import web, WSMsgType
import aiohttp_cors
import weakref
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from dns_handler import DNSHandler
    from padding_handler import PaddingHandler
except ImportError as e:
    logger.error(f"Import error: {e}")
    exit(1)

class WebMonitor:
    """Web-based real-time protection monitor"""
    
    def __init__(self):
        self.dns_handler = None
        self.padding_handler = None
        self.websockets = weakref.WeakSet()
        self.stats = {
            'dns_active': False,
            'padding_active': False,
            'start_time': None,
            'dns_queries': 0,
            'dummy_packets': 0,
            'protection_events': [],
            'live_dns_queries': [],
            'network_connections': [],
            'traffic_stats': [],
            'ip_info': {}
        }
        self.app = None
        self.monitoring_tasks = []
        self.last_network_stats = None
    
    async def websocket_handler(self, request):
        """Handle WebSocket connections"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websockets.add(ws)
        logger.info("New WebSocket connection")
        
        # Send initial status
        await self.send_status_update(ws)
        
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    await self.handle_websocket_message(data, ws)
                except json.JSONDecodeError:
                    pass
            elif msg.type == WSMsgType.ERROR:
                logger.error(f'WebSocket error: {ws.exception()}')
        
        logger.info("WebSocket connection closed")
        return ws
    
    async def handle_websocket_message(self, data, ws):
        """Handle incoming WebSocket messages"""
        action = data.get('action')
        
        if action == 'start_dns':
            await self.start_dns_protection()
        elif action == 'stop_dns':
            await self.stop_dns_protection()
        elif action == 'start_padding':
            await self.start_padding_protection()
        elif action == 'stop_padding':
            await self.stop_padding_protection()
        elif action == 'get_status':
            await self.send_status_update(ws)
        elif action == 'start_monitoring':
            await self.start_live_monitoring()
        elif action == 'stop_monitoring':
            await self.stop_live_monitoring()
        elif action == 'test_dns':
            await self.test_dns_queries()
        elif action == 'stop_all_shutdown':
            await self.stop_all_and_prepare_shutdown()
    
    async def start_dns_protection(self):
        """Start DNS protection and notify clients"""
        try:
            if not self.dns_handler:
                self.dns_handler = DNSHandler()
                await self.dns_handler.start_doh('cloudflare')
                self.stats['dns_active'] = True
                self.stats['start_time'] = time.time()
                await self.add_event("DNS-over-HTTPS protection started")
                await self.broadcast_status()
        except Exception as e:
            await self.add_event(f"DNS protection failed: {e}")
    
    async def stop_dns_protection(self):
        """Stop DNS protection and notify clients"""
        try:
            if self.dns_handler:
                await self.dns_handler.stop()
                self.dns_handler = None
                self.stats['dns_active'] = False
                await self.add_event("DNS-over-HTTPS protection stopped")
                await self.broadcast_status()
        except Exception as e:
            await self.add_event(f"DNS stop failed: {e}")
    
    async def start_padding_protection(self):
        """Start traffic obfuscation and notify clients"""
        try:
            if not self.padding_handler:
                self.padding_handler = PaddingHandler()
                await self.padding_handler.start()
                self.stats['padding_active'] = True
                await self.add_event("Traffic obfuscation started")
                await self.broadcast_status()
        except Exception as e:
            await self.add_event(f"Traffic obfuscation failed: {e}")
    
    async def stop_padding_protection(self):
        """Stop traffic obfuscation and notify clients"""
        try:
            if self.padding_handler:
                await self.padding_handler.stop()
                self.padding_handler = None
                self.stats['padding_active'] = False
                await self.add_event("Traffic obfuscation stopped")
                await self.broadcast_status()
        except Exception as e:
            await self.add_event(f"Traffic stop failed: {e}")
    
    async def start_live_monitoring(self):
        """Start live monitoring tasks"""
        if not self.monitoring_tasks:
            self.monitoring_tasks = [
                asyncio.create_task(self.monitor_dns_queries()),
                asyncio.create_task(self.monitor_network_traffic()),
                asyncio.create_task(self.monitor_connections()),
                asyncio.create_task(self.get_ip_information())
            ]
            await self.add_event("Live monitoring started")
    
    async def stop_live_monitoring(self):
        """Stop live monitoring tasks"""
        for task in self.monitoring_tasks:
            task.cancel()
        self.monitoring_tasks = []
        await self.add_event("Live monitoring stopped")
    
    async def monitor_dns_queries(self):
        """Monitor DNS queries in real-time"""
        test_domains = ['google.com', 'github.com', 'cloudflare.com', 'microsoft.com', 'youtube.com']
        
        while True:
            try:
                for domain in test_domains:
                    try:
                        start_time = time.time()
                        ip_address = socket.gethostbyname(domain)
                        response_time = round((time.time() - start_time) * 1000, 1)
                        
                        dns_query = {
                            'timestamp': datetime.now().strftime("%H:%M:%S"),
                            'domain': domain,
                            'ip': ip_address,
                            'response_time': response_time,
                            'encrypted': self.stats['dns_active']
                        }
                        
                        self.stats['live_dns_queries'].append(dns_query)
                        
                        # Keep only last 20 queries
                        if len(self.stats['live_dns_queries']) > 20:
                            self.stats['live_dns_queries'] = self.stats['live_dns_queries'][-20:]
                        
                        await asyncio.sleep(3)
                    except Exception as e:
                        dns_query = {
                            'timestamp': datetime.now().strftime("%H:%M:%S"),
                            'domain': domain,
                            'ip': 'FAILED',
                            'response_time': 0,
                            'encrypted': False,
                            'error': str(e)[:30]
                        }
                        self.stats['live_dns_queries'].append(dns_query)
                
                await asyncio.sleep(10)  # Wait before next cycle
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(5)
    
    async def monitor_network_traffic(self):
        """Monitor network traffic statistics"""
        try:
            self.last_network_stats = psutil.net_io_counters()
        except:
            return
        
        while True:
            try:
                await asyncio.sleep(2)
                
                current_stats = psutil.net_io_counters()
                
                if self.last_network_stats:
                    bytes_sent_rate = (current_stats.bytes_sent - self.last_network_stats.bytes_sent) / 2
                    bytes_recv_rate = (current_stats.bytes_recv - self.last_network_stats.bytes_recv) / 2
                    packets_sent_rate = (current_stats.packets_sent - self.last_network_stats.packets_sent) / 2
                    packets_recv_rate = (current_stats.packets_recv - self.last_network_stats.packets_recv) / 2
                    
                    traffic_data = {
                        'timestamp': datetime.now().strftime("%H:%M:%S"),
                        'bytes_sent_rate': round(bytes_sent_rate),
                        'bytes_recv_rate': round(bytes_recv_rate),
                        'packets_sent_rate': round(packets_sent_rate, 1),
                        'packets_recv_rate': round(packets_recv_rate, 1),
                        'dummy_packets': self.padding_handler.get_stats()['dummy_packets_sent'] if self.padding_handler else 0
                    }
                    
                    self.stats['traffic_stats'].append(traffic_data)
                    
                    # Keep only last 30 data points
                    if len(self.stats['traffic_stats']) > 30:
                        self.stats['traffic_stats'] = self.stats['traffic_stats'][-30:]
                
                self.last_network_stats = current_stats
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(5)
    
    async def monitor_connections(self):
        """Monitor active network connections"""
        last_connections = set()
        
        while True:
            try:
                await asyncio.sleep(5)
                
                current_connections = set()
                connections = psutil.net_connections(kind='inet')
                
                for conn in connections:
                    if conn.status == 'ESTABLISHED' and conn.raddr:
                        conn_str = f"{conn.laddr.ip}:{conn.laddr.port} -> {conn.raddr.ip}:{conn.raddr.port}"
                        current_connections.add(conn_str)
                        
                        # Show new connections
                        if conn_str not in last_connections:
                            connection_data = {
                                'timestamp': datetime.now().strftime("%H:%M:%S"),
                                'local': f"{conn.laddr.ip}:{conn.laddr.port}",
                                'remote': f"{conn.raddr.ip}:{conn.raddr.port}",
                                'protocol': 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP',
                                'status': 'NEW'
                            }
                            
                            self.stats['network_connections'].append(connection_data)
                            
                            # Keep only last 15 connections
                            if len(self.stats['network_connections']) > 15:
                                self.stats['network_connections'] = self.stats['network_connections'][-15:]
                
                last_connections = current_connections
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(5)
    
    async def get_ip_information(self):
        """Get current IP and network information"""
        try:
            # Get network interfaces
            interfaces = []
            net_if_addrs = psutil.net_if_addrs()
            
            for interface_name, addresses in net_if_addrs.items():
                if 'Loopback' not in interface_name:
                    interface_info = {'name': interface_name, 'addresses': []}
                    for addr in addresses:
                        if addr.family == socket.AF_INET:
                            interface_info['addresses'].append(f"IPv4: {addr.address}")
                        elif addr.family == socket.AF_INET6 and not addr.address.startswith('fe80'):
                            interface_info['addresses'].append(f"IPv6: {addr.address[:20]}...")
                    if interface_info['addresses']:
                        interfaces.append(interface_info)
            
            # Try to get public IP
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get('https://api.ipify.org?format=json', timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            public_ip = data['ip']
                            
                            # Get location info
                            try:
                                async with session.get(f'http://ip-api.com/json/{public_ip}', timeout=10) as geo_response:
                                    if geo_response.status == 200:
                                        geo_data = await geo_response.json()
                                        self.stats['ip_info'] = {
                                            'public_ip': public_ip,
                                            'city': geo_data.get('city', 'Unknown'),
                                            'country': geo_data.get('country', 'Unknown'),
                                            'isp': geo_data.get('isp', 'Unknown'),
                                            'interfaces': interfaces
                                        }
                            except:
                                self.stats['ip_info'] = {
                                    'public_ip': public_ip,
                                    'interfaces': interfaces
                                }
            except:
                self.stats['ip_info'] = {'interfaces': interfaces}
                
        except Exception as e:
            self.stats['ip_info'] = {'error': str(e)}
    
    async def test_dns_queries(self):
        """Test DNS queries manually"""
        test_domains = ['google.com', 'github.com', 'stackoverflow.com']
        
        for domain in test_domains:
            try:
                start_time = time.time()
                ip_address = socket.gethostbyname(domain)
                response_time = round((time.time() - start_time) * 1000, 1)
                
                await self.add_event(f"DNS test: {domain} -> {ip_address} ({response_time}ms)")
            except Exception as e:
                await self.add_event(f"DNS test failed: {domain} -> {str(e)[:30]}")
    
    async def stop_all_and_prepare_shutdown(self):
        """Stop all protections and prepare for safe shutdown"""
        try:
            await self.add_event("Initiating safe shutdown sequence...")
            
            # Stop all monitoring
            await self.stop_live_monitoring()
            
            # Stop DNS protection
            if self.dns_handler:
                await self.stop_dns_protection()
            
            # Stop traffic obfuscation
            if self.padding_handler:
                await self.stop_padding_protection()
            
            await self.add_event("All protections stopped - safe to close terminal")
            
            # Notify clients
            await self.broadcast_status()
            
            # Send shutdown signal to clients
            shutdown_message = json.dumps({
                'type': 'shutdown_ready',
                'message': 'All protections stopped. Terminal can be safely closed.'
            })
            
            for ws in list(self.websockets):
                try:
                    await ws.send_str(shutdown_message)
                except:
                    pass
            
        except Exception as e:
            await self.add_event(f"Shutdown preparation error: {e}")
    
    async def add_event(self, message):
        """Add event to log"""
        event = {
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'message': message
        }
        self.stats['protection_events'].append(event)
        
        # Keep only last 20 events
        if len(self.stats['protection_events']) > 20:
            self.stats['protection_events'] = self.stats['protection_events'][-20:]
        """Add event to log"""
        event = {
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'message': message
        }
        self.stats['protection_events'].append(event)
        
        # Keep only last 20 events
        if len(self.stats['protection_events']) > 20:
            self.stats['protection_events'] = self.stats['protection_events'][-20:]
    
    async def get_current_stats(self):
        """Get current protection statistics"""
        current_stats = self.stats.copy()
        
        # Add real-time data
        if self.padding_handler and self.stats['padding_active']:
            padding_stats = self.padding_handler.get_stats()
            current_stats.update(padding_stats)
        
        # Calculate uptime
        if self.stats['start_time']:
            current_stats['uptime'] = int(time.time() - self.stats['start_time'])
        else:
            current_stats['uptime'] = 0
        
        return current_stats
    
    async def send_status_update(self, ws):
        """Send status update to specific WebSocket"""
        try:
            stats = await self.get_current_stats()
            await ws.send_str(json.dumps({
                'type': 'status_update',
                'data': stats
            }))
        except Exception as e:
            logger.error(f"Failed to send status update: {e}")
    
    async def broadcast_status(self):
        """Broadcast status to all connected WebSockets"""
        if not self.websockets:
            return
        
        stats = await self.get_current_stats()
        message = json.dumps({
            'type': 'status_update', 
            'data': stats
        })
        
        # Send to all connected clients
        disconnected = []
        for ws in self.websockets:
            try:
                await ws.send_str(message)
            except Exception:
                disconnected.append(ws)
        
        # Remove disconnected websockets
        for ws in disconnected:
            try:
                self.websockets.discard(ws)
            except:
                pass
    
    async def periodic_updates(self):
        """Send periodic status updates"""
        while True:
            try:
                await asyncio.sleep(2)  # Update every 2 seconds
                await self.broadcast_status()
            except Exception as e:
                logger.error(f"Periodic update error: {e}")
    
    async def index_handler(self, request):
        """Serve the main dashboard page"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>🛡️ Network Protection Monitor</title>
    <meta charset="utf-8">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0; padding: 20px; background: #1a1a1a; color: #fff;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #00ff88; margin: 0; }
        .controls { display: flex; gap: 20px; margin-bottom: 30px; justify-content: center; }
        .btn { 
            padding: 12px 24px; border: none; border-radius: 5px; 
            font-size: 16px; cursor: pointer; transition: all 0.3s;
        }
        .btn-start { background: #00ff88; color: #000; }
        .btn-stop { background: #ff4444; color: #fff; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.3); }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .status-card { 
            background: #2a2a2a; padding: 20px; border-radius: 10px; 
            border-left: 4px solid #00ff88;
        }
        .status-card h3 { margin-top: 0; color: #00ff88; }
        .status-indicator { 
            display: inline-block; width: 12px; height: 12px; 
            border-radius: 50%; margin-right: 8px;
        }
        .status-active { background: #00ff88; }
        .status-inactive { background: #666; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
        .stat-item { text-align: center; background: #333; padding: 15px; border-radius: 5px; }
        .stat-value { font-size: 24px; font-weight: bold; color: #00ff88; }
        .stat-label { font-size: 12px; color: #ccc; }
        .events { background: #2a2a2a; padding: 20px; border-radius: 10px; max-height: 300px; overflow-y: auto; }
        .events h3 { margin-top: 0; color: #00ff88; }
        .event { padding: 8px 0; border-bottom: 1px solid #333; font-family: monospace; }
        .event:last-child { border-bottom: none; }
        .timestamp { color: #888; margin-right: 10px; }
        .connection-status { 
            position: fixed; top: 20px; right: 20px; 
            padding: 10px; border-radius: 5px; font-size: 14px;
        }
        .connected { background: #00ff88; color: #000; }
        .disconnected { background: #ff4444; color: #fff; }
        
        /* DNS Queries Table */
        .dns-table, .traffic-table, .connections-table {
            background: #333; border-radius: 5px; overflow: hidden; margin-top: 10px;
        }
        .dns-header, .traffic-header, .connections-header {
            display: grid; grid-template-columns: 1fr 2fr 2fr 1fr 1fr; 
            background: #444; padding: 10px; font-weight: bold; color: #00ff88;
        }
        .dns-row, .traffic-row, .connection-row {
            display: grid; grid-template-columns: 1fr 2fr 2fr 1fr 1fr;
            padding: 8px 10px; border-bottom: 1px solid #555; font-family: monospace;
        }
        .dns-row:last-child, .traffic-row:last-child, .connection-row:last-child {
            border-bottom: none;
        }
        .encrypted { color: #00ff88; }
        .unencrypted { color: #ff4444; }
        .failed { color: #ff8844; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Network Protection Monitor</h1>
            <p>Real-time monitoring of DNS encryption and traffic obfuscation</p>
        </div>
        
        <div class="controls">
            <button class="btn btn-start" onclick="startDNS()">🌐 Start DNS Protection</button>
            <button class="btn btn-stop" onclick="stopDNS()">⏹️ Stop DNS Protection</button>
            <button class="btn btn-start" onclick="startPadding()">📦 Start Traffic Obfuscation</button>
            <button class="btn btn-stop" onclick="stopPadding()">⏹️ Stop Traffic Obfuscation</button>
            <button class="btn btn-start" onclick="startMonitoring()">👁️ Start Live Monitoring</button>
            <button class="btn btn-stop" onclick="stopMonitoring()">⏹️ Stop Monitoring</button>
            <button class="btn btn-stop" onclick="stopAllAndShutdown()" style="background: #cc0000; margin-left: 20px;">🛑 Stop All & Safe Shutdown</button>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>🌐 DNS Protection</h3>
                <p><span class="status-indicator" id="dns-indicator"></span><span id="dns-status">Inactive</span></p>
                <p>Encrypts DNS queries via HTTPS, prevents ISP from seeing visited websites</p>
            </div>
            
            <div class="status-card">
                <h3>📦 Traffic Obfuscation</h3>
                <p><span class="status-indicator" id="padding-indicator"></span><span id="padding-status">Inactive</span></p>
                <p>Generates dummy traffic and randomizes patterns to resist analysis</p>
            </div>
        </div>
        
        <div class="stats" id="stats">
            <div class="stat-item">
                <div class="stat-value" id="uptime">0</div>
                <div class="stat-label">Uptime (seconds)</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="dummy-packets">0</div>
                <div class="stat-label">Dummy Packets</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="padded-packets">0</div>
                <div class="stat-label">Padded Packets</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="bytes-added">0</div>
                <div class="stat-label">Bytes Added</div>
            </div>
        </div>
        
        <div class="events">
            <h3>📋 Protection Events</h3>
            <div id="events-list">
                <div class="event">
                    <span class="timestamp">--:--:--</span>
                    <span>System ready - click buttons above to start protection</span>
                </div>
            </div>
        </div>
        
        <!-- Live DNS Queries Section -->
        <div class="events">
            <h3>🌐 Live DNS Queries</h3>
            <div class="dns-table">
                <div class="dns-header">
                    <span>Time</span>
                    <span>Domain</span>
                    <span>IP Address</span>
                    <span>Response</span>
                    <span>Status</span>
                </div>
                <div id="dns-queries-list">
                    <div class="dns-row">
                        <span>--:--:--</span>
                        <span>No queries yet</span>
                        <span>-</span>
                        <span>-</span>
                        <span>-</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Network Traffic Section -->
        <div class="events">
            <h3>📏 Network Traffic</h3>
            <div class="traffic-table">
                <div class="traffic-header">
                    <span>Time</span>
                    <span>⬆️ Upload B/s</span>
                    <span>⬇️ Download B/s</span>
                    <span>📦 Packets/s</span>
                    <span>🎭 Dummy</span>
                </div>
                <div id="traffic-stats-list">
                    <div class="traffic-row">
                        <span>--:--:--</span>
                        <span>0</span>
                        <span>0</span>
                        <span>0</span>
                        <span>0</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Network Connections Section -->
        <div class="events">
            <h3>🔗 Active Connections</h3>
            <div class="connections-table">
                <div class="connections-header">
                    <span>Time</span>
                    <span>Local Address</span>
                    <span>Remote Address</span>
                    <span>Protocol</span>
                    <span>Status</span>
                </div>
                <div id="connections-list">
                    <div class="connection-row">
                        <span>--:--:--</span>
                        <span>No connections</span>
                        <span>-</span>
                        <span>-</span>
                        <span>-</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- IP Information Section -->
        <div class="status-card">
            <h3>🌍 IP & Network Information</h3>
            <div id="ip-info">
                <p>Loading network information...</p>
            </div>
        </div>
    </div>
    
    <div class="connection-status disconnected" id="connection-status">
        Disconnected
    </div>
    
    <script>
        let ws = null;
        
        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            ws.onopen = function() {
                document.getElementById('connection-status').className = 'connection-status connected';
                document.getElementById('connection-status').textContent = 'Connected';
                ws.send(JSON.stringify({action: 'get_status'}));
            };
            
            ws.onclose = function() {
                document.getElementById('connection-status').className = 'connection-status disconnected';
                document.getElementById('connection-status').textContent = 'Disconnected';
                setTimeout(connect, 2000); // Reconnect after 2 seconds
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                if (message.type === 'status_update') {
                    updateStatus(message.data);
                } else if (message.type === 'shutdown') {
                    // Handle server shutdown
                    document.getElementById('connection-status').className = 'connection-status disconnected';
                    document.getElementById('connection-status').textContent = 'Server Shutting Down';
                    
                    // Show shutdown message
                    alert('⚠️ Server is shutting down. All protections have been stopped and system settings restored.');
                }
            };
        }
        
        function updateStatus(data) {
            // Update DNS status
            const dnsIndicator = document.getElementById('dns-indicator');
            const dnsStatus = document.getElementById('dns-status');
            if (data.dns_active) {
                dnsIndicator.className = 'status-indicator status-active';
                dnsStatus.textContent = 'Active - DNS queries encrypted';
            } else {
                dnsIndicator.className = 'status-indicator status-inactive';
                dnsStatus.textContent = 'Inactive';
            }
            
            // Update padding status
            const paddingIndicator = document.getElementById('padding-indicator');
            const paddingStatus = document.getElementById('padding-status');
            if (data.padding_active) {
                paddingIndicator.className = 'status-indicator status-active';
                paddingStatus.textContent = 'Active - Traffic obfuscated';
            } else {
                paddingIndicator.className = 'status-indicator status-inactive';
                paddingStatus.textContent = 'Inactive';
            }
            
            // Update stats
            document.getElementById('uptime').textContent = data.uptime || 0;
            document.getElementById('dummy-packets').textContent = data.dummy_packets_sent || 0;
            document.getElementById('padded-packets').textContent = data.packets_padded || 0;
            document.getElementById('bytes-added').textContent = data.bytes_added || 0;
            
            // Update events
            if (data.protection_events) {
                const eventsList = document.getElementById('events-list');
                eventsList.innerHTML = '';
                data.protection_events.forEach(event => {
                    const eventDiv = document.createElement('div');
                    eventDiv.className = 'event';
                    eventDiv.innerHTML = `<span class="timestamp">${event.timestamp}</span><span>${event.message}</span>`;
                    eventsList.appendChild(eventDiv);
                });
            }
            
            // Update DNS queries
            if (data.live_dns_queries) {
                const dnsQueriesList = document.getElementById('dns-queries-list');
                dnsQueriesList.innerHTML = '';
                data.live_dns_queries.forEach(query => {
                    const queryDiv = document.createElement('div');
                    queryDiv.className = 'dns-row';
                    const statusClass = query.encrypted ? 'encrypted' : (query.ip === 'FAILED' ? 'failed' : 'unencrypted');
                    const statusText = query.encrypted ? '🔒 ENC' : (query.ip === 'FAILED' ? '❌ FAIL' : '❌ RAW');
                    queryDiv.innerHTML = `
                        <span>${query.timestamp}</span>
                        <span>${query.domain}</span>
                        <span>${query.ip}</span>
                        <span>${query.response_time}ms</span>
                        <span class="${statusClass}">${statusText}</span>
                    `;
                    dnsQueriesList.appendChild(queryDiv);
                });
            }
            
            // Update traffic stats
            if (data.traffic_stats) {
                const trafficStatsList = document.getElementById('traffic-stats-list');
                trafficStatsList.innerHTML = '';
                data.traffic_stats.slice(-10).forEach(stat => {
                    const statDiv = document.createElement('div');
                    statDiv.className = 'traffic-row';
                    statDiv.innerHTML = `
                        <span>${stat.timestamp}</span>
                        <span>${stat.bytes_sent_rate}</span>
                        <span>${stat.bytes_recv_rate}</span>
                        <span>${stat.packets_sent_rate}</span>
                        <span class="encrypted">${stat.dummy_packets}</span>
                    `;
                    trafficStatsList.appendChild(statDiv);
                });
            }
            
            // Update network connections
            if (data.network_connections) {
                const connectionsList = document.getElementById('connections-list');
                connectionsList.innerHTML = '';
                data.network_connections.forEach(conn => {
                    const connDiv = document.createElement('div');
                    connDiv.className = 'connection-row';
                    connDiv.innerHTML = `
                        <span>${conn.timestamp}</span>
                        <span>${conn.local}</span>
                        <span>${conn.remote}</span>
                        <span>${conn.protocol}</span>
                        <span class="encrypted">${conn.status}</span>
                    `;
                    connectionsList.appendChild(connDiv);
                });
            }
            
            // Update IP information
            if (data.ip_info) {
                const ipInfo = document.getElementById('ip-info');
                let html = '';
                
                if (data.ip_info.public_ip) {
                    html += `<p><strong>🌍 Public IP:</strong> ${data.ip_info.public_ip}</p>`;
                }
                if (data.ip_info.city && data.ip_info.country) {
                    html += `<p><strong>📍 Location:</strong> ${data.ip_info.city}, ${data.ip_info.country}</p>`;
                }
                if (data.ip_info.isp) {
                    html += `<p><strong>🏢 ISP:</strong> ${data.ip_info.isp}</p>`;
                }
                
                if (data.ip_info.interfaces) {
                    html += '<p><strong>🔌 Network Interfaces:</strong></p>';
                    data.ip_info.interfaces.forEach(iface => {
                        html += `<p style="margin-left: 20px;"><strong>${iface.name}:</strong><br>`;
                        iface.addresses.forEach(addr => {
                            html += `&nbsp;&nbsp;${addr}<br>`;
                        });
                        html += '</p>';
                    });
                }
                
                if (data.ip_info.error) {
                    html = `<p>❌ Error: ${data.ip_info.error}</p>`;
                }
                
                ipInfo.innerHTML = html || '<p>No IP information available</p>';
            }
        }
        
        function startDNS() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: 'start_dns'}));
            }
        }
        
        function stopDNS() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: 'stop_dns'}));
            }
        }
        
        function startPadding() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: 'start_padding'}));
            }
        }
        
        function stopPadding() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: 'stop_padding'}));
            }
        }
        
        function startMonitoring() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: 'start_monitoring'}));
            }
        }
        
        function stopMonitoring() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: 'stop_monitoring'}));
            }
        }
        
        function testDNS() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: 'test_dns'}));
            }
        }
        
        function stopAllAndShutdown() {
            if (confirm('⚠️ This will stop ALL protections and prepare for safe shutdown. Continue?')) {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({action: 'stop_all_shutdown'}));
                }
            }
        }
        
        // Connect on page load
        connect();
    </script>
</body>
</html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def create_app(self):
        """Create the web application"""
        app = web.Application()
        
        # Add routes
        app.router.add_get('/', self.index_handler)
        app.router.add_get('/ws', self.websocket_handler)
        
        # Setup CORS
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Add CORS to all routes
        for route in list(app.router.routes()):
            cors.add(route)
        
        return app
    
    async def run_server(self, host='localhost', port=8080):
        """Run the web server"""
        self.app = await self.create_app()
        
        # Start periodic updates task
        asyncio.create_task(self.periodic_updates())
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        print(f"🌐 Web monitor started at http://{host}:{port}")
        print("🔍 Open this URL in your browser to see real-time protection status")
        print("🚨 IMPORTANT: When you're done, use the STOP buttons in web interface first!")
        print("🚨 Then press Ctrl+C to safely shutdown and restore system settings")
        print("Press Ctrl+C to stop")
        
        try:
            # Keep the server running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping web monitor...")
        finally:
            await self.cleanup()
            await runner.cleanup()
    
    async def cleanup(self):
        """Clean up resources and restore system settings"""
        try:
            print("\n🛑 Cleaning up and restoring system settings...")
            
            # Stop all monitoring tasks first
            for task in self.monitoring_tasks:
                task.cancel()
            self.monitoring_tasks = []
            
            # Stop protection handlers and restore settings
            if self.dns_handler:
                print("🌐 Stopping DNS protection and restoring DNS settings...")
                await self.dns_handler.stop()
                self.dns_handler = None
                print("✅ DNS settings restored")
                
            if self.padding_handler:
                print("📦 Stopping traffic obfuscation...")
                await self.padding_handler.stop()
                self.padding_handler = None
                print("✅ Traffic obfuscation stopped")
            
            # Notify all connected clients about shutdown
            if self.websockets:
                shutdown_message = json.dumps({
                    'type': 'shutdown',
                    'message': 'Server shutting down - all protections stopped'
                })
                
                for ws in list(self.websockets):
                    try:
                        await ws.send_str(shutdown_message)
                        await ws.close()
                    except:
                        pass
            
            print("✅ All protections stopped and system restored to normal")
            print("✅ Safe to close terminal")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            print(f"⚠️  Cleanup error: {e}")
            print("🔧 Manual cleanup may be required")

def main():
    """Entry point"""
    monitor = WebMonitor()
    try:
        asyncio.run(monitor.run_server())
    except KeyboardInterrupt:
        print("Web monitor stopped.")

if __name__ == "__main__":
    main()