from easysnmp import Session
import json

# Параметры SNMP
HOST = "10.66.10.1"
COMMUNITY = "public"          # ← замени на реальный RO community, если не public
VERSION = 2                   # 1, 2c или 3

session = Session(
    hostname=HOST,
    community=COMMUNITY,
    version=VERSION,
    timeout=2, retries=2
)

# OID для ARP-таблицы (ipNetToMediaTable)
# 1.3.6.1.2.1.4.22.1.2 = ipNetToMediaPhysAddress (IP → MAC)
# 1.3.6.1.2.1.4.22.1.1 = ipNetToMediaNetAddress (IP)
# 1.3.6.1.2.1.4.22.1.4 = ipNetToMediaType (1=other, 2=dynamic, 3=static, 4=invalid)

print("Собираем ARP-таблицу по SNMP...")

try:
    arp_table = session.walk([
        "1.3.6.1.2.1.4.22.1.1",  # ipNetToMediaNetAddress (IP)
        "1.3.6.1.2.1.4.22.1.2",  # ipNetToMediaPhysAddress (MAC)
        "1.3.6.1.2.1.4.22.1.4"   # ipNetToMediaType
    ])

    hosts = []

    # walk возвращает list of Varbind
    for i in range(0, len(arp_table), 3):
        ip_var = arp_table[i]
        mac_var = arp_table[i+1]
        type_var = arp_table[i+2]

        if ip_var.oid_index == mac_var.oid_index == type_var.oid_index:
            ip = ip_var.value
            mac_raw = mac_var.value.hex() if hasattr(mac_var.value, 'hex') else mac_var.value
            mac = ':'.join(mac_raw[j:j+2] for j in range(0, len(mac_raw), 2)).lower()
            arp_type = int(type_var.value) if type_var.value.isdigit() else type_var.value

            hosts.append({
                "ip": ip,
                "mac": mac,
                "arp_type": arp_type,  # 2=dynamic, 3=static и т.д.
                "source": "snmp"
            })

    print(f"Найдено ARP-записей: {len(hosts)}")

    # Выводим первые 5 для примера
    print(json.dumps(hosts[:5], indent=2, ensure_ascii=False))

    # Сохраняем полный результат
    with open("data/snmp_arp_test.json", "w", encoding="utf-8") as f:
        json.dump({
            "snapshot": {
                "type": "snmp_arp_test",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "device_ip": HOST
            },
            "hosts": hosts
        }, f, ensure_ascii=False, indent=2)

    print("Сохранено в data/snmp_arp_test.json")

except Exception as e:
    print(f"Ошибка SNMP: {e}")