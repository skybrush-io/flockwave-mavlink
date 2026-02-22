"""Benchmark for the MAVLink packet parser."""

import sys
from argparse import ArgumentParser, Namespace
from collections import defaultdict
from operator import itemgetter
from pickle import load
from time import monotonic_ns

from flockwave.protocols.mavlink.dialects.v20.ardupilotmega import MAVLink


def hex_to_bytes(input: str | None) -> bytes:
    """Converts a hexadecimal string to bytes."""
    if input is None:
        return b""
    else:
        return bytes.fromhex(input)


def create_parser() -> ArgumentParser:
    """Creates a command line argument parser for the entry point of the script."""
    parser = ArgumentParser()
    parser.add_argument(
        "input_file",
        help="path to the input file containing raw MAVLink messages to benchmark",
    )
    parser.add_argument(
        "-S",
        "--signing-key",
        help="use the given hexadecimal signing key to verify the packets",
        type=hex_to_bytes,
    )
    return parser


def process_options(options: Namespace) -> int:
    """Processes the command line options and runs the benchmark."""
    from rich.progress import track

    input_file = options.input_file

    with open(input_file, "rb") as f:
        data = load(f)

    # Okay, packets loaded, time to parse!
    link = MAVLink(None, srcSystem=1, srcComponent=1)
    link.robust_parsing = True

    # Configure signing key if provided
    if options.signing_key:
        link.signing.secret_key = options.signing_key
        print(f"Using signing key: {options.signing_key.hex()}")

    total_parsed = 0
    start_time = monotonic_ns()
    packets_by_types = defaultdict(int)
    for chunk in track(data, description="Parsing packets..."):
        packets = link.parse_buffer(chunk)
        if packets is not None:
            for packet in packets:
                packet_type = packet.get_type()
                if packet_type != "BAD_DATA" and not packet_type.startswith("UNKNOWN_"):
                    packets_by_types[packet.get_type()] += 1
        total_parsed += len(packets or ())
    end_time = monotonic_ns()

    duration_nsec = end_time - start_time
    duration = duration_nsec / 1_000_000_000  # Convert to seconds

    total_parsed_not_bad_data = sum(packets_by_types.values())
    print(f"Received {len(data)} UDP packets.")
    print(
        f"Parsed {total_parsed_not_bad_data} packets from {input_file} in {duration} seconds."
    )
    print(f"Packets per second: {total_parsed_not_bad_data / duration:.2f} pps.")

    for pkt_type, count in sorted(
        packets_by_types.items(), key=itemgetter(1), reverse=True
    ):
        print(pkt_type, count)

    return 0


def main() -> int:
    parser = create_parser()
    options = parser.parse_args()
    return process_options(options)


if __name__ == "__main__":
    sys.exit(main())
