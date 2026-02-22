from importlib import import_module
from types import ModuleType
from typing import Type

from .types import MAVLinkMessage

__all__ = ("import_dialect", "get_mavlink_message_class")

dialect_pkg = (__package__ or "flockwave.protocols.mavlink") + ".dialects.v20."


def import_dialect(dialect: str) -> ModuleType:
    """Imports the module representing the given MAVLink dialect.

    Args:
        dialect: the dialect to import

    Returns:
        the module representing the given MAVLink dialect

    Raises:
        ImportError: if the given dialect is not known to this module
    """
    pkg_name = dialect_pkg + dialect
    return import_module(pkg_name)


def get_mavlink_message_class(dialect: str, type: str) -> Type[MAVLinkMessage]:
    """Returns the class representing the MAVLink message of the given type in the
    given dialect.

    Args:
        dialect: the dialect to query
        type: the message type to retrieve. Case insensitive.
    """
    dialect_module = import_dialect(dialect)
    type = type.lower()
    return getattr(dialect_module, f"MAVLink_{type}_message")
