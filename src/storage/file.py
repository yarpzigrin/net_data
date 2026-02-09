from typing import Dict
from pathlib import Path
from datetime import datetime
import json

def save_parsed(parsed_data: Dict, identifier: str, command_slug: str):
    """
    Сохраняет parsed-данные в правильную папку в зависимости от типа команды.
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")

    # Определяем тип данных и папку
    if command_slug in ["vlan", "interface_brief", "version", "ip_interface", "running_config"]:
        base_path = Path("data/parsed/static")
    elif command_slug in ["mac_address_table", "arp"]:
        base_path = Path("data/parsed/dynamic")
        subfolder = "macs" if command_slug == "mac_address_table" else "arps"
        base_path = base_path / subfolder
    else:
        base_path = Path("data/parsed/other")  # fallback для новых команд

    base_path.mkdir(parents=True, exist_ok=True)

    filename = base_path / f"{identifier}_{timestamp}_{command_slug}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=2)

    print(f"Сохранён parsed ({command_slug}): {filename}")
    
def save_snapshot(snapshot: Dict, identifier: str = None):
    """
    Сохраняет snapshot в JSON.
    Если identifier задан — используем его в имени файла.
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    device_part = f"_{identifier}" if identifier else ""
    filename = f"data/snapshots/static/{timestamp}{device_part}_static_snapshot.json"
    
    Path("data/snapshots/static").mkdir(parents=True, exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    
    print(f"Сохранён snapshot: {filename}")

# src/storage/file.py (добавляем в конец файла)
def save_dynamic_snapshot(snapshot: Dict, snapshot_type: str = "hosts"):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"data/snapshots/dynamic/{timestamp}_{snapshot_type}_snapshot.json"
    
    Path("data/snapshots/dynamic").mkdir(parents=True, exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    
    print(f"Сохранён dynamic snapshot: {filename}")
