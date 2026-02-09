from typing import Callable, Dict

parser_registry: Dict[str, Callable] = {}

def register_parser(vendor: str, command_slug: str, parser_func: Callable):
    key = f"{vendor}_{command_slug}"
    parser_registry[key] = parser_func

def get_parser(vendor: str, command_slug: str) -> Callable | None:
    key = f"{vendor}_{command_slug}"
    return parser_registry.get(key)
