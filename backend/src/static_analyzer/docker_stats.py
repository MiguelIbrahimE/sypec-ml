# backend/src/static_analyzer/docker_stats.py
import os
from typing import Dict

def estimate_docker_usage(repo_path: str) -> Dict[str, float]:
    dockerfile_path = os.path.join(repo_path, "Dockerfile")
    if not os.path.isfile(dockerfile_path):
        return {"estimated_ram_mb": 256, "estimated_disk_mb": 100}

    ram = 256
    disk = 100

    try:
        with open(dockerfile_path, "r") as f:
            lines = f.readlines()
            for line in lines:
                if "apt-get install" in line or "RUN" in line:
                    disk += 50
                if "python" in line or "pip install" in line:
                    ram += 128
    except Exception:
        pass

    return {"estimated_ram_mb": ram, "estimated_disk_mb": disk}
