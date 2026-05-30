# Hantech / JHS A018-12KR2A IR remote

Flipper Zero IR file for a Hantech 12000 BTU mobile air conditioner with model
`A018-12KR2/A`. The file is intended for Flipper Zero and Android apps that can
import Flipper `.ir` files from a GitHub repository, such as IR Blaster Remote.

## Files

- `ACs/Hantech/Hantech_A018-12KR2A.ir` - importable Flipper IR file
- `ACs/Hantech/Hantech_A018-12KR2A_android_test.ir` - Android test variant with explicit trailing spaces
- `tools/generate_hantech_a018.py` - parser, decoder, checksum validator, and generator

## Verified captures

The first four buttons in the generated `.ir` file are unchanged raw captures
from the original remote and have already worked through Flipper Zero:

| Button in output | Source name | Decoded bytes | Checksum |
| --- | --- | --- | --- |
| `Power_Original` | `Power` | `18 81 01 10 00 00 6E` | OK |
| `Cool_16C_Original` | `16` | `18 A1 01 10 00 00 4E` | OK |
| `Swing_On_Original` | `Winkel_an` | `18 81 21 10 00 00 4E` | OK |
| `Fan_2_Original` | `Lufer2` | `18 91 22 10 00 00 3D` | OK |

All captures use:

- `type: raw`
- `frequency: 38000`
- `duty_cycle: 0.330000`

## Protocol notes

The signal decodes as 56 bits / 7 bytes, MSB-first within each byte:

- Header: about `8807 4380`
- Bit mark: about `544`
- Bit `0` space: about `549`
- Bit `1` space: about `1655`
- End mark: about `584`

Checksum:

```text
checksum = (0x100 - ((byte1 + byte2 + byte3) & 0xFF)) & 0xFF
```

Here `byte1`, `byte2`, and `byte3` mean the second, third, and fourth bytes of
the full packet, excluding the leading fixed `0x18`.

## Generated test states

These entries are generated hypotheses and should be tested carefully before
expanding the library:

- `Cool_16C_Fan1_SwingOff_Generated` -> `18 A1 01 10 00 00 4E`
- `Cool_17C_Fan1_SwingOff_Generated` -> `18 A1 01 11 00 00 4D`
- `Cool_20C_Fan1_SwingOff_Generated` -> `18 A1 01 14 00 00 4A`
- `Cool_20C_Fan2_SwingOff_Generated` -> `18 A1 02 14 00 00 49`
- `Cool_20C_Fan2_SwingOn_Generated` -> `18 A1 22 14 00 00 29`

The original `Fan_2_Original` capture decodes as `0x22` in the flags byte, so it
may represent fan 2 plus swing on if swing was already active.

## Regenerate

From this directory:

```powershell
python .\tools\generate_hantech_a018.py --source C:\Users\elena\Desktop\AC.ir
```

The output is written to:

```text
ACs/Hantech/Hantech_A018-12KR2A.ir
ACs/Hantech/Hantech_A018-12KR2A_android_test.ir
```

## Android troubleshooting

If the unchanged Flipper captures work on Flipper Zero but not through Android,
first try `Hantech_A018-12KR2A_android_test.ir`. It contains the same signals,
but each raw pattern explicitly ends with a `45000` us space. This avoids relying
on an app importer to auto-pad Flipper raw signals that end with a final mark.

If that still does not work, capture the POCO F5 output with Flipper Zero:

1. On the Flipper, open `Infrared -> Learn New Remote`.
2. Point the POCO F5 IR emitter at the Flipper receiver.
3. Press `Power_Original` in IR Blaster Remote.
4. Save the learned signal and compare it with the original `Power` capture.

That tells us whether the phone/app is transmitting the same pattern, a distorted
pattern, or no IR signal at all.
