<p align="center">
  <img src="https://raw.githubusercontent.com/ndawinata/ew_exporter/refs/heads/main/ew_text putih.png" width="300" height="300" style="border-radius: 50%;">
</p>


# Earthworm Exporter

Prometheus exporter for Earthworm seismic processing system metrics, written in Python.

## Overview

Earthworm Exporter is a Prometheus exporter that collects metrics from an Earthworm seismic processing system. It exposes various metrics about the system status, ring buffers, and module states for monitoring and alerting purposes.

## Installation

### Prerequisites

- Python 3.6 or later
- Earthworm 7.10 or later
- Root/sudo access
- Properly configured Earthworm environment

### Building and Running

1. Clone the repository:
```bash
git clone https://github.com/your-repo/ew_exporter.git
cd ew_exporter
```

2. Configure the exporter by editing `config.cfg`:
```ini
[server]
# Host to bind the exporter (default: localhost)
host = 0.0.0.0
port = 9877

[directories]
INSTALL_DIR = /opt/ew_exporter
LOG_DIR = /opt/ew_exporter/log
EW_LINUX_BASH_PATH = /opt/earthworm/run_working/ew_linux.bash

[logging]
# Log directory path
log_dir = /opt/ew_exporter/log
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
log_level = INFO
```

3. Run the installation script:
```bash
sudo ./install.sh
```

The installer will:
- Create necessary directories
- Set up Python virtual environment
- Install required dependencies
- Configure systemd service
- Start the exporter

### Verifying Installation

Check if the exporter is running:
```bash
sudo systemctl status ew_exporter
```

View logs:
```bash
sudo journalctl -u ew_exporter -f
```

## Configuration

### Exporter Configuration

The exporter can be configured using `config.cfg`:

```ini
[server]
# Host to bind the exporter (default: localhost)
host = 0.0.0.0
port = 9877

[directories]
INSTALL_DIR = /opt/ew_exporter
LOG_DIR = /opt/ew_exporter/log
EW_LINUX_BASH_PATH = /opt/earthworm/run_working/ew_linux.bash

[logging]
# Log directory path
log_dir = /opt/ew_exporter/log
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
log_level = INFO
```

### Systemd Service

The exporter runs as a systemd service with the following features:
- Automatic startup on boot
- Automatic restart on failure
- Process isolation
- Proper logging

## API Endpoints

The exporter provides the following HTTP endpoints:

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/` | GET | Basic information about the exporter |
| `/metrics` | GET | Prometheus metrics |
| `/restart/{module_name}` | GET | Restart a specific Earthworm module |
| `/stop/{module_name}` | GET | Stop a specific Earthworm module |

### Module Management Endpoints

#### Restart Module
```
GET /restart/{module_name}
```
Restarts the specified Earthworm module.

Response codes:
- 200: Module successfully restarted
- 404: Module not found
- 500: Failed to restart module

Example response (success):
```json
{
    "success": true,
    "message": "Successfully restarted module 'tpd_pick' (PID: 12345)"
}
```

#### Stop Module
```
GET /stop/{module_name}
```
Stops the specified Earthworm module.

Response codes:
- 200: Module successfully stopped
- 404: Module not found
- 500: Failed to stop module

## Metrics

The exporter exposes the following metrics at `/metrics`:

### System Metrics

| Metric | Description | Type |
|--------|-------------|------|
| `ew_disk_space_bytes` | Available disk space in bytes | Gauge |

### Module Metrics

| Metric | Description | Type | Labels |
|--------|-------------|------|--------|
| `ew_module_pid` | Earthworm Module PID | Gauge | module |
| `ew_module_status` | Module status (5=Status Error, 4=Not Exec, 3=Zombie, 2=Dead, 1=Stop, 0=Alive) | Gauge | module |
| `ew_module_cpu_usage` | CPU usage per module (%) | Gauge | module |
| `ew_module_memory_usage_total` | Total memory usage per module (%) | Gauge | module |
| `ew_module_memory_usage_allocated` | Allocated memory usage per module (%) | Gauge | module |
| `ew_module_virtual_memory` | Virtual memory size (vsz) in kb | Gauge | module |
| `ew_module_resident_memory` | Resident set size (rss) in kb | Gauge | module |

### Metric Details

#### Status Values
- 5: Status Error
- 4: Not Exec
- 3: Zombie
- 2: Dead
- 1: Stop
- 0: Alive

## Prometheus Configuration

Add the following to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'earthworm'
    static_configs:
      - targets: ['localhost:9877']
```

## Development

### Requirements

Development requirements are listed in `requirements.txt`:
```
prometheus_client
configparser
```

### Building from Source

1. Clone the repository
2. Install development dependencies
3. Make your changes
4. Test the changes
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **Exporter fails to start**
   - Check if Earthworm is properly configured
   - Verify PATH and environment variables
   - Check logs with `journalctl -u ew_exporter -f`

2. **No metrics available**
   - Verify the exporter is running
   - Check if the port is accessible
   - Ensure Earthworm status command is working

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

