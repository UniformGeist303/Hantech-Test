#!/usr/bin/env python3
"""Generate a Flipper Zero IR file for Hantech/JHS A018-12KR2 AC units.

The source captures are raw Flipper signals.  This script decodes them as a
56-bit, 7-byte, MSB-first protocol, validates the observed checksum, derives
average timings from the captures, and appends a small set of generated test
states.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


BIT_THRESHOLD_US = 1000
DEFAULT_SOURCE = Path(r"C:\Users\elena\Desktop\AC.ir")
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "ACs"
    / "Hantech"
    / "Hantech_A018-12KR2A.ir"
)


@dataclass
class Signal:
    name: str
    kind: str
    frequency: int
    duty_cycle: str
    data: list[int]


@dataclass
class Timings:
    header_mark: int
    header_space: int
    bit_mark: int
    zero_space: int
    one_space: int
    end_mark: int


def parse_flipper_ir(path: Path) -> list[Signal]:
    signals: list[Signal] = []
    current: dict[str, str] = {}

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(("Filetype:", "Version:")):
            continue
        if ": " not in line:
            continue

        key, value = line.split(": ", 1)
        if key == "name" and current:
            signals.append(signal_from_fields(current))
            current = {}
        current[key] = value

    if current:
        signals.append(signal_from_fields(current))

    return signals


def signal_from_fields(fields: dict[str, str]) -> Signal:
    return Signal(
        name=fields["name"],
        kind=fields["type"],
        frequency=int(fields["frequency"]),
        duty_cycle=fields["duty_cycle"],
        data=[int(part) for part in fields["data"].split()],
    )


def decode_bytes(signal: Signal) -> list[int]:
    if signal.kind != "raw":
        raise ValueError(f"{signal.name}: only raw signals are supported")
    if len(signal.data) != 115:
        raise ValueError(f"{signal.name}: expected 115 timing values, got {len(signal.data)}")

    bits: list[int] = []
    pulse_pairs = signal.data[2:-1]
    for index in range(0, len(pulse_pairs), 2):
        space = pulse_pairs[index + 1]
        bits.append(1 if space > BIT_THRESHOLD_US else 0)

    if len(bits) != 56:
        raise ValueError(f"{signal.name}: expected 56 bits, got {len(bits)}")

    decoded: list[int] = []
    for index in range(0, len(bits), 8):
        value = 0
        for bit in bits[index : index + 8]:
            value = (value << 1) | bit
        decoded.append(value)
    return decoded


def checksum(byte1: int, byte2: int, byte3: int) -> int:
    return (0x100 - ((byte1 + byte2 + byte3) & 0xFF)) & 0xFF


def packet(byte1: int, byte2: int, byte3: int) -> list[int]:
    return [0x18, byte1, byte2, byte3, 0x00, 0x00, checksum(byte1, byte2, byte3)]


def derive_timings(signals: list[Signal]) -> Timings:
    header_marks: list[int] = []
    header_spaces: list[int] = []
    bit_marks: list[int] = []
    zero_spaces: list[int] = []
    one_spaces: list[int] = []
    end_marks: list[int] = []

    for signal in signals:
        header_marks.append(signal.data[0])
        header_spaces.append(signal.data[1])
        end_marks.append(signal.data[-1])
        for index in range(2, len(signal.data) - 1, 2):
            bit_marks.append(signal.data[index])
            space = signal.data[index + 1]
            if space > BIT_THRESHOLD_US:
                one_spaces.append(space)
            else:
                zero_spaces.append(space)

    return Timings(
        header_mark=round(mean(header_marks)),
        header_space=round(mean(header_spaces)),
        bit_mark=round(mean(bit_marks)),
        zero_space=round(mean(zero_spaces)),
        one_space=round(mean(one_spaces)),
        end_mark=round(mean(end_marks)),
    )


def encode_raw(bytes_: list[int], timings: Timings) -> list[int]:
    raw = [timings.header_mark, timings.header_space]
    for byte in bytes_:
        for bit_index in range(7, -1, -1):
            bit = (byte >> bit_index) & 1
            raw.append(timings.bit_mark)
            raw.append(timings.one_space if bit else timings.zero_space)
    raw.append(timings.end_mark)
    return raw


def write_signal(lines: list[str], name: str, frequency: int, duty_cycle: str, data: list[int]) -> None:
    lines.extend(
        [
            "# ",
            f"name: {name}",
            "type: raw",
            f"frequency: {frequency}",
            f"duty_cycle: {duty_cycle}",
            "data: " + " ".join(str(value) for value in data),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    source_signals = parse_flipper_ir(args.source)
    if not source_signals:
        raise SystemExit("No IR signals found")

    frequency = source_signals[0].frequency
    duty_cycle = source_signals[0].duty_cycle
    timings = derive_timings(source_signals)

    original_names = {
        "Power": "Power_Original",
        "16": "Cool_16C_Original",
        "Winkel_an": "Swing_On_Original",
        "Lufer2": "Fan_2_Original",
    }

    generated = {
        "Cool_16C_Fan1_SwingOff_Generated": packet(0xA1, 0x01, 0x10),
        "Cool_17C_Fan1_SwingOff_Generated": packet(0xA1, 0x01, 0x11),
        "Cool_20C_Fan1_SwingOff_Generated": packet(0xA1, 0x01, 0x14),
        "Cool_20C_Fan2_SwingOff_Generated": packet(0xA1, 0x02, 0x14),
        "Cool_20C_Fan2_SwingOn_Generated": packet(0xA1, 0x22, 0x14),
    }

    lines = [
        "Filetype: IR signals file",
        "Version: 1",
        "# Hantech/JHS A018-12KR2A mobile AC",
        "# First four signals are original working Flipper captures.",
        "# Generated entries are protocol hypotheses for POCO F5 / IR Blaster Remote tests.",
        f"# Derived timings: header {timings.header_mark} {timings.header_space}, bit {timings.bit_mark}, zero {timings.zero_space}, one {timings.one_space}, end {timings.end_mark}",
    ]

    print("Decoded source signals:")
    for signal in source_signals:
        decoded = decode_bytes(signal)
        expected = checksum(decoded[1], decoded[2], decoded[3])
        status = "OK" if expected == decoded[6] else "FAIL"
        print(f"- {signal.name}: {' '.join(f'{value:02X}' for value in decoded)} checksum={status}")
        write_signal(
            lines,
            original_names.get(signal.name, f"{signal.name}_Original"),
            signal.frequency,
            signal.duty_cycle,
            signal.data,
        )

    print(
        "Derived timings:",
        timings.header_mark,
        timings.header_space,
        timings.bit_mark,
        timings.zero_space,
        timings.one_space,
        timings.end_mark,
    )

    for name, bytes_ in generated.items():
        print(f"- {name}: {' '.join(f'{value:02X}' for value in bytes_)}")
        write_signal(lines, name, frequency, duty_cycle, encode_raw(bytes_, timings))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
