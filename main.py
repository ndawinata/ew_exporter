import json
import time
from prometheus_client import start_http_server, Gauge, Info
import subprocess
import configparser
import logging
import os
# Load configuration
config = configparser.ConfigParser()
config.read('config.cfg')

# Setup logging
log_dir = config.get('logging', 'log_dir', fallback='/opt/ew_exporter/log')
log_level = config.get('logging', 'log_level', fallback='INFO')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/ew_exporter.log'),
        logging.StreamHandler()  # Also log to console
    ]
)


# Metrics Definitions
disk_space = Gauge("ew_disk_space_bytes", "Earthworm Available disk space in bytes")
pid = Gauge("ew_module_pid", "Earthworm Module PID", ["module"])
module_status = Gauge("ew_module_status", "Earthworm Module status (3=Not Exec, 2=Zombie, 1=Alive, 0=Dead)", ["module"])
module_cpu_usage = Gauge("ew_module_cpu_usage", "Earthworm Module CPU usage (%)", ["module"])
module_memory_usage = Gauge("ew_module_memory_usage", "Earthworm Module Memory usage (%)", ["module"])
module_vsz = Gauge("ew_module_virtual_memory", "Earthworm Module Virtual memory size (vsz) in kb", ["module"])
module_rss = Gauge("ew_module_resident_memory", "Earthworm Module Resident set size (rss) in kb", ["module"])


def get_earthworm_status():
    try:
        data = {
            'system': {},
            'rings': {},
            'module': {}
        }

        # Jalankan perintah 'status'
        result = subprocess.run(['status'], capture_output=True, text=True, check=True)
        output = result.stdout

        # Parse system information
        for line in output.split("\n"):
            line = line.strip()
            
            # Parse Hostname dan OS
            if "Hostname-OS:" in line:
                data['system']['hostname_os'] = line.split(':', 1)[1].strip()
            
            # Parse Start time
            elif "Start time (UTC):" in line:
                data['system']['start_time'] = line.split(':', 1)[1].strip()
            
            # Parse Current time
            elif "Current time (UTC):" in line:
                data['system']['current_time'] = line.split(':', 1)[1].strip()
            
            # Parse Disk space
            elif "Disk space avail:" in line:
                data['system']['disk_space'] = int(line.split(':', 1)[1].strip().split()[0])
            
            # Parse Ring information
            elif "Ring" in line and "name/key/size:" in line:
                parts = line.split(':', 1)[1].strip().split('/')
                ring_num = line.split()[1]  # Get ring number
                data['rings'][ring_num] = {
                    'name': parts[0].strip(),
                    'key': parts[1].strip(),
                    'size': int(parts[2].strip().split()[0])
                }
            
            # Parse Version
            elif "Startstop Version:" in line:
                data['system']['version'] = line.split(':', 1)[1].strip()

        # Parse module status
        modules = []
        process_section = False
        for line in output.split("\n"):
            # Skip header lines
            if "Process  Process" in line or "Name" in line or "-------" in line:
                process_section = True
                continue
            
            if process_section and line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    module_name = parts[0]
                    if module_name not in data['module']:
                        data['module'][module_name] = {
                            'status': None,
                            'pid': None,
                            'priority': None,
                            'cpu_used': None,
                            'argument': None
                        }
                    data['module'][module_name]['status'] = parts[2]
                    data['module'][module_name]['pid'] = parts[1]
                    if len(parts) >= 4:
                        data['module'][module_name]['priority'] = parts[3]
                    if len(parts) >= 5:
                        data['module'][module_name]['cpu_used'] = parts[4]
                    if len(parts) >= 6:
                        data['module'][module_name]['argument'] = parts[6]
                    modules.append(module_name)
        
        paths = '|'.join(modules)
        cmd = f'ps aux | grep -E "{paths}" | grep -v grep'
        result1 = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        output1 = result1.stdout

        for line in output1.split("\n"):
            line = line.strip()
            
            if line:
                parts = line.split(maxsplit=10)
                if len(parts) >= 11:
                    # Cari nama modul berdasarkan command path
                    command = parts[10]
                    module_name = None
                    for name in modules:
                        if name in command:
                            module_name = name
                            break

                    if module_name:
                        data['module'][module_name]['pid'] = int(parts[1])
                        data['module'][module_name]['cpu_used'] = round(float(parts[2]), 2)
                        data['module'][module_name]['memory_used'] = round(float(parts[3]), 2)
                        data['module'][module_name]['vsz'] = int(parts[4])
                        data['module'][module_name]['rss'] = int(parts[5])
                        data['module'][module_name]['tty'] = parts[6]
                        data['module'][module_name]['stat'] = parts[7]
                        data['module'][module_name]['start'] = parts[8]
                        data['module'][module_name]['time'] = parts[9]
                        data['module'][module_name]['command'] = command

        return data

    except subprocess.CalledProcessError as e:
        print(f"Error menjalankan perintah status: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def update_metrics():
    data = get_earthworm_status()

    disk_space.set(data["system"]["disk_space"])

    # Module Metrics
    for module_name, module_data in data["module"].items():
        status_value = None
        if module_data["status"] == "Zombie":
            status_value = 2
        if module_data["status"] == "Not Exec":
            status_value = 3
        if module_data["status"] == "Dead":
            status_value = 0
        if module_data["status"] == "Alive":
            status_value = 1
        pid.labels(module=module_name).set(module_data["pid"])
        module_status.labels(module=module_name).set(status_value)
        module_cpu_usage.labels(module=module_name).set(module_data["cpu_used"])
        module_memory_usage.labels(module=module_name).set(module_data["memory_used"])
        module_vsz.labels(module=module_name).set(module_data["vsz"])
        module_rss.labels(module=module_name).set(module_data["rss"])

def main():
    # Get server configuration
    host = config.get('server', 'host', fallback='localhost')
    port = config.getint('server', 'port', fallback=9877)

    # Start the server
    start_http_server(port, addr=host)
    logging.info(f"Earthworm exporter server started at http://{host}:{port}/metrics")
    
    
    # Update metrics every 15 seconds
    while True:
        try:
            update_metrics()
            time.sleep(15)
        except Exception as e:
            logging.error(f"Main loop error: {str(e)}")
            time.sleep(15)

if __name__ == "__main__":
    main()