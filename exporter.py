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
            if "Process  Process" in line:
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
                        data['module'][module_name]['argument'] = ' '.join(parts[5:])
                    modules.append(module_name)

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
