# Earthworm Exporter

Earthworm Exporter adalah Prometheus exporter untuk memonitor status dan metrik dari Earthworm Seismic System. Exporter ini mengumpulkan informasi tentang status modul, penggunaan sumber daya, dan metrik sistem lainnya dari instalasi Earthworm.

## Fitur

- Monitoring status modul Earthworm (Alive, Dead, Zombie, Not Exec)
- Metrik penggunaan CPU dan memori per modul
- Informasi penggunaan disk sistem
- Metrik VSZ (Virtual Memory Size) dan RSS (Resident Set Size) per modul
- Auto-discovery modul Earthworm yang berjalan

## Persyaratan

- Python 3.6+
- Earthworm Seismic System yang terinstall
- Akses ke command `status` Earthworm
- Hak akses root/sudo untuk instalasi

## Instalasi

1. Clone repository atau download source code:

```bash
git clone git@github.com:ndawinata/ew_exporter.git
cd ew_exporter
```

2. Konfigurasi sebelum instalasi:
   - Edit `config.cfg` sesuai kebutuhan
   - Pastikan environment Earthworm sudah terkonfigurasi dengan benar

3. Jalankan script instalasi:

```bash
sudo ./install.sh
```

## Konfigurasi

Konfigurasi utama tersedia di file `config.cfg`:

```ini
[server]
# Host untuk binding exporter (default: localhost)
host = 0.0.0.0
# Port untuk endpoint metrics (default: 9877)
port = 9877

[logging]
# Direktori log
log_dir = /opt/ew_exporter/log
# Level log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
log_level = INFO
```

## Metrics

| Metric Name | Type | Description | Labels |
|------------|------|-------------|---------|
| system_info | Info | Informasi sistem Earthworm | hostname, version |
| system_disk_space_bytes | Gauge | Ruang disk yang tersedia dalam bytes | - |
| module_status | Gauge | Status modul (3=Not Exec, 2=Zombie, 1=Alive, 0=Dead) | module |
| module_cpu_usage | Gauge | Penggunaan CPU per modul (%) | module |
| module_memory_usage | Gauge | Penggunaan memori per modul (%) | module |
| module_virtual_memory | Gauge | Virtual memory size (VSZ) | module |
| module_resident_memory | Gauge | Resident set size (RSS) | module |

## Endpoint

Metrics tersedia di endpoint `/metrics`:
```
http://localhost:9877/metrics
```

## Contoh Output Metrics

```
# HELP system_info Information about the system
# TYPE system_info gauge
system_info{hostname="SEEW1 - Linux 5.14.0",version="v7.10 2019-06-13"} 1

# HELP module_status Module status (3=Not Exec, 2=Zombie, 1=Alive, 0=Dead)
# TYPE module_status gauge
module_status{module="startstop"} 1
module_status{module="import_generic"} 1
module_status{module="tpd_pick"} 1
module_status{module="tcpd"} 1

# HELP module_cpu_usage CPU usage per module (%)
# TYPE module_cpu_usage gauge
module_cpu_usage{module="startstop"} 0.0
module_cpu_usage{module="import_generic"} 3.4
```

## Grafana Dashboard

Tersedia template dashboard Grafana di direktori `dashboards/`. Dashboard ini mencakup:
- Overview status sistem
- Status dan metrik modul
- Penggunaan sumber daya
- Historis status modul

## Troubleshooting

### Service Tidak Berjalan
```bash
# Cek status service
sudo systemctl status ew_exporter

# Cek logs
sudo journalctl -u ew_exporter -f
```

### Metrics Tidak Tersedia
1. Pastikan port tidak digunakan oleh aplikasi lain
2. Verifikasi hak akses ke command Earthworm
3. Cek file log di `/opt/ew_exporter/log/ew_exporter.log`

## Development

Untuk berkontribusi:
1. Fork repository
2. Buat branch fitur
3. Commit perubahan
4. Buat pull request

## License

MIT License - lihat file [LICENSE](LICENSE) untuk detail lengkap.

## Kontak

Untuk pertanyaan dan dukungan, silakan buat issue di repository atau hubungi maintainer.

