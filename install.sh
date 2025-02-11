#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    error "Please run as root"
    exit 1
fi

# Base directories
INSTALL_DIR="/opt/earthworm/run_working/ew_exporter"
LOG_DIR="/opt/earthworm/run_working/log"
VENV_DIR="${INSTALL_DIR}/venv"

log "Starting Earthworm Exporter installation..."

# Create directories
log "Creating directories..."
mkdir -p ${INSTALL_DIR}
mkdir -p ${LOG_DIR}

# Install required packages
log "Installing required packages..."
apt-get update
apt-get install -y python3 python3-venv python3-pip

# Create and activate virtual environment
log "Setting up Python virtual environment..."
python3 -m venv ${VENV_DIR}
source ${VENV_DIR}/bin/activate

# Install Python packages
log "Installing Python packages..."
pip install prometheus_client configparser

# Copy files
log "Copying files..."
cp exporter.py ${INSTALL_DIR}/
cp config.cfg ${INSTALL_DIR}/
cp ew_exporter.service /etc/systemd/system/

# Set permissions
log "Setting permissions..."
chown -R root:root ${INSTALL_DIR}
chmod 755 ${INSTALL_DIR}
chmod 644 ${INSTALL_DIR}/config.cfg
chmod 755 ${INSTALL_DIR}/exporter.py

# Update service file to use virtual environment
log "Updating service file..."
sed -i "s|ExecStart=/usr/bin/python3|ExecStart=${VENV_DIR}/bin/python3|" /etc/systemd/system/ew_exporter.service

# Reload systemd and enable service
log "Configuring systemd service..."
systemctl daemon-reload
systemctl enable ew_exporter
systemctl start ew_exporter

# Check service status
if systemctl is-active --quiet ew_exporter; then
    log "Earthworm Exporter service is running"
    log "Installation completed successfully!"
    log "You can check the service status with: systemctl status ew_exporter"
    log "View logs with: journalctl -u ew_exporter -f"
    log "Metrics available at: http://localhost:9877/metrics"
else
    error "Service failed to start. Please check logs with: journalctl -u ew_exporter -f"
    exit 1
fi

# Deactivate virtual environment
deactivate