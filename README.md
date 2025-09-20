# UndercoverNet

# 🛡️ Advanced Network Traffic Obfuscation System

A sophisticated multi-layer network privacy protection system that implements three distinct architectures for traffic obfuscation and ISP evasion.

## 🎯 Overview

This application provides advanced network traffic obfuscation through multiple privacy architectures:

1. **WireGuard + obfs4**: VPN with pluggable transport obfuscation
2. **Tor + meek**: Anonymous routing with domain fronting 
3. **Multi-layer**: Shadowsocks + WireGuard/Tor with advanced padding

All architectures include DNS-over-HTTPS, packet padding, timing obfuscation, and automatic kill switch protection.

## ✨ Features

- 🔒 **Multi-layer encryption** with industry-standard protocols
- 🎭 **Traffic obfuscation** to bypass deep packet inspection
- 🌐 **Domain fronting** support (Azure, Cloudflare, Amazon CDNs)
- 🛡️ **Automatic kill switch** prevents traffic leaks
- 🔄 **DNS-over-HTTPS** with multiple providers
- 📊 **Packet padding** and timing randomization
- 🎛️ **Terminal interface** for easy operation
- 🔧 **Modular architecture** for easy customization

## 🏗️ Architecture Overview

### Architecture A: WireGuard + obfs4
```
[Your Device] → [obfs4 Layer] → [WireGuard VPN] → [Target Server]
              ↓
         [DNS-over-HTTPS] + [Packet Padding] + [Kill Switch]
```

### Architecture B: Tor + meek
```
[Your Device] → [meek Domain Fronting] → [Tor Network] → [Target Server]
              ↓
         [Tor DNS] + [Packet Padding] + [Kill Switch]
```

### Architecture C: Multi-layer
```
[Your Device] → [Shadowsocks] → [WireGuard/Tor] → [Target Server]
              ↓
         [DNS-over-HTTPS Proxy] + [Advanced Padding] + [Kill Switch]
```

## 📋 Requirements

### System Requirements
- **Python 3.11+**
- **Administrator/Root privileges** (required for firewall operations)
- **8GB RAM** (recommended)
- **Windows 10/11**, **Linux**, or **macOS**

### Required External Tools

#### Windows
```powershell
# Install Chocolatey (if not already installed)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install required tools
choco install tor wireguard shadowsocks-libev
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install tor obfs4proxy wireguard-tools shadowsocks-libev python3-pip python3-dev build-essential libnetfilter-queue-dev
```

#### CentOS/RHEL/Fedora
```bash
sudo dnf install tor obfs4proxy wireguard-tools shadowsocks-libev python3-pip python3-devel gcc libnetfilter_queue-devel
```

#### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install tor wireguard-tools shadowsocks-libev
```

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-repo/network-obfuscation.git
cd network-obfuscation
```

### 2. Install Python Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Platform-Specific Setup

#### Windows Additional Setup
```powershell
# Install WinDivert for packet interception
# Download from: https://www.reqrypt.org/windivert.html
# Extract to system PATH or application directory
```

#### Linux Additional Setup
```bash
# Install additional networking tools
sudo apt install iptables-persistent socat

# Enable IP forwarding (optional, for some configurations)
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 4. Configuration

#### WireGuard Configuration
1. Copy `wireguard_example.conf` to `wireguard.conf`
2. Replace placeholder values with your WireGuard server details:
```bash
cp wireguard_example.conf wireguard.conf
# Edit wireguard.conf with your server details
```

#### Shadowsocks Configuration  
1. Copy `shadowsocks_example.json` to `shadowsocks.json`
2. Replace with your Shadowsocks server details:
```bash
cp shadowsocks_example.json shadowsocks.json
# Edit shadowsocks.json with your server details
```

#### obfs4 Bridges
1. Get real bridge lines from [bridges.torproject.org](https://bridges.torproject.org/)
2. Update `obfs4_bridges.conf` with real bridge lines

## 🎮 Usage

### Basic Usage
```bash
# Run with administrator/root privileges
sudo python main.py  # Linux/macOS
# or
python main.py  # Windows (run as Administrator)
```

### Command Line Options
```bash
# Start with specific architecture
python main.py --architecture wireguard_obfs4
python main.py --architecture tor_meek  
python main.py --architecture multilayer

# Start with custom configuration
python main.py --config custom_config.json

# Enable debug mode
python main.py --debug

# Show help
python main.py --help
```

### Interactive Menu
The application provides an interactive terminal menu:

```
╔══════════════════════════════════════════════════════════════╗
║            Advanced Network Traffic Obfuscation              ║
║                   Privacy Protection System                  ║
╠══════════════════════════════════════════════════════════════╣
║  Multi-layer encryption • Traffic masking • ISP evasion     ║
╚══════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────┐
│                  Select Protection Architecture             │
├─────────────────────────────────────────────────────────────┤
│  [1] WireGuard + obfs4                                      │
│  [2] Tor + meek (domain fronting)                          │
│  [3] Multi-layer (Shadowsocks + WireGuard/Tor + DoH)       │
│  [0] Exit                                                   │
└─────────────────────────────────────────────────────────────┘

Enter your choice (0-3):
```

## ⚙️ Configuration

### Main Configuration (`config.json`)

The main configuration file controls all aspects of the application:

```json
{
  "dns": {
    "default_provider": "cloudflare",
    "fallback_servers": ["8.8.8.8", "1.1.1.1"]
  },
  "firewall": {
    "kill_switch_enabled": true,
    "backup_rules": true
  },
  "padding": {
    "target_packet_size": 512,
    "advanced_mode": false
  }
}
```

### Architecture-Specific Configurations

Each architecture has its own configuration section in `config.json` and separate configuration files for detailed settings.

## 🔧 Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Ensure you're running with proper privileges
sudo python main.py  # Linux/macOS
# Run PowerShell/Command Prompt as Administrator on Windows
```

#### Firewall Issues
```bash
# Temporarily disable firewall for testing (not recommended for production)
# Windows:
netsh advfirewall set allprofiles state off

# Ubuntu:
sudo ufw disable

# Re-enable after testing
```

#### Package Installation Issues
```bash
# For netfilterqueue on Linux:
sudo apt install python3-dev libnetfilter-queue-dev
pip install --upgrade netfilterqueue

# For pydivert on Windows:
pip install --upgrade pydivert
```

#### Binary Not Found Errors
```bash
# Ensure all required binaries are in PATH
which tor obfs4proxy wg ss-local  # Linux/macOS
where tor obfs4proxy wg ss-local  # Windows
```

### Debug Mode
Enable debug mode for detailed logging:
```bash
python main.py --debug
```

### Log Files
Check log files for detailed error information:
- `network_obfuscation.log` - Main application log
- `tor.log` - Tor-specific logs (in temp directory)

## 🔒 Security Considerations

### Important Security Notes

1. **Always run with kill switch enabled** to prevent traffic leaks
2. **Use real bridge/server configurations** - examples are for testing only
3. **Regularly update bridge lines** to maintain effectiveness
4. **Monitor logs** for any connection failures or anomalies
5. **Test configurations** before relying on them for sensitive activities

### Traffic Analysis Resistance

The application implements several techniques to resist traffic analysis:
- **Packet padding** to constant sizes
- **Timing randomization** to break patterns
- **Dummy traffic** generation
- **Multiple obfuscation layers**

### DNS Leak Prevention

- **DNS-over-HTTPS** encrypts all DNS queries
- **Automatic DNS configuration** prevents leaks
- **Kill switch** blocks traffic if DNS fails
- **Multiple DoH providers** for redundancy

## 📊 Monitoring and Logs

### Real-time Status
The application provides real-time status information:
- Connection status for each component
- Traffic statistics
- Error reporting
- Performance metrics

### Log Analysis
Monitor logs for:
- Connection establishment/failures
- DNS resolution issues
- Firewall rule changes
- Performance degradation

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt pytest black flake8

# Run tests
pytest

# Code formatting
black .

# Linting
flake8
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Legal Disclaimer

This software is provided for educational and research purposes. Users are responsible for ensuring compliance with all applicable laws and regulations in their jurisdiction. The authors do not condone or support any illegal activities.

## 🆘 Support

### Getting Help

1. **Check the documentation** - Most issues are covered here
2. **Search existing issues** on GitHub
3. **Create a new issue** with detailed information
4. **Join our community** for discussions and support

### Reporting Bugs

When reporting bugs, please include:
- Operating system and version
- Python version
- Complete error messages
- Steps to reproduce
- Configuration details (remove sensitive information)

### Feature Requests

We welcome feature requests! Please:
- Check existing requests first
- Provide detailed use cases
- Explain the benefits
- Consider contributing the implementation

## 📚 Additional Resources

### Related Documentation
- [WireGuard Documentation](https://www.wireguard.com/)
- [Tor Project](https://www.torproject.org/)
- [Shadowsocks Documentation](https://shadowsocks.org/)
- [obfs4 Specification](https://github.com/Yawning/obfs4)

### Security Research
- [Traffic Analysis Resistance](https://blog.torproject.org/traffic-analysis-resistance)
- [Domain Fronting](https://www.bamsoftware.com/papers/fronting/)
- [Pluggable Transports](https://trac.torproject.org/projects/tor/wiki/doc/PluggableTransports)

---

**⚡ Built for privacy advocates, researchers, and security professionals**

*Stay safe, stay private, stay anonymous.*
