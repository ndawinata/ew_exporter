import json
import time
from fastapi import FastAPI, Response, HTTPException, status
from prometheus_client import (
    Gauge, 
    generate_latest, 
    CONTENT_TYPE_LATEST,
    CollectorRegistry
)
import subprocess
import configparser
import logging
import os
import uvicorn
from typing import Dict, Any

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
        logging.StreamHandler()
    ]
)

# Create FastAPI app
app = FastAPI(
    title="Earthworm Exporter",
    description="Prometheus exporter for Earthworm seismic processing system",
    version="1.0.0"
)

# Create a custom registry
registry = CollectorRegistry()

# Metrics Definitions
disk_space = Gauge(
    "ew_disk_space_bytes", 
    "Earthworm Available disk space in bytes",
    registry=registry
)
pid = Gauge(
    "ew_module_pid", 
    "Earthworm Module PID", 
    ["module"],
    registry=registry
)
module_status = Gauge(
    "ew_module_status", 
    "Earthworm Module status (3=Not Exec, 2=Zombie, 1=Alive, 0=Dead)", 
    ["module"],
    registry=registry
)
module_cpu_usage = Gauge(
    "ew_module_cpu_usage", 
    "Earthworm Module CPU usage (%)", 
    ["module"],
    registry=registry
)
module_memory_usage_total = Gauge(
    "ew_module_memory_usage_total", 
    "Earthworm Module Memory Usage (Total Memory) (%)", 
    ["module"],
    registry=registry
)
module_memory_usage_allocated = Gauge(
    "ew_module_memory_usage_allocated", 
    "Earthworm Module Memory Usage (Allocated Memory) (%)", 
    ["module"],
    registry=registry
)
module_vsz = Gauge(
    "ew_module_virtual_memory", 
    "Earthworm Module Virtual memory size (vsz) in kb", 
    ["module"],
    registry=registry
)
module_rss = Gauge(
    "ew_module_resident_memory", 
    "Earthworm Module Resident set size (rss) in kb", 
    ["module"],
    registry=registry
)

def get_earthworm_status() -> Dict[str, Any]:
    try:
        data = {
            'system': {},
            'rings': {},
            'module': {}
        }

        # Run status command with full path
        result = subprocess.run(
            ["status"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        output = result.stdout

        # Parse system information
        for line in output.split("\n"):
            line = line.strip()
            
            if "Hostname-OS:" in line:
                data['system']['hostname_os'] = line.split(':', 1)[1].strip()
            elif "Start time (UTC):" in line:
                data['system']['start_time'] = line.split(':', 1)[1].strip()
            elif "Current time (UTC):" in line:
                data['system']['current_time'] = line.split(':', 1)[1].strip()
            elif "Disk space avail:" in line:
                data['system']['disk_space'] = int(line.split(':', 1)[1].strip().split()[0])
            elif "Ring" in line and "name/key/size:" in line:
                parts = line.split(':', 1)[1].strip().split('/')
                ring_num = line.split()[1]
                data['rings'][ring_num] = {
                    'name': parts[0].strip(),
                    'key': parts[1].strip(),
                    'size': int(parts[2].strip().split()[0])
                }
            elif "Startstop Version:" in line:
                data['system']['version'] = line.split(':', 1)[1].strip()

        # Parse module status
        modules = []
        process_section = False
        for line in output.split("\n"):
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

        # print(modules)

        # Get detailed process info
        paths = '|'.join(modules)
        cmd = f'ps aux | grep -E "{paths}" | grep -v grep'
        result1 = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        output1 = result1.stdout

        for line in output1.split("\n"):
            if line.strip():
                parts = line.split(maxsplit=10)
                if len(parts) >= 11:
                    command = parts[10]
                    module_name = next((name for name in modules if name in command), None)
                    
                    if module_name:
                        data['module'][module_name].update({
                            'pid': int(parts[1]),
                            'cpu_used': round(float(parts[2]), 2),
                            'memory_used': round(float(parts[3]), 2),
                            'vsz': int(parts[4]),
                            'rss': int(parts[5]),
                            'tty': parts[6],
                            'stat': parts[7],
                            'start': parts[8],
                            'time': parts[9],
                            'command': command
                        })

        return data

    except subprocess.CalledProcessError as e:
        logging.error(f"Error running status command: {e}")
        return None
    except Exception as e:
        logging.error(f"Error: {e}")
        return None

def get_process_info() -> Dict[str, str]:
    try:
        # Run status command
        result = subprocess.run(
            ["status"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        processes = {}
        process_section = False
        
        # Parse output line by line
        for line in result.stdout.split("\n"):
            # Detect start of process section
            if "Process  Process" in line or "Name" in line or "-------" in line:
                process_section = True
                continue
            
            # Parse process lines
            if process_section and line.strip():
                parts = line.split()
                if len(parts) >= 3:  # Minimal: name, id, status
                    process_name = parts[0]
                    process_id = parts[1]
                    processes[process_name] = process_id
        
        return processes

    except subprocess.CalledProcessError as e:
        logging.error(f"Error running status command: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error parsing status output: {e}")
        return {}

def update_metrics() -> None:
    data = get_earthworm_status()
    if data is None:
        logging.error("Failed to get Earthworm status")
        return

    try:
        disk_space.set(data["system"]["disk_space"])

        for module_name, module_data in data["module"].items():
            
            if module_data.get("status") is not None:
                status_value = {
                    "Not Exec": 4,
                    "Zombie": 3,
                    "Dead": 2,
                    "Stop": 1,
                    "Alive": 0
                }.get(module_data["status"])
                module_status.labels(module=module_name).set(status_value)
            else:
                # 0 = Status Error
                module_status.labels(module=module_name).set(5)

            allocated_memory = 0
            if module_data.get("rss") is not None and module_data.get("vsz") is not None:
                allocated_memory = (module_data["rss"]/module_data["vsz"])*100
            
            pid.labels(module=module_name).set(module_data["pid"] if module_data.get("pid") else 0)
            module_cpu_usage.labels(module=module_name).set(module_data["cpu_used"] if module_data.get("cpu_used") else 0)
            module_memory_usage_allocated.labels(module=module_name).set(round(allocated_memory, 2))
            module_memory_usage_total.labels(module=module_name).set(module_data["memory_used"] if module_data.get("memory_used") else 0)
            module_vsz.labels(module=module_name).set(module_data["vsz"] if module_data.get("vsz") else 0)
            module_rss.labels(module=module_name).set(module_data["rss"] if module_data.get("rss") else 0)
    except Exception as e:
        logging.error(f"Error updating metrics: {e}")

@app.get("/")
async def root():
    return {
        "name": "Earthworm Exporter",
        "version": "1.0.0",
        "description": "Prometheus exporter for Earthworm seismic processing system",
        "endpoints": {
            "metrics": "/metrics",
            "restart module": "/restart/pid",
            "stop module": "/stop/pid"
        }
    }

@app.get("/metrics")
async def metrics():
    update_metrics()
    return Response(
        generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/restart/{module_name}")
async def restart_module(module_name: str):
    try:
        # Get process info
        pid = get_process_info().get(module_name)
        if pid is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module '{module_name}' not found"
            )

        # Try to restart
        try:
            subprocess.run(["restart", str(pid)], check=True)
            return {
                "success": True,
                "message": f"Successfully restarted module '{module_name}' (PID: {pid})"
            }
        except subprocess.CalledProcessError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to restart module '{module_name}': {str(e)}"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@app.get("/stop/{module_name}")
async def stop_module(module_name: str):
    try:
        # Get process info
        pid = get_process_info().get(module_name)
        if pid is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module '{module_name}' not found"
            )

        # Try to stop
        try:
            subprocess.run(["stopmodule", str(pid)], check=True)
            return {
                "success": True,
                "message": f"Successfully stopped module '{module_name}' (PID: {pid})"
            }
        except subprocess.CalledProcessError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to stop module '{module_name}': {str(e)}"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

if __name__ == "__main__":
    host = config.get('server', 'host', fallback='localhost')
    port = config.getint('server', 'port', fallback=9877)
    
    # Start uvicorn server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )