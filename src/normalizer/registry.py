registry = {}  # {"vendor_entity": func}
def register(vendor: str, entity: str, func):
    key = f"{vendor}_{entity}"
    registry[key] = func
def get_normalizer(vendor: str, entity: str):
    key = f"{vendor}_{entity}"
    return registry.get(key)