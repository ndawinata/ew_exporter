#!/bin/bash

# Configure these settings at the beginning so they can run on all systems.
# ##############################################################
# Base directories
INSTALL_DIR="/opt/ew_exporter"
LOG_DIR="/opt/ew_exporter/log"
VENV_DIR="${INSTALL_DIR}/venv"
EW_LINUX_BASH_PATH="/opt/earthworm/run_working/ew_linux.bash"

### ##############################################################


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



log "Starting Earthworm Exporter installation..."

# Create directories
log "Creating directories..."
mkdir -p ${INSTALL_DIR}
mkdir -p ${LOG_DIR}

# Install required packages
log "Installing required packages..."
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y python3 python3-venv python3-pip
elif command -v yum &> /dev/null; then
    yum install -y python3 python3-pip
fi

# Create and activate virtual environment
log "Setting up Python virtual environment..."
python3 -m venv ${VENV_DIR}

# Upgrade pip
log "Upgrading pip..."
${VENV_DIR}/bin/python3 -m pip install --upgrade pip

# Install Python packages in venv
log "Installing Python packages..."
${VENV_DIR}/bin/pip install -r requirements.txt

# Copy files
log "Copying files..."
cp main.py ${INSTALL_DIR}/
cp config.cfg ${INSTALL_DIR}/

# Create wrapper script
log "Creating wrapper script..."
cat > ${INSTALL_DIR}/start.sh << EOF
#!/bin/bash
source ${EW_LINUX_BASH_PATH}
exec ${VENV_DIR}/bin/python3 ${INSTALL_DIR}/main.py
EOF
chmod +x ${INSTALL_DIR}/start.sh

# Create service file
log "Creating service file..."
cat > /etc/systemd/system/ew_exporter.service << EOF
[Unit]
Description=Earthworm Exporter Service
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=${INSTALL_DIR}
Environment=PYTHONUNBUFFERED=1
Environment=PATH=${VENV_DIR}/bin:$PATH
ExecStart=${INSTALL_DIR}/start.sh
Restart=always
RestartSec=10

# Hardening
ProtectSystem=full
ProtectHome=true
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
log "Setting permissions..."
chown -R root:root ${INSTALL_DIR}
chmod 755 ${INSTALL_DIR}
chmod 644 ${INSTALL_DIR}/config.cfg
chmod 755 ${INSTALL_DIR}/main.py
chmod 644 /etc/systemd/system/ew_exporter.service

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