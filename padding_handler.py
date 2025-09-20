"""
Packet Padding and Timing Obfuscation Handler
Implements traffic analysis resistance through packet padding and timing manipulation
"""

import asyncio
import random
import time
import logging
import socket
import struct
import platform
from typing import Optional, List, Dict, Tuple
import threading
# Try to import scapy, but continue without it if not available
try:
    from scapy.all import *
    from scapy.layers.inet import IP, TCP, UDP
    from scapy.layers.l2 import Ether
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Scapy not available - packet analysis features disabled")

# Platform-specific imports
if platform.system() == 'Windows':
    try:
        import pydivert
        PYDIVERT_AVAILABLE = True
    except ImportError:
        pydivert = None
        PYDIVERT_AVAILABLE = False
        logger = logging.getLogger(__name__)
        logger.warning("pydivert not available - packet interception disabled on Windows")
else:
    try:
        from netfilterqueue import NetfilterQueue
        NETFILTERQUEUE_AVAILABLE = True
    except ImportError:
        NetfilterQueue = None
        NETFILTERQUEUE_AVAILABLE = False
        logger = logging.getLogger(__name__)
        logger.warning("netfilterqueue not available - packet interception disabled on Linux")

logger = logging.getLogger(__name__)

class PaddingHandler:
    """
    Handles packet padding and timing obfuscation to resist traffic analysis
    Implements constant packet size and timing randomization
    """
    
    def __init__(self):
        self.running = False
        self.target_packet_size = 512  # Target packet size in bytes
        self.min_delay = 0.05  # Minimum delay between packets (50ms)
        self.max_delay = 0.15  # Maximum delay between packets (150ms)
        self.dummy_traffic_interval = 5.0  # Dummy traffic every 5 seconds
        
        # Traffic statistics
        self.stats = {
            'packets_padded': 0,
            'packets_delayed': 0,
            'dummy_packets_sent': 0,
            'bytes_added': 0
        }
        
        # Platform-specific handlers
        self.packet_interceptor = None
        self.dummy_traffic_task = None
        self.timing_task = None
        
        # Advanced mode settings
        self.advanced_mode = False
        self.cover_traffic_patterns = []
        self.burst_protection = True
    
    async def start(self):
        """Start basic packet padding and timing obfuscation"""
        logger.info("Starting packet padding and timing obfuscation")
        
        self.running = True
        
        try:
            # Start packet interception for padding
            await self._start_packet_interception()
            
            # Start dummy traffic generation
            self.dummy_traffic_task = asyncio.create_task(self._generate_dummy_traffic())
            
            # Start timing obfuscation
            self.timing_task = asyncio.create_task(self._timing_obfuscation())
            
            logger.info("Packet padding and timing obfuscation started")
            
        except Exception as e:
            logger.error(f"Failed to start padding handler: {e}")
            await self.stop()
            raise
    
    async def start_advanced(self):
        """Start advanced packet padding with sophisticated traffic patterns"""
        logger.info("Starting advanced packet padding and timing obfuscation")
        
        self.advanced_mode = True
        self.running = True
        
        try:
            # Initialize advanced cover traffic patterns
            self._initialize_cover_patterns()
            
            # Start packet interception
            await self._start_packet_interception()
            
            # Start advanced dummy traffic generation
            self.dummy_traffic_task = asyncio.create_task(self._generate_advanced_dummy_traffic())
            
            # Start sophisticated timing obfuscation
            self.timing_task = asyncio.create_task(self._advanced_timing_obfuscation())
            
            logger.info("Advanced packet padding and timing obfuscation started")
            
        except Exception as e:
            logger.error(f"Failed to start advanced padding handler: {e}")
            await self.stop()
            raise
    
    def _initialize_cover_patterns(self):
        """Initialize cover traffic patterns for advanced mode"""
        # Common web browsing patterns
        self.cover_traffic_patterns = [
            {
                'name': 'web_browsing',
                'packet_sizes': [64, 128, 256, 512, 1024, 1460],
                'intervals': [0.1, 0.2, 0.5, 1.0, 2.0],
                'burst_size': (3, 8),
                'probability': 0.4
            },
            {
                'name': 'video_streaming',
                'packet_sizes': [1024, 1460, 1500],
                'intervals': [0.02, 0.03, 0.04],
                'burst_size': (10, 25),
                'probability': 0.3
            },
            {
                'name': 'file_download',
                'packet_sizes': [1460, 1500],
                'intervals': [0.01, 0.02],
                'burst_size': (50, 100),
                'probability': 0.2
            },
            {
                'name': 'background_updates',
                'packet_sizes': [64, 128, 256],
                'intervals': [5.0, 10.0, 30.0],
                'burst_size': (1, 3),
                'probability': 0.1
            }
        ]
    
    async def _start_packet_interception(self):
        """Start packet interception based on platform"""
        try:
            if platform.system() == 'Windows' and PYDIVERT_AVAILABLE:
                await self._start_windows_interception()
            elif platform.system() == 'Linux' and NETFILTERQUEUE_AVAILABLE:
                await self._start_linux_interception()
            else:
                logger.warning("Packet interception not available, using dummy traffic only")
                
        except Exception as e:
            logger.error(f"Failed to start packet interception: {e}")
            # Continue without packet interception, rely on dummy traffic
    
    async def _start_windows_interception(self):
        """Start packet interception on Windows using WinDivert"""
        try:
            if not PYDIVERT_AVAILABLE or not pydivert:
                raise RuntimeError("pydivert not available")
                
            # Create WinDivert handle for outbound packets
            self.packet_interceptor = pydivert.WinDivert(
                "outbound and tcp.PayloadLength > 0"
            )
            
            # Start packet processing in separate thread
            self.intercept_thread = threading.Thread(
                target=self._windows_packet_loop,
                daemon=True
            )
            self.intercept_thread.start()
            
            logger.info("Windows packet interception started")
            
        except Exception as e:
            logger.error(f"Failed to start Windows packet interception: {e}")
            raise
    
    def _windows_packet_loop(self):
        """Windows packet processing loop"""
        try:
            self.packet_interceptor.open()
            
            while self.running:
                try:
                    # Capture packet
                    packet = self.packet_interceptor.recv()
                    
                    if packet:
                        # Process packet (add padding, apply delay)
                        modified_packet = self._process_packet(packet.raw)
                        
                        if modified_packet:
                            # Apply timing delay
                            if self.advanced_mode:
                                delay = self._calculate_advanced_delay()
                            else:
                                delay = random.uniform(self.min_delay, self.max_delay)
                            
                            time.sleep(delay)
                            
                            # Send modified packet
                            packet.raw = modified_packet
                            self.packet_interceptor.send(packet)
                            
                            self.stats['packets_delayed'] += 1
                        else:
                            # Send original packet
                            self.packet_interceptor.send(packet)
                
                except Exception as e:
                    if self.running:
                        logger.error(f"Error in Windows packet loop: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Windows packet loop error: {e}")
        finally:
            if self.packet_interceptor:
                self.packet_interceptor.close()
    
    async def _start_linux_interception(self):
        """Start packet interception on Linux using netfilterqueue"""
        try:
            if not NETFILTERQUEUE_AVAILABLE or not NetfilterQueue:
                raise RuntimeError("netfilterqueue not available")
                
            # Create netfilter queue
            self.nfqueue = NetfilterQueue()
            self.nfqueue.bind(0, self._linux_packet_callback)
            
            # Start netfilter processing in separate thread
            self.intercept_thread = threading.Thread(
                target=self._linux_packet_loop,
                daemon=True
            )
            self.intercept_thread.start()
            
            logger.info("Linux packet interception started")
            
        except Exception as e:
            logger.error(f"Failed to start Linux packet interception: {e}")
            raise
    
    def _linux_packet_loop(self):
        """Linux packet processing loop"""
        try:
            self.nfqueue.run()
        except Exception as e:
            if self.running:
                logger.error(f"Linux packet loop error: {e}")
    
    def _linux_packet_callback(self, packet):
        """Callback for Linux netfilter packet processing"""
        try:
            # Process packet (add padding, apply delay)
            modified_payload = self._process_packet(packet.get_payload())
            
            if modified_payload:
                # Apply timing delay
                if self.advanced_mode:
                    delay = self._calculate_advanced_delay()
                else:
                    delay = random.uniform(self.min_delay, self.max_delay)
                
                time.sleep(delay)
                
                # Set modified payload and accept
                packet.set_payload(modified_payload)
                packet.accept()
                
                self.stats['packets_delayed'] += 1
            else:
                # Accept original packet
                packet.accept()
                
        except Exception as e:
            logger.error(f"Error in Linux packet callback: {e}")
            packet.accept()  # Accept packet to avoid blocking
    
    def _process_packet(self, packet_data: bytes) -> Optional[bytes]:
        """
        Process packet by adding padding if necessary
        
        Args:
            packet_data: Raw packet data
            
        Returns:
            Modified packet data or None if no modification needed
        """
        try:
            if len(packet_data) >= self.target_packet_size:
                return None  # Packet is already large enough
            
            # Calculate padding needed
            padding_needed = self.target_packet_size - len(packet_data)
            
            # Add random padding
            padding = self._generate_padding(padding_needed)
            modified_packet = packet_data + padding
            
            self.stats['packets_padded'] += 1
            self.stats['bytes_added'] += padding_needed
            
            return modified_packet
            
        except Exception as e:
            logger.error(f"Error processing packet: {e}")
            return None
    
    def _generate_padding(self, size: int) -> bytes:
        """
        Generate padding bytes
        
        Args:
            size: Number of padding bytes needed
            
        Returns:
            Padding bytes
        """
        # Generate pseudo-random padding that looks like real data
        padding = bytearray()
        
        for i in range(size):
            # Mix of common byte values found in network traffic
            if i % 8 == 0:
                padding.append(0x00)  # NULL bytes
            elif i % 8 == 1:
                padding.append(0x20)  # Space character
            elif i % 8 == 2:
                padding.append(random.randint(0x41, 0x5A))  # Uppercase letters
            elif i % 8 == 3:
                padding.append(random.randint(0x61, 0x7A))  # Lowercase letters
            elif i % 8 == 4:
                padding.append(random.randint(0x30, 0x39))  # Numbers
            else:
                padding.append(random.randint(0x01, 0xFF))  # Random bytes
        
        return bytes(padding)
    
    async def _generate_dummy_traffic(self):
        """Generate dummy traffic to obscure real traffic patterns"""
        logger.info("Starting dummy traffic generation")
        
        dummy_destinations = [
            ('8.8.8.8', 53),      # Google DNS
            ('1.1.1.1', 53),      # Cloudflare DNS
            ('208.67.222.222', 53), # OpenDNS
            ('9.9.9.9', 53)       # Quad9 DNS
        ]
        
        while self.running:
            try:
                # Wait for interval
                await asyncio.sleep(self.dummy_traffic_interval + random.uniform(-1, 1))
                
                if not self.running:
                    break
                
                # Generate dummy packets
                for _ in range(random.randint(1, 3)):
                    destination = random.choice(dummy_destinations)
                    await self._send_dummy_packet(destination[0], destination[1])
                    
                    # Small delay between dummy packets
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                
            except Exception as e:
                logger.error(f"Error generating dummy traffic: {e}")
                await asyncio.sleep(1)
    
    async def _generate_advanced_dummy_traffic(self):
        """Generate sophisticated dummy traffic patterns"""
        logger.info("Starting advanced dummy traffic generation")
        
        while self.running:
            try:
                # Select a traffic pattern
                pattern = self._select_traffic_pattern()
                
                # Generate burst of packets according to pattern
                burst_size = random.randint(*pattern['burst_size'])
                
                for i in range(burst_size):
                    if not self.running:
                        break
                    
                    # Select packet size and destination
                    packet_size = random.choice(pattern['packet_sizes'])
                    destination = self._select_dummy_destination(pattern)
                    
                    # Send dummy packet
                    await self._send_dummy_packet(
                        destination[0], destination[1], packet_size
                    )
                    
                    # Inter-packet delay within burst
                    if i < burst_size - 1:
                        delay = random.choice(pattern['intervals'])
                        await asyncio.sleep(delay)
                
                # Inter-burst delay
                await asyncio.sleep(random.uniform(1, 5))
                
            except Exception as e:
                logger.error(f"Error generating advanced dummy traffic: {e}")
                await asyncio.sleep(1)
    
    def _select_traffic_pattern(self) -> Dict:
        """Select a traffic pattern based on probabilities"""
        rand = random.random()
        cumulative_prob = 0
        
        for pattern in self.cover_traffic_patterns:
            cumulative_prob += pattern['probability']
            if rand <= cumulative_prob:
                return pattern
        
        # Fallback to first pattern
        return self.cover_traffic_patterns[0]
    
    def _select_dummy_destination(self, pattern: Dict) -> Tuple[str, int]:
        """Select appropriate destination for dummy traffic pattern"""
        if pattern['name'] == 'web_browsing':
            destinations = [
                ('www.google.com', 80),
                ('www.cloudflare.com', 443),
                ('www.github.com', 443),
                ('www.stackoverflow.com', 443)
            ]
        elif pattern['name'] == 'video_streaming':
            destinations = [
                ('youtube.com', 443),
                ('netflix.com', 443),
                ('twitch.tv', 443)
            ]
        elif pattern['name'] == 'file_download':
            destinations = [
                ('archive.org', 443),
                ('download.mozilla.org', 443)
            ]
        else:  # background_updates
            destinations = [
                ('update.microsoft.com', 443),
                ('dl.google.com', 443)
            ]
        
        return random.choice(destinations)
    
    async def _send_dummy_packet(self, host: str, port: int, size: Optional[int] = None):
        """
        Send a dummy packet to specified destination
        
        Args:
            host: Destination host
            port: Destination port
            size: Packet size (if None, use random size)
        """
        try:
            if size is None:
                size = random.randint(64, self.target_packet_size)
            
            # Create dummy data
            dummy_data = self._generate_padding(size)
            
            # Try to send UDP packet (less likely to cause issues)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            
            try:
                await asyncio.get_event_loop().sock_sendto(
                    sock, dummy_data[:size], (host, port)
                )
                
                self.stats['dummy_packets_sent'] += 1
                logger.debug(f"Sent dummy packet to {host}:{port} ({size} bytes)")
                
            except Exception:
                pass  # Ignore errors (expected for dummy traffic)
            finally:
                sock.close()
                
        except Exception as e:
            logger.debug(f"Error sending dummy packet: {e}")
    
    async def _timing_obfuscation(self):
        """Basic timing obfuscation"""
        while self.running:
            try:
                # Random delay to break timing patterns
                delay = random.uniform(0.1, 2.0)
                await asyncio.sleep(delay)
                
                # Occasionally send a burst of dummy packets
                if random.random() < 0.1:  # 10% chance
                    for _ in range(random.randint(2, 5)):
                        await self._send_dummy_packet('8.8.8.8', 53)
                        await asyncio.sleep(random.uniform(0.01, 0.05))
                
            except Exception as e:
                logger.error(f"Error in timing obfuscation: {e}")
                await asyncio.sleep(1)
    
    async def _advanced_timing_obfuscation(self):
        """Advanced timing obfuscation with burst protection"""
        burst_detector = BurstDetector()
        
        while self.running:
            try:
                # Monitor for traffic bursts
                if self.burst_protection and burst_detector.detect_burst():
                    # Add cover traffic during bursts
                    await self._add_burst_cover_traffic()
                
                # Adaptive timing based on current traffic
                delay = self._calculate_adaptive_delay()
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error in advanced timing obfuscation: {e}")
                await asyncio.sleep(1)
    
    def _calculate_advanced_delay(self) -> float:
        """Calculate delay for advanced timing obfuscation"""
        # Use multiple factors to determine delay
        base_delay = random.uniform(self.min_delay, self.max_delay)
        
        # Add jitter based on time of day (simulate human behavior)
        hour = time.localtime().tm_hour
        if 9 <= hour <= 17:  # Business hours
            jitter = random.uniform(0.8, 1.2)
        elif 22 <= hour or hour <= 6:  # Night hours
            jitter = random.uniform(1.5, 2.5)
        else:  # Evening hours
            jitter = random.uniform(1.0, 1.8)
        
        return base_delay * jitter
    
    def _calculate_adaptive_delay(self) -> float:
        """Calculate adaptive delay based on current traffic patterns"""
        # Simplified adaptive delay calculation
        base_delay = random.uniform(0.1, 1.0)
        
        # Adjust based on recent packet statistics
        if self.stats['packets_padded'] > 100:
            # High padding activity, reduce delay
            base_delay *= 0.8
        
        if self.stats['dummy_packets_sent'] > 500:
            # High dummy traffic, can increase delay
            base_delay *= 1.2
        
        return min(base_delay, 3.0)  # Cap at 3 seconds
    
    async def _add_burst_cover_traffic(self):
        """Add cover traffic during detected bursts"""
        try:
            # Send random cover packets
            for _ in range(random.randint(3, 8)):
                size = random.randint(64, 1024)
                await self._send_dummy_packet('1.1.1.1', 53, size)
                await asyncio.sleep(random.uniform(0.01, 0.1))
            
        except Exception as e:
            logger.error(f"Error adding burst cover traffic: {e}")
    
    async def stop(self):
        """Stop packet padding and timing obfuscation"""
        logger.info("Stopping packet padding and timing obfuscation")
        
        self.running = False
        
        try:
            # Stop tasks
            if self.dummy_traffic_task:
                self.dummy_traffic_task.cancel()
                try:
                    await self.dummy_traffic_task
                except asyncio.CancelledError:
                    pass
            
            if self.timing_task:
                self.timing_task.cancel()
                try:
                    await self.timing_task
                except asyncio.CancelledError:
                    pass
            
            # Stop packet interception
            if hasattr(self, 'packet_interceptor') and self.packet_interceptor:
                if platform.system() == 'Windows':
                    self.packet_interceptor.close()
                elif platform.system() == 'Linux':
                    self.nfqueue.unbind()
            
            # Wait for interception thread to finish
            if hasattr(self, 'intercept_thread') and self.intercept_thread.is_alive():
                self.intercept_thread.join(timeout=2)
            
            logger.info(f"Padding handler stopped. Stats: {self.stats}")
            
        except Exception as e:
            logger.error(f"Error stopping padding handler: {e}")
    
    def get_stats(self) -> Dict:
        """Get current padding statistics"""
        return self.stats.copy()

class BurstDetector:
    """Detects traffic bursts for burst protection"""
    
    def __init__(self, window_size: int = 10, threshold: int = 5):
        self.window_size = window_size
        self.threshold = threshold
        self.packet_times = []
    
    def detect_burst(self) -> bool:
        """
        Detect if current traffic shows burst pattern
        
        Returns:
            True if burst detected, False otherwise
        """
        current_time = time.time()
        
        # Add current time
        self.packet_times.append(current_time)
        
        # Remove old times outside window
        cutoff_time = current_time - self.window_size
        self.packet_times = [t for t in self.packet_times if t > cutoff_time]
        
        # Check if packet count exceeds threshold
        return len(self.packet_times) > self.threshold