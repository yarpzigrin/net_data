from typing import Iterable

def load_parsers(extra_modules: Iterable[str] | None = None) -> None:
    """
    Импортирует парсеры для регистрации в registry.
    Расширяемость: можно передать дополнительные модули с парсерами.
    """
    modules = [
        "src.parsers.nateks",
        "src.parsers.rvi",
    ]
    if extra_modules:
        modules.extend(extra_modules)

    for module in modules:
        __import__(module)
