#!/usr/bin/env python3
"""Generates the code for this Python module based on a current or a given
version of ``pymavlink``.
"""

from argparse import ArgumentParser, Namespace
from collections import defaultdict
from contextlib import contextmanager, ExitStack
from functools import partial
from pathlib import Path
from subprocess import PIPE, Popen, run
from shutil import move, rmtree
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import DefaultDict, Dict, Iterator, List, Optional
from venv import create as create_virtualenv

import sys


def create_parser() -> ArgumentParser:
    """Creates a command line argument parser for the entry point of the script."""
    default_output = str((Path.cwd() / __file__).parent.parent / "src")
    parser = ArgumentParser()
    parser.add_argument(
        "-w",
        "--work-dir",
        help="directory to use as a working folder. Defaults to a temporary folder.",
    )
    parser.add_argument(
        "--format",
        default=False,
        action="store_true",
        help="format the generated code with black",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="name of the root of the source tree to extend with the generated files",
        default=default_output,
    )
    return parser


@contextmanager
def create_work_dir(path: Optional[str] = None) -> Iterator[Path]:
    if path is None:
        with TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    else:
        result = Path(path)
        if result.is_dir():
            rmtree(result)
        result.mkdir(parents=True, exist_ok=True)
        yield result


def call_python(*args: str, in_venv: Optional[Path] = None) -> bytes:
    """Calls Python programmatically with a list of arguments."""
    py = sys.executable if in_venv is None else str(in_venv / "bin" / "python")
    return run([py] + list(args), check=True, stdout=PIPE).stdout


def call_pip(*args: str, in_venv: Optional[Path] = None) -> None:
    """Calls pip programmatically with a list of arguments."""
    call_python("-m", "pip", *args, in_venv=in_venv)


def find_dialects_in_venv(venv: Path) -> Dict[str, List[str]]:
    """Finds all the MAVLink dialects in a ``pymavlink`` installation within the
    given virtualenv.
    """
    py = partial(call_python, in_venv=venv)

    result: DefaultDict[str, List[str]] = defaultdict(list)

    for dialect_version in ("v10", "v20"):
        pkg = f"pymavlink.dialects.{dialect_version}"
        lines = py(
            "-c",
            "from importlib.resources import contents; "
            + f"print('\\n'.join(contents('{pkg}')))",
        )
        for line in lines.split(b"\n"):
            if (
                line.endswith(b".py")
                and b"__init__" not in line
                and not line.endswith(b"test.py")
            ):
                result[dialect_version].append(line.decode("ascii")[:-3])
    return dict(result)


def get_pymavlink_version_in_venv(venv: Path) -> str:
    """Returns the version of ``pymavlink`` installed within the given
    virtualenv.
    """
    return (
        call_python(
            "-c", "import pymavlink; print(pymavlink.__version__)", in_venv=venv
        )
        .decode("utf-8")
        .strip()
    )


def read_dialect(dialect: str, version: str, *, in_venv: Path) -> bytes:
    py = partial(call_python, in_venv=in_venv)
    pkg = f"pymavlink.dialects.{version}"
    return py(
        "-c",
        "from importlib.resources import read_binary; import sys; "
        + f"sys.stdout.buffer.write(read_binary('{pkg}', '{dialect}.py'))",
    )


def _patch_dialect_code(code: bytes) -> bytes:
    result: List[bytes] = []
    for line in code.strip().split(b"\n"):
        if line.startswith(b"native_supported ="):
            line = b"native_supported = False"
        elif line.startswith(b"from pymavlink.generator.mavcrc import x25crc"):
            line = b"from flockwave.protocols.mavlink.utils import X25CRCCalculator as x25crc"
        result.append(line)
    return b"\n".join(result) + b"\n"


def process_dialect_code(code: bytes, *, format: bool = False) -> bytes:
    code = _patch_dialect_code(code)
    if format:
        proc = Popen(
            [
                sys.executable,
                "-m",
                "black.__main__",
                "-q",
                "-t",
                "py37",
                "-",
            ],
            stdin=PIPE,
            stdout=PIPE,
            stderr=None,
        )
        formatted_code = proc.communicate(code, timeout=60)[0]
        if proc.returncode:
            raise RuntimeError(f"black exited with return code {proc.returncode}")
    else:
        formatted_code = code
    return formatted_code


def process_options(options: Namespace) -> int:
    """Processes the command line options and executes the main functionality
    of the script.
    """
    from rich.console import Console  # type: ignore
    from rich.progress import track  # type: ignore

    console = Console()
    with ExitStack() as stack:
        work_dir = stack.enter_context(create_work_dir(options.work_dir))
        venv_dir = work_dir / "venv"
        output_dir = work_dir / "output"

        pip = partial(call_pip, in_venv=venv_dir)

        with console.status("Creating virtualenv..."):
            create_virtualenv(venv_dir, clear=True, symlinks=True, with_pip=True)
        console.log(f"Created virtualenv in [b]{venv_dir}[/b]")

        packages = ["pip", "wheel", "pymavlink"]
        for package in packages:
            with console.status(f"Installing {package}..."):
                pip("install", "-q", "-U", package)

        console.log(f"Dependencies installed in [b]{venv_dir}[/b]")

        pymavlink_version = get_pymavlink_version_in_venv(venv_dir)
        console.log(f"PyMAVLink is at version [b]{pymavlink_version}[/b]")

        dialects_by_version = find_dialects_in_venv(venv_dir)
        for dialect_version in sorted(dialects_by_version):
            dialect_output_dir = output_dir / "dialects" / dialect_version
            dialect_output_dir.mkdir(parents=True, exist_ok=True)
            (dialect_output_dir / "__init__.py").write_text(
                dedent(
                    f"""\
                # Auto-generated MAVLink {dialect_version} dialect files from PyMAVLink {pymavlink_version}
                # Do not modify.
            """
                )
            )

            for dialect in track(
                dialects_by_version[dialect_version],
                description=f"Copying {dialect_version} dialects...",
            ):
                code = read_dialect(dialect, version=dialect_version, in_venv=venv_dir)
                formatted_code = process_dialect_code(code, format=options.format)
                (dialect_output_dir / f"{dialect}.py").write_bytes(formatted_code)

        (output_dir / "dialects" / "__init__.py").write_text(
            dedent(
                f"""\
                # Auto-generated MAVLink dialect files from PyMAVLink {pymavlink_version}
                # Do not modify.

                pymavlink_version = {pymavlink_version!r}
            """
            )
        )

        final_dir = Path(options.output) / "flockwave" / "protocols" / "mavlink"

        with console.status("Moving generated files to output folder..."):
            final_dir.mkdir(parents=True, exist_ok=True)
            for output_subdir in output_dir.glob("*"):
                if (final_dir / output_subdir.name).exists():
                    rmtree(final_dir / output_subdir.name)
                move(output_subdir, final_dir)

        console.log(f"Output generated in [b]{final_dir}[/b]")

    return 0


def main() -> int:
    parser = create_parser()
    options = parser.parse_args()
    return process_options(options)


if __name__ == "__main__":
    sys.exit(main())
