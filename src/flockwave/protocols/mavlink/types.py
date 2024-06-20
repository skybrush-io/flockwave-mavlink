from __future__ import annotations

from struct import Struct
from typing import Any, Callable, Dict, List, Optional, Protocol, Sequence, Tuple, Union


class MAVLinkHeader(Protocol):
    """Interface specification for the `MAVLink_header` classes that are to be
    found in each of the dialect modules.
    """

    mlen: int
    seq: int
    srcSystem: int
    srcComponent: int
    msgId: int
    incompat_flags: int
    compat_flags: int

    def __init__(
        self,
        msgId: int,
        incompat_flags: int = 0,
        compat_flags: int = 0,
        mlen: int = 0,
        seq: int = 0,
        srcSystem: int = 0,
        srcComponent: int = 0,
    ) -> None: ...

    def pack(self, force_mavlink1: bool = False) -> bytes: ...


class MAVLinkMessage(Protocol):
    """Interface specification for the `MAVLink_message` classes that are to be
    found in each of the dialect modules.
    """

    id: int
    msgname: str
    fieldnames: List[str]
    ordered_fieldnames: List[str]
    fieldtypes: List[str]
    fielddisplays_by_name: Dict[str, str]
    fieldenums_by_name: Dict[str, str]
    fieldunits_by_name: Dict[str, str]
    native_format: bytearray
    orders: List[int]
    lengths: List[int]
    array_lengths: List[int]
    crc_extra: int = 0
    unpacker: Struct
    instance_field: Optional[str]
    instance_offset: int

    def __init__(self, msgId: int, name: str) -> None: ...
    def get_msgbuf(self) -> bytearray: ...
    def get_header(self) -> MAVLinkHeader: ...
    def get_payload(self) -> Optional[bytes]: ...
    def get_crc(self) -> Optional[int]: ...
    def get_fieldnames(self) -> List[str]: ...
    def get_type(self) -> str: ...
    def get_msgId(self) -> int: ...
    def get_srcSystem(self) -> int: ...
    def get_srcComponent(self) -> int: ...
    def get_seq(self) -> int: ...
    def get_signed(self) -> bool: ...
    def get_link_id(self) -> Optional[int]: ...
    def pack(self, mav: "MAVLinkInterface", force_mavlink1: bool = False) -> bytes: ...
    def sign_packet(self, mav: "MAVLinkInterface") -> None: ...
    def to_dict(self) -> Dict[str, Union[str, float, int]]: ...
    def to_json(self) -> str: ...

    def __getitem__(self, key: str) -> str: ...
    def __str__(self) -> str: ...
    def __ne__(self, other: object) -> bool: ...
    def __eq__(self, other: object) -> bool: ...


class MAVLinkSigningInterface(Protocol):
    """Interface specification for the `MAVLinkSigning` instances to be found
    on `MAVLink` instances in the `signing` attribute.
    """

    secret_key: Optional[bytes]
    timestamp: int
    link_id: int
    sign_outgoing: bool
    allow_unsigned_callback: Optional[Callable[[MAVLinkInterface, int], bool]]
    stream_timestamps: Dict[Tuple[int, int, int], int]
    sig_count: int
    badsig_count: int
    goodsig_count: int
    unsigned_count: int
    reject_count: int


class MAVLinkInterface(Protocol):
    """Interface specification for the `MAVLink` classes that are to be found
    in each of the dialect modules.

    This interface lists only the common and publicly available members of the
    MAVLink classes. Dialect-specific functions are not included. The interface
    is not meant to be exhaustive as it is unclear which members of the class
    are meant to be public and which members are meant to be private.
    """

    seq: int
    srcSystem: int
    srcComponent: int
    robust_parsing: bool
    total_packets_sent: int
    total_bytes_sent: int
    total_packets_received: int
    total_bytes_received: int
    total_receive_errors: int
    startup_time: float
    signing: MAVLinkSigningInterface

    def __init__(
        self,
        file: Any,
        srcSystem: int = 0,
        srcComponent: int = 0,
    ): ...

    def set_callback(
        self, callback: Callable[..., None], *args: Any, **kwargs: Any
    ) -> None: ...
    def set_send_callback(
        self, callback: Callable[..., None], *args: Any, **kwargs: Any
    ) -> None: ...

    def send(self, mavmsg: MAVLinkMessage, force_mavlink1: bool = False) -> None: ...

    def buf_len(self) -> int: ...
    def bytes_needed(self) -> int: ...

    def parse_char(self, c: Sequence[int]) -> Optional[MAVLinkMessage]: ...
    def parse_buffer(self, s: Sequence[int]) -> Optional[List[MAVLinkMessage]]: ...

    def check_signature(
        self, msgbuf: bytearray, srcSystem: int, srcComponent: int
    ) -> bool: ...

    def decode(self, msgbuf: bytearray) -> MAVLinkMessage: ...


MAVLinkFactory = Callable[[], MAVLinkInterface]
"""Type specification for factory objects that create MAVLinkInterface_ instances."""
