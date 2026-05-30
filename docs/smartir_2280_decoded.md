# SmartIR 2280 decoded

Decoded from `smartir_2280.json` Broadlink Base64 codes.

- Protocol: Hantech/JHS 56-bit raw
- Bit order: MSB-first per byte
- All decoded checksums: OK
- SmartIR modes: `cool`, `dry`, `fan_only`, `off`
- Not present in SmartIR: night/sleep, timer, C/F toggle

| Bytes | Count | SmartIR paths |
| --- | ---: | --- |
| `18 A1 24 10 00 00 2B` | 1 | `cool/high/16` |
| `18 A1 24 11 00 00 2A` | 1 | `cool/high/17` |
| `18 A1 24 12 00 00 29` | 1 | `cool/high/18` |
| `18 A1 24 13 00 00 28` | 1 | `cool/high/19` |
| `18 A1 24 14 00 00 27` | 1 | `cool/high/20` |
| `18 A1 24 15 00 00 26` | 1 | `cool/high/21` |
| `18 A1 24 16 00 00 25` | 1 | `cool/high/22` |
| `18 A1 24 17 00 00 24` | 1 | `cool/high/23` |
| `18 A1 24 18 00 00 23` | 1 | `cool/high/24` |
| `18 A1 24 19 00 00 22` | 1 | `cool/high/25` |
| `18 A1 21 10 00 00 2E` | 1 | `cool/low/16` |
| `18 A1 21 11 00 00 2D` | 1 | `cool/low/17` |
| `18 A1 21 12 00 00 2C` | 1 | `cool/low/18` |
| `18 A1 21 13 00 00 2B` | 1 | `cool/low/19` |
| `18 A1 21 14 00 00 2A` | 1 | `cool/low/20` |
| `18 A1 21 15 00 00 29` | 1 | `cool/low/21` |
| `18 A1 21 16 00 00 28` | 1 | `cool/low/22` |
| `18 A1 21 17 00 00 27` | 1 | `cool/low/23` |
| `18 A1 21 18 00 00 26` | 1 | `cool/low/24` |
| `18 A1 21 19 00 00 25` | 1 | `cool/low/25` |
| `18 A1 22 10 00 00 2D` | 1 | `cool/mid/16` |
| `18 A1 22 11 00 00 2C` | 1 | `cool/mid/17` |
| `18 A1 22 12 00 00 2B` | 1 | `cool/mid/18` |
| `18 A1 22 13 00 00 2A` | 1 | `cool/mid/19` |
| `18 A1 22 14 00 00 29` | 1 | `cool/mid/20` |
| `18 A1 22 15 00 00 28` | 1 | `cool/mid/21` |
| `18 A1 22 16 00 00 27` | 1 | `cool/mid/22` |
| `18 A1 22 17 00 00 26` | 1 | `cool/mid/23` |
| `18 A1 22 18 00 00 25` | 1 | `cool/mid/24` |
| `18 A1 22 19 00 00 24` | 1 | `cool/mid/25` |
| `18 82 21 19 00 00 44` | 30 | `dry/low/16, dry/low/17, dry/low/18, dry/low/19, dry/low/20, dry/low/21, dry/low/22, dry/low/23, dry/low/24, dry/low/25, dry/mid/16, dry/mid/17, ...` |
| `18 94 24 19 00 00 2F` | 10 | `fan_only/high/16, fan_only/high/17, fan_only/high/18, fan_only/high/19, fan_only/high/20, fan_only/high/21, fan_only/high/22, fan_only/high/23, fan_only/high/24, fan_only/high/25` |
| `18 84 21 19 00 00 42` | 10 | `fan_only/low/16, fan_only/low/17, fan_only/low/18, fan_only/low/19, fan_only/low/20, fan_only/low/21, fan_only/low/22, fan_only/low/23, fan_only/low/24, fan_only/low/25` |
| `18 94 22 19 00 00 31` | 10 | `fan_only/mid/16, fan_only/mid/17, fan_only/mid/18, fan_only/mid/19, fan_only/mid/20, fan_only/mid/21, fan_only/mid/22, fan_only/mid/23, fan_only/mid/24, fan_only/mid/25` |
| `18 01 01 16 00 00 E8` | 1 | `off` |
