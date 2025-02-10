import subprocess
import json

def get_earthworm_status():
    try:
        # Jalankan perintah 'status'
        result = subprocess.run(["status"], capture_output=True, text=True, check=True)
        output = result.stdout

        

        # Parse status modul
        modul = []
        status_dict = {}
        for line in output.split("\n"):
            if "Alive" in line:
                parts = line.split()
                status_dict[parts[0]] = "Alive"
                modul.append(parts[0])
            elif "Dead" in line:
                parts = line.split()
                status_dict[parts[0]] = "Dead"
                modul.append(parts[0])
        
        print(modul)


        # print(status_dict)

        cmd = 'ps aux | grep -E "import_generic|tpd_pick|tcpd|startstop" | grep -v grep'
        result1 = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        processes = []
        for line in result1.stdout.strip().split("\n"):
            parts = line.split(maxsplit=10)  # Memisahkan berdasarkan spasi
            
            if len(parts) < 11:
                continue  # Skip jika tidak sesuai format
            
            process_info = {
                "user": parts[0],      # Pemilik proses
                "pid": int(parts[1]),  # Process ID
                "cpu": float(parts[2]), # Penggunaan CPU
                "mem": float(parts[3]), # Penggunaan Memori
                "vsz": int(parts[4]),  # Virtual Memory Size
                "rss": int(parts[5]),  # Resident Set Size
                "tty": parts[6],       # Terminal terkait
                "stat": parts[7],      # Status proses (Running, Sleeping, dll.)
                "start": parts[8],     # Waktu proses dimulai
                "time": parts[9],      # Total CPU Time digunakan
                "command": parts[10]   # Perintah yang dieksekusi
            }
            
            processes.append(process_info)
        
        json_output = json.dumps(processes, indent=4)
        # print(json_output)

    except subprocess.CalledProcessError as e:
        print("Error menjalankan perintah status:", e)

# Jalankan fungsi
get_earthworm_status()
