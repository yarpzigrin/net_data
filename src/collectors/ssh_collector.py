import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import yaml
from dotenv import load_dotenv
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

load_dotenv()

# Загружаем команды из файла
COMMANDS_FILE = Path("commands.yaml")

if not COMMANDS_FILE.exists():
    raise FileNotFoundError(f"Файл команд не найден: {COMMANDS_FILE}")

with open(COMMANDS_FILE, "r") as f:
    commands_config = yaml.safe_load(f)

STATIC_COMMANDS = [cmd["command"] for cmd in commands_config.get("static_commands", [])]
DYNAMIC_COMMANDS = [cmd["command"] for cmd in commands_config.get("dynamic_commands", [])]

def sanitize_filename(s: str) -> str:
    return "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in s)

def save_raw_output(identifier: str, command: str, output: str, command_type: str = "static"):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    slug = sanitize_filename(command.replace(" ", "_"))
    path = Path("data/raw") / command_type / f"{identifier}_{timestamp}_{slug}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(output, encoding="utf-8")
    print(f"Сохранён raw: {path}")

def collect_raw(device: Dict, command_type: str = "static") -> Dict[str, str]:
    identifier = device.get("ip")
    vendor = device["vendor"]

    commands = STATIC_COMMANDS if command_type == "static" else DYNAMIC_COMMANDS

    conn_params = {
        "device_type": "cisco_ios",
        "host": device["ip"],
        "username": os.getenv("SSH_USERNAME"),
        "password": os.getenv("SSH_PASSWORD"),
        "global_cmd_verify": False,
        "global_delay_factor": 2,
        "session_log": f"data/logs/ssh_{device['ip']}.log",
        "session_log_record_writes": True,
        "session_log_file_mode": "write",
        "allow_auto_change": True,
        "conn_timeout": 15,
        "secret": "",  # пустой secret — netmiko НЕ будет требовать пароль для enable
    }

    raw_data = {}

    try:
        with ConnectHandler(**conn_params) as conn:
            print(f"Подключено к {identifier} ({vendor})")

            # Пытаемся войти в enable без пароля (просто команда enable + Enter)
            try:
                conn.send_command_timing("enable", delay_factor=2)
                print(f"Вошли в enable mode на {identifier} (без ввода пароля)")
            except Exception as e:
                print(f"Enable не удался на {identifier}: {e}")
                print("Продолжаем в текущем режиме — некоторые команды могут не отработать")

            # Отключаем paging (terminal length 0)
            conn.send_command("terminal length 0", expect_string=r"[>#]")

            # Проверяем текущий промпт
            prompt = conn.find_prompt()
            print(f"Текущий промпт: {prompt}")

            for cmd in commands:
                print(f"Выполняю: {cmd}")
                try:
                    output = conn.send_command(cmd, expect_string=r'[>#]')
                    raw_data[cmd] = output.strip()
                    save_raw_output(identifier, cmd, output, command_type)
                except Exception as e:
                    print(f"Ошибка выполнения {cmd} на {identifier}: {e}")
                    raw_data[cmd] = f"ERROR: {e}"

    except NetmikoTimeoutException:
        print(f"Timeout подключения к {identifier}")
        return {}
    except NetmikoAuthenticationException:
        print(f"Ошибка аутентификации {identifier}")
        return {}
    except Exception as e:
        print(f"Ошибка на {identifier}: {e}")
        return {}

    return raw_data