import subprocess
import json

def get_earthworm_status():
    try:
        # Inisialisasi dictionary untuk menyimpan data
        data = {
            'system': {},
            'rings': {},
            'module': {}
        }

        # Jalankan perintah 'status'
        result = subprocess.run(["status"], capture_output=True, text=True, check=True)
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
                        data['module'][module_name]['cpu_used'] = float(parts[2])
                        data['module'][module_name]['memory_used'] = float(parts[3])
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

# Jalankan fungsi
data = get_earthworm_status()
print(data)
