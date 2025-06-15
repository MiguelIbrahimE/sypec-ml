import os
import logging

logger = logging.getLogger(__name__)

def estimate_test_coverage(repo_path: str) -> dict:
    test_files = 0
    total_py = 0

    for root, _, files in os.walk(repo_path):
        for f in files:
            if f.endswith(".py"):
                total_py += 1
                if "test" in f.lower():
                    test_files += 1

    percent = (test_files / total_py * 100) if total_py else 0
    logger.debug(f"Estimated test coverage: {percent:.2f}%")
    return {
        "test_files": test_files,
        "total_py": total_py,
        "coverage_percent": round(percent, 1)
    }
