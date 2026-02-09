from pathlib import Path
import yaml

def load_port_filters() -> dict:
    path = Path("config/port_filters.yaml")
    if not path.exists():
        print("port_filters.yaml не найден — фильтр отключён")
        return {"global": {"ignore_patterns": [], "ignore_ports": []}, "devices": {}}

    with open(path, "r") as f:
        config = yaml.safe_load(f)

    return config.get("filters", {})

def is_ignored_port(device_ip: str, port: str) -> bool:
    if not port:
        return False

    filters = load_port_filters()

    # Глобальные паттерны (tg, te, xe...)
    global_patterns = filters.get("global", {}).get("ignore_patterns", [])
    for pattern in global_patterns:
        if pattern.lower() in port.lower():
            print(f"[FILTER] Игнорируем порт {port} по глобальному паттерну {pattern}")
            return True

    # Глобальные конкретные порты
    global_ignore = filters.get("global", {}).get("ignore_ports", [])
    if port in global_ignore:
        print(f"[FILTER] Игнорируем порт {port} по глобальному списку")
        return True

    # Конкретное устройство (по IP)
    device_filters = filters.get("devices", {}).get(device_ip, {})
    if device_filters:
        ignore_ports = device_filters.get("ignore_ports", [])
        if port in ignore_ports:
            print(f"[FILTER] Игнорируем порт {port} для устройства {device_ip}")
            return True

    # Fallback "*"
    fallback = filters.get("devices", {}).get("*", {})
    if fallback:
        ignore_ports = fallback.get("ignore_ports", [])
        if port in ignore_ports:
            print(f"[FILTER] Игнорируем порт {port} по fallback")
            return True

    return False