import winrm
from datetime import datetime
from pathlib import Path
import os

def collect_dhcp_raw(server_ip: str) -> tuple[str, str]:
    """
    Собирает сырые leases и reservations со ВСЕХ scope.
    Возвращает (leases_text, reservations_text) — просто текст PowerShell.
    """
    print(f"[DHCP] Подключаемся к {server_ip}")

    try:
        session = winrm.Session(
            f"http://{server_ip}:5985/wsman",
            auth=(os.getenv("WINRM_USERNAME"), os.getenv("WINRM_PASSWORD")),
            transport="ntlm",
            server_cert_validation='ignore'
        )
        print("[DHCP] WinRM-сессия создана")

    except Exception as e:
        print(f"[DHCP] Не удалось подключиться: {e}")
        return "", ""

    # Leases
    try:
        leases_cmd = r"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Get-DhcpServerv4Scope | ForEach-Object {
    Get-DhcpServerv4Lease -ScopeId $_.ScopeId -AllLeases |
        Select-Object IPAddress, ClientId, HostName, AddressState, LeaseExpiryTime
}
"""
        result = session.run_ps(leases_cmd)
        leases_text = result.std_out.decode('utf-8', errors='replace')
        print(f"[DHCP] Leases строк: {len(leases_text.splitlines())}")
    except Exception as e:
        print(f"[DHCP] Ошибка leases: {e}")
        leases_text = ""

    # Reservations
    try:
        reservations_cmd = r"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Get-DhcpServerv4Scope | ForEach-Object {
    Get-DhcpServerv4Reservation -ScopeId $_.ScopeId |
        Select-Object IPAddress, ClientId, Name, Description, Type
}
"""
        result = session.run_ps(reservations_cmd)
        reservations_text = result.std_out.decode('utf-8', errors='replace')
        print(f"[DHCP] Reservations строк: {len(reservations_text.splitlines())}")
    except Exception as e:
        print(f"[DHCP] Ошибка reservations: {e}")
        reservations_text = ""

    return leases_text, reservations_text


def save_dhcp_raw(leases_text: str, reservations_text: str, server_ip: str):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = Path("data/raw/dhcp")
    output_dir.mkdir(parents=True, exist_ok=True)

    leases_path = output_dir / f"{server_ip}_{timestamp}_leases.txt"
    reservations_path = output_dir / f"{server_ip}_{timestamp}_reservations.txt"

    with open(leases_path, "w", encoding="utf-8") as f:
        f.write(leases_text)

    with open(reservations_path, "w", encoding="utf-8") as f:
        f.write(reservations_text)

    print(f"[✓] Сохранено leases: {leases_path}")
    print(f"[✓] Сохранено reservations: {reservations_path}")