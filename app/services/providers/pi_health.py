import shutil
from typing import Any, Dict

from app.services.providers.base import DataProvider


class PiHealthProvider(DataProvider):
    """Reads Pi system health from /proc, /sys, and shutil."""

    @property
    def name(self) -> str:
        return "pi_health"

    @staticmethod
    def _read_cpu_percent() -> float:
        """Read CPU usage from /proc/stat (delta between two snapshots)."""
        import time

        def read_cpu_times():
            with open("/proc/stat") as f:
                parts = f.readline().split()
            # user, nice, system, idle, iowait, irq, softirq, steal
            times = list(map(int, parts[1:9]))
            idle = times[3] + times[4]
            total = sum(times)
            return idle, total

        idle1, total1 = read_cpu_times()
        time.sleep(0.1)
        idle2, total2 = read_cpu_times()

        idle_delta = idle2 - idle1
        total_delta = total2 - total1
        if total_delta == 0:
            return 0.0
        return round((1.0 - idle_delta / total_delta) * 100, 1)

    @staticmethod
    def _read_memory_percent() -> float:
        """Read memory usage from /proc/meminfo."""
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                key = parts[0].rstrip(":")
                info[key] = int(parts[1])
        total = info.get("MemTotal", 1)
        available = info.get("MemAvailable", 0)
        used_pct = (1.0 - available / total) * 100
        return round(used_pct, 1)

    @staticmethod
    def _read_temp() -> int:
        """Read CPU temperature from thermal zone."""
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                return round(int(f.read().strip()) / 1000)
        except (FileNotFoundError, ValueError):
            return 0

    @staticmethod
    def _read_disk_percent() -> int:
        """Read root filesystem usage."""
        usage = shutil.disk_usage("/")
        return round(usage.used / usage.total * 100)

    @staticmethod
    def _read_uptime() -> str:
        """Read uptime from /proc/uptime and format as '14d 7h'."""
        with open("/proc/uptime") as f:
            seconds = float(f.read().split()[0])
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        if days > 0:
            return f"{days}d {hours}h"
        if hours > 0:
            return f"{hours}h"
        mins = int((seconds % 3600) // 60)
        return f"{mins}m"

    async def get_data(self) -> Dict[str, Any]:
        return {
            "systems": {
                "pi": {
                    "cpu_pct": self._read_cpu_percent(),
                    "memory_pct": self._read_memory_percent(),
                    "temp": self._read_temp(),
                    "disk_pct": self._read_disk_percent(),
                    "uptime": self._read_uptime(),
                },
            },
        }
