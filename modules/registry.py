from types import ModuleType

from modules import fail2ban, network, ssh, system_update, timezone


BUILTIN_MODULES: tuple[ModuleType, ...] = (
    timezone,
    ssh,
    fail2ban,
    network,
    system_update,
)

# Add trusted local modules here. Modules run with the privileges of Hardenix.
CUSTOM_MODULES: tuple[ModuleType, ...] = ()


def get_modules() -> list[ModuleType]:
    modules = [*BUILTIN_MODULES, *CUSTOM_MODULES]
    names: set[str] = set()
    required = ("check_existence", "install", "configure", "backup", "status")
    for module in modules:
        name = getattr(module, "NAME", None)
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{module.__name__} must define a non-empty NAME")
        key = name.casefold()
        if key in names:
            raise ValueError(f"Duplicate module NAME: {name}")
        names.add(key)
        missing = [method for method in required if not callable(getattr(module, method, None))]
        if missing:
            raise ValueError(
                f"Module {name} is missing required functions: {', '.join(missing)}"
            )
        for attribute in (
            "VERSION",
            "DESCRIPTION",
            "SUPPORTED_DISTROS",
            "PACKAGES",
            "SERVICES",
        ):
            if not hasattr(module, attribute):
                raise ValueError(f"Module {name} must define {attribute}")
        if not isinstance(module.VERSION, str) or not module.VERSION.strip():
            raise ValueError(f"Module {name} must define a non-empty string VERSION")
        if not isinstance(module.DESCRIPTION, str) or not module.DESCRIPTION.strip():
            raise ValueError(f"Module {name} must define a non-empty string DESCRIPTION")
        for attribute in ("SUPPORTED_DISTROS", "PACKAGES", "SERVICES"):
            value = getattr(module, attribute)
            if not isinstance(value, (list, tuple)) or any(
                not isinstance(item, str) or not item.strip() for item in value
            ):
                raise ValueError(f"Module {name} must define {attribute} as a list of strings")
    return modules


def get_module(name: str) -> ModuleType | None:
    return next(
        (module for module in get_modules() if module.NAME.casefold() == name.casefold()),
        None,
    )
