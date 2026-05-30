#!/usr/bin/env python3
"""Decode SmartIR Hantech 2280 Broadlink codes into Hantech bytes and Flipper IR."""

from __future__ import annotations

import argparse
import base64
import json
from dataclasses import dataclass
from pathlib import Path


BROADLINK_TICK_US = 8192 / 269
DEFAULT_SOURCE = Path(__file__).resolve().parents[1] / "smartir_2280.json"
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "ACs"
    / "Hantech"
    / "Hantech_A018-12KR2A_smartir_2280.ir"
)
DEFAULT_DOC = Path(__file__).resolve().parents[1] / "docs" / "smartir_2280_decoded.md"
TRAILING_SPACE_US = 45000
HANTECH_HEADER_MARK_US = 8807
HANTECH_HEADER_SPACE_US = 4380
HANTECH_BIT_MARK_US = 544
HANTECH_ZERO_SPACE_US = 549
HANTECH_ONE_SPACE_US = 1655
HANTECH_END_MARK_US = 584
SWING_BYTES = (0x18, 0x81, 0x21, 0x10, 0x00, 0x00, 0x4E)


@dataclass(frozen=True)
class DecodedCommand:
    path: tuple[str, ...]
    durations: list[int]
    bytes_: tuple[int, ...]


def broadlink_base64_to_durations(code: str) -> list[int]:
    packet = base64.b64decode(code)
    if packet[:2] != b"\x26\x00":
        raise ValueError(f"Unsupported Broadlink packet header: {packet[:4].hex(' ')}")

    payload = packet[4:]
    if payload[-2:] == b"\x0d\x05":
        payload = payload[:-2]

    durations: list[int] = []
    index = 0
    while index < len(payload):
        value = payload[index]
        index += 1
        if value == 0:
            if index + 1 >= len(payload):
                break
            ticks = (payload[index] << 8) | payload[index + 1]
            index += 2
        else:
            ticks = value
        durations.append(round(ticks * BROADLINK_TICK_US))
    return durations


def decode_hantech_bytes(durations: list[int]) -> tuple[int, ...]:
    if len(durations) != 115:
        raise ValueError(f"Expected 115 durations, got {len(durations)}")

    bits: list[int] = []
    for index in range(2, 114, 2):
        bits.append(1 if durations[index + 1] > 1000 else 0)

    decoded: list[int] = []
    for index in range(0, 56, 8):
        value = 0
        for bit in bits[index : index + 8]:
            value = (value << 1) | bit
        decoded.append(value)
    return tuple(decoded)


def checksum(byte1: int, byte2: int, byte3: int) -> int:
    return (0x100 - ((byte1 + byte2 + byte3) & 0xFF)) & 0xFF


def hantech_bytes_to_durations(bytes_: tuple[int, ...]) -> list[int]:
    durations = [HANTECH_HEADER_MARK_US, HANTECH_HEADER_SPACE_US]
    for byte in bytes_:
        for bit_index in range(7, -1, -1):
            bit = (byte >> bit_index) & 1
            durations.append(HANTECH_BIT_MARK_US)
            durations.append(HANTECH_ONE_SPACE_US if bit else HANTECH_ZERO_SPACE_US)
    durations.append(HANTECH_END_MARK_US)
    return durations


def iter_leaves(value: object, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, dict):
        leaves: list[tuple[tuple[str, ...], str]] = []
        for key, child in value.items():
            leaves.extend(iter_leaves(child, path + (str(key),)))
        return leaves
    return []


def decode_commands(source: Path) -> list[DecodedCommand]:
    data = json.loads(source.read_text(encoding="utf-8"))
    commands: list[DecodedCommand] = []
    for path, code in iter_leaves(data["commands"]):
        durations = broadlink_base64_to_durations(code)
        bytes_ = decode_hantech_bytes(durations)
        expected = checksum(bytes_[1], bytes_[2], bytes_[3])
        if expected != bytes_[6]:
            raise ValueError(f"{'/'.join(path)} checksum mismatch: expected {expected:02X}")
        commands.append(DecodedCommand(path=path, durations=durations, bytes_=bytes_))
    return commands


def command_name(path: tuple[str, ...]) -> str:
    if path == ("off",):
        return "Off"
    mode, fan, temp = path
    fan_name = {"low": "Fan1", "mid": "Fan2", "high": "Fan3"}[fan]
    if mode == "cool":
        return f"Cool_{temp}_{fan_name}"
    if mode == "dry":
        return "Dry"
    if mode == "fan_only":
        fan_number = {"low": "1", "mid": "2", "high": "3"}[fan]
        return f"Fan_only{fan_number}"
    return "_".join(path)


def ordered_commands(commands: list[DecodedCommand]) -> list[tuple[str, DecodedCommand]]:
    by_path = {command.path: command for command in commands}

    ordered: list[tuple[str, DecodedCommand]] = [
        ("On", by_path[("cool", "high", "16")]),
        ("Off", by_path[("off",)]),
        (
            "Cool_16_Fan3_Swing",
            DecodedCommand(
                path=("manual", "cool_16_fan3_swing"),
                durations=hantech_bytes_to_durations(SWING_BYTES),
                bytes_=SWING_BYTES,
            ),
        ),
        ("Dry", by_path[("dry", "low", "16")]),
        ("Fan_only1", by_path[("fan_only", "low", "16")]),
        ("Fan_only2", by_path[("fan_only", "mid", "16")]),
        ("Fan_only3", by_path[("fan_only", "high", "16")]),
    ]

    for fan in ("low", "mid", "high"):
        for temp in range(16, 26):
            path = ("cool", fan, str(temp))
            name = command_name(path)
            ordered.append((name, by_path[path]))

    return ordered


def write_flipper_ir(commands: list[DecodedCommand], output: Path) -> None:
    seen_names: set[str] = set()
    lines = [
        "Filetype: IR signals file",
        "Version: 1",
        "# Hantech/JHS A018-12KR2A mobile air conditioner",
        "# Also sold/rebranded as Hantech A018-12KR2/A family devices.",
        "# Contains: On alias, Off, Cool 16-25C Fan 1-3, Dry, Fan only 1-3.",
        "# Cool_16_Fan3_Swing uses the same state with swing enabled.",
        "# Not included: Night/Sleep, Timer, C/F toggle.",
    ]

    for name, command in ordered_commands(commands):
        if name in seen_names:
            continue

        seen_names.add(name)
        lines.extend(
            [
                "# ",
                f"name: {name}",
                "type: raw",
                "frequency: 38000",
                "duty_cycle: 0.330000",
                "data: " + " ".join(str(value) for value in command.durations + [TRAILING_SPACE_US]),
            ]
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_doc(commands: list[DecodedCommand], output: Path) -> None:
    unique: dict[tuple[int, ...], list[str]] = {}
    for command in commands:
        unique.setdefault(command.bytes_, []).append("/".join(command.path))

    lines = [
        "# SmartIR 2280 decoded",
        "",
        "Decoded from `smartir_2280.json` Broadlink Base64 codes.",
        "",
        "- Protocol: Hantech/JHS 56-bit raw",
        "- Bit order: MSB-first per byte",
        "- All decoded checksums: OK",
        "- SmartIR modes: `cool`, `dry`, `fan_only`, `off`",
        "- Not present in SmartIR: night/sleep, timer, C/F toggle",
        "",
        "| Bytes | Count | SmartIR paths |",
        "| --- | ---: | --- |",
    ]

    for bytes_, paths in sorted(unique.items(), key=lambda item: item[1][0]):
        bytes_text = " ".join(f"{value:02X}" for value in bytes_)
        path_text = ", ".join(paths[:12])
        if len(paths) > 12:
            path_text += ", ..."
        lines.append(f"| `{bytes_text}` | {len(paths)} | `{path_text}` |")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    args = parser.parse_args()

    commands = decode_commands(args.source)
    write_flipper_ir(commands, args.output)
    write_doc(commands, args.doc)

    unique_count = len({command.bytes_ for command in commands})
    print(f"Decoded {len(commands)} SmartIR commands into {unique_count} unique packets")
    print(f"Wrote {args.output}")
    print(f"Wrote {args.doc}")


if __name__ == "__main__":
    main()
