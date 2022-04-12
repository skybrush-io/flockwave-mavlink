"""MAVLink CRC-16/MCRF4XX code

Copyright Andrew Tridgell
Released under GNU LGPL version 3 or later

Modernized for Python 3.x by Tamas Nepusz
"""

from array import array
from typing import Any, Iterable, Optional, Union

__all__ = ("X25CRCCalculator",)


class X25CRCCalculator:
    """CRC-16/MCRF4XX - based on checksum.h from mavlink library"""

    crc: int

    def __init__(self, buf: Optional[Union[bytes, str]] = None):
        self.crc = 0xFFFF
        if buf is not None:
            if isinstance(buf, str):
                self.accumulate_str(buf)
            else:
                self.accumulate(buf)

    def accumulate(self, buf: Iterable[int]) -> None:
        """add in some more bytes"""
        accum = self.crc
        for b in buf:
            tmp = b ^ (accum & 0xFF)
            tmp = (tmp ^ (tmp << 4)) & 0xFF
            accum = (accum >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)
        self.crc = accum

    def accumulate_str(self, buf: Any) -> None:
        """add in some more bytes"""
        bytes_array = array("B")
        try:  # if buf is bytes
            bytes_array.frombytes(buf)
        except TypeError:  # if buf is str
            bytes_array.frombytes(buf.encode())
        self.accumulate(bytes_array)
