import os
import logging

logger = logging.getLogger(__name__)

def detect_code_smells(repo_path: str) -> list[str]:
    smells = []

    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), "r", errors="ignore") as f:
                    lines = f.readlines()

                if any(len(line) > 120 for line in lines):
                    smells.append(f"{file} has very long lines.")
                if sum(1 for line in lines if line.strip().startswith("def ")) > 10:
                    smells.append(f"{file} has too many functions.")
                if "import *" in "".join(lines):
                    smells.append(f"{file} uses wildcard imports.")

    logger.debug(f"Code smells detected: {smells}")
    return smells
