from typing import List, Optional, Tuple, Union

__all__ = ("x25crc", "X25CRCCalculator")

# CRC calculation using fastcrc, falling back to a pure Python implementation
# if fastcrc is not available
try:
    import fastcrc

    mcrf4xx = fastcrc.crc16.mcrf4xx
except Exception:
    mcrf4xx = None


BytesLike = Union[List[int], Tuple[int, ...], bytes, bytearray, str]


class _x25crc_slow(object):
    """CRC-16/MCRF4XX - based on checksum.h from mavlink library"""

    crc: int

    def __init__(self, buf: Optional[BytesLike] = None):
        self.crc = 0xFFFF
        if buf is not None:
            self.accumulate(buf)

    def accumulate(self, buf: BytesLike) -> None:
        """add in some more bytes (it also accepts strings)"""
        if isinstance(buf, str):
            buf = buf.encode()

        accum = self.crc
        for b in buf:
            tmp = b ^ (accum & 0xFF)
            tmp = (tmp ^ (tmp << 4)) & 0xFF
            accum = (accum >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)
        self.crc = accum


class _x25crc_fast(object):
    """CRC-16/MCRF4XX - based on checksum.h from mavlink library"""

    def __init__(self, buf: Optional[BytesLike] = None):
        self.crc = 0xFFFF
        if buf is not None:
            self.accumulate(buf)

    def accumulate(self, buf: BytesLike) -> None:
        """add in some more bytes (it also accepts strings)"""
        if isinstance(buf, str):
            buf_as_bytes = bytes(buf.encode())
        elif isinstance(buf, (list, tuple, bytearray)):
            buf_as_bytes = bytes(buf)
        else:
            buf_as_bytes = buf
        self.crc = mcrf4xx(buf_as_bytes, self.crc)  # ty:ignore[call-non-callable]


x25crc = _x25crc_fast if mcrf4xx is not None else _x25crc_slow
X25CRCCalculator = x25crc  # deprecated alias
