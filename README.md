# LAZYPOS Transparency - Don't trust us. Check us.

Figures are read straight from the Solana blockchain and updated daily.

Last updated: 2026-11-25 22:57 UTC and 2026-11-25 16:57 CST (US Central). Supply slot 473921720.

| Metric | Tokens | Share |
| --- | ---: | --- |
| Current supply | 882,972,397.693392 | 100% of current supply |
| Burned | 117,027,602.306608 | 11.70% of original 1,000,000,000 |
| Jupiter locked | 497,727,538.652504 | 56.37% of current supply |
| Circulating estimate | 385,244,859.040888 | 43.63% of current supply |

Burned tokens are already removed from current supply (original supply minus `getTokenSupply`). Jupiter-locked tokens are still inside current supply. Circulating estimate = current supply − Jupiter locked. This is an estimate. Staking pools are not separately identified yet, so staked tokens are still included. Liquidity-pool balances are still included too.

Original supply used for the burn figure: 1,000,000,000 tokens. On-chain decimals: 6.

## Jupiter Lock

Program `LocpQgucEQHbqNABEYvBvwoxCPsSbG91A1QaQhQQqjn` (executable account, confirmed this run). Lock program account is executable. Reference escrow 51EH7rNnbU5ZRvcCNNDuk16kevwbQE22uV9AZsRan7om is owned by that program and is included in the scan.

These are escrow token-account balances. They are not burned. 2 Jupiter Lock accounts for this mint have a zero token balance and are not included in the locked total.

Unlock times are shown only when the escrow account matches the Jupiter Lock vesting layout and the timestamps decode cleanly. The projection rule is: nothing is unlocked before `cliff_time`; after that, unlocked = cliff amount + amount per period × completed periods, and completed periods = min(number of periods, floor((now − cliff time) / frequency)). A root escrow, or any account that does not match that layout, is listed with its amount only.

| Escrow | Amount | % of supply | Unlock schedule |
| --- | ---: | ---: | --- |
| `7upKqUpChoancUwHCEv7RWYnyrjqhq8U44syv1nV42kB` | 130,000,003.99992 | 14.72% | Cliff 2028-11-27 03:30 UTC unlocks 0; then 1,083,333.366666 every 2,628,000 seconds (365/12 days) for 120 periods; fully unlocks 2038-11-25 03:30 UTC; next unlock 2028-12-27 13:30 UTC; claimed 0 |
| `Fi5k3MW1ycvx3cq2sXA7SxYyUPErjkZMfLNuGgA7fWU1` | 101,000,000 | 11.44% | Cliff 2026-06-18 13:40 UTC unlocks 0; then 50,500,000 every 365 days for 2 periods; fully unlocks 2028-06-17 13:40 UTC; next unlock 2027-06-18 13:40 UTC; claimed 0 |
| `Gg2FhWHQwQAkjgGdEsq1JKWpPXVCtHL4FAwXpfe8HMyh` | 56,219,184.98604 | 6.37% | Cliff 2026-10-17 18:40 UTC unlocks 0; then 156,164.402739 every 7 days for 365 periods; fully unlocks 2033-10-15 18:40 UTC; next unlock 2026-11-28 18:40 UTC; claimed 780,822.013695 |
| `51EH7rNnbU5ZRvcCNNDuk16kevwbQE22uV9AZsRan7om` | 50,000,000 | 5.66% | Cliff 2025-12-04 17:30 UTC unlocks 0; then 50,000,000 every 365 days for 1 period; fully unlocks 2026-12-04 17:30 UTC; claimed 0 |
| `2uJKBDNLRVeHX2x5xdEMsBEgjpVP2pSsFLTv3kQ3CyXZ` | 41,666,666.66666 | 4.72% | Cliff 2026-06-26 22:30 UTC unlocks 0; then 2,083,333.333333 every 2,628,000 seconds (365/12 days) for 24 periods; fully unlocks 2028-06-25 22:30 UTC; next unlock 2026-11-26 00:30 UTC; claimed 8,333,333.333332 |
| `X8ACD4nKbSvurcgZR67yQkdTHjwYy9rwW6qhVGZaqpz` | 26,250,000 | 2.97% | Cliff 2026-06-11 23:19 UTC unlocks 0; then 3,750,000 every 2,628,000 seconds (365/12 days) for 12 periods; fully unlocks 2027-06-11 23:19 UTC; next unlock 2026-12-11 11:19 UTC; claimed 18,750,000 |
| `6UTqKpUNe1NxThAfdF1HMXqw8TtLTDzuzrwTwvQNC9zZ` | 24,999,999.999996 | 2.83% | Cliff 2026-05-23 09:30 UTC unlocks 0; then 4,166,666.666666 every 2,628,000 seconds (365/12 days) for 12 periods; fully unlocks 2027-05-23 09:30 UTC; next unlock 2026-12-22 07:30 UTC; claimed 24,999,999.999996 |
| `8CJPhy7xg4FAjeM7FqSBGMg9VeV28ELkbMmoab2i3MN1` | 18,333,333.333315 | 2.08% | Cliff 2026-08-04 05:15 UTC unlocks 0; then 555,555.555555 every 2,628,000 seconds (365/12 days) for 36 periods; fully unlocks 2029-08-03 05:15 UTC; next unlock 2026-12-03 21:15 UTC; claimed 1,666,666.666665 |
| `F8cfionqBpGYSEdk5KbFBAfazvD2v9YE8ciZYdvCcP1q` | 18,049,999.999962 | 2.04% | Cliff 2026-08-13 20:15 UTC unlocks 0; then 316,666.666666 every 2,628,000 seconds (365/12 days) for 60 periods; fully unlocks 2031-08-12 20:15 UTC; next unlock 2026-12-13 12:15 UTC; claimed 949,999.999998 |
| `6RjCHSkGut6yqyYCq94qhQCCkFSJdw3RWvJ3piMWwMc2` | 9,499,999.999962 | 1.08% | Cliff 2026-08-25 16:35 UTC unlocks 0; then 166,666.666666 every 2,628,000 seconds (365/12 days) for 60 periods; fully unlocks 2031-08-24 16:35 UTC; next unlock 2026-12-25 08:35 UTC; claimed 499,999.999998 |
| `iwYecboj4ndmXFJesGX5ojcPyxH8X9exX4eJSoHgoAo` | 6,708,337.166659 | 0.76% | Cliff 2026-09-30 08:30 UTC unlocks 0; then 291,666.833333 every 2,628,000 seconds (365/12 days) for 24 periods; fully unlocks 2028-09-29 08:30 UTC; next unlock 2026-11-30 04:30 UTC; claimed 291,666.833333 |
| `83WKDEjBzQtZDLWYHXJfhfh5QxgU4FfMwDGY8ojc6hBq` | 5,833,337.5 | 0.66% | Cliff 2026-09-08 15:13 UTC unlocks 0; then 583,333.75 every 2,628,000 seconds (365/12 days) for 12 periods; fully unlocks 2027-09-08 15:13 UTC; next unlock 2026-12-08 21:13 UTC; claimed 1,166,667.5 |
| `4mEe3AnkBJ4w8WCrwd1DK1APrSt5NMUuQDDZ3J9HVpyr` | 5,000,004.16666 | 0.57% | Cliff 2026-09-23 12:09 UTC unlocks 0; then 500,000.416666 every 2,628,000 seconds (365/12 days) for 12 periods; fully unlocks 2027-09-23 12:09 UTC; next unlock 2026-12-23 18:09 UTC; claimed 1,000,000.833332 |
| `9qZCyEWdmZhyC8S4UJEUnjGDbw8tkZ6rmFf3BGzHmZr3` | 4,166,670.83333 | 0.47% | Cliff 2026-09-16 22:10 UTC unlocks 0; then 416,667.083333 every 2,628,000 seconds (365/12 days) for 12 periods; fully unlocks 2027-09-16 22:10 UTC; next unlock 2026-12-17 04:10 UTC; claimed 833,334.166666 |

## Top 20 holders

Largest token accounts were taken from a full getProgramAccounts scan of this mint, sorted by balance, because getTokenLargestAccounts was rate limited on the public RPC. The owner is read from each token account. Percent is of current supply. A Jupiter Lock label means that owner is one of the escrows above. A StakePoint label means the owner account is owned by the StakePoint program. Those balances are not split into staking versus locks here, and they are not removed from the circulating estimate.

| # | Token account | Owner | Amount | % of supply | Label |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | `CqB9eSKWoLszxYQVihafRggeJmEq96TqdiGwb9Xg1H6n` | `7Z82HCGMkKh1z9aXEduPTnZc42aRV3R3ruCxeh1XZgqn` | 266,512,534.333466 | 30.18% | Liquidity pool (PumpSwap) |
| 2 | `8gMyiQthfzx4t1LyBJHQbZD5469P4CbW3wS4rW28KMrG` | `7upKqUpChoancUwHCEv7RWYnyrjqhq8U44syv1nV42kB` | 130,000,003.99992 | 14.72% | Jupiter Lock |
| 3 | `4Sk5rB4TBFWvkDWFspbK3JWHwjsyUPiQSrcbcnTLJheD` | `Fi5k3MW1ycvx3cq2sXA7SxYyUPErjkZMfLNuGgA7fWU1` | 101,000,000 | 11.44% | Jupiter Lock |
| 4 | `8pmngsdWyttyJPXoxTPLo4UYN9WgWHEYyouRgGNRAXvg` | `Gg2FhWHQwQAkjgGdEsq1JKWpPXVCtHL4FAwXpfe8HMyh` | 56,219,184.98604 | 6.37% | Jupiter Lock |
| 5 | `EyqLVoWiQCSAGPyzDE3g2AvcpD1SDv6znysCA6U2kFqu` | `51EH7rNnbU5ZRvcCNNDuk16kevwbQE22uV9AZsRan7om` | 50,000,000 | 5.66% | Jupiter Lock |
| 6 | `5gxYUPNtdY2qrnsA4FtEHP79UQjPsPYmCEJrAkVu7Asn` | `2uJKBDNLRVeHX2x5xdEMsBEgjpVP2pSsFLTv3kQ3CyXZ` | 41,666,666.66666 | 4.72% | Jupiter Lock |
| 7 | `8wxsYwXzkZRGE7NBWGaMSLSF9LHp1BRQyzM9epAYaGuJ` | `G6qqhy358WzBfHAsUnnj3puPfUC6i7Ev3QaVBaaLMqoj` | 30,622,899.894648 | 3.47% | StakePoint |
| 8 | `D8jPjPFTKVzy72beqpT9DmAzFCvT4Ta66sdRzZmWzUYe` | `2x62yXUrTWdwFssmmyyaioz7uoLrcGNnZUuCW9Pej9D7` | 28,164,576.443887 | 3.19% | — |
| 9 | `5u1SSnsf3kVXV1GzLNuWHm7mNQnJvSo1yqUiRvAxMjQg` | `X8ACD4nKbSvurcgZR67yQkdTHjwYy9rwW6qhVGZaqpz` | 26,250,000 | 2.97% | Jupiter Lock |
| 10 | `5RRj2qz6BowFPUpLD6XP9UjPXqwaFRMXrfhxzTfHbipJ` | `6UTqKpUNe1NxThAfdF1HMXqw8TtLTDzuzrwTwvQNC9zZ` | 24,999,999.999996 | 2.83% | Jupiter Lock |
| 11 | `E1GJvJpjshycim3nyaa2whdbx1pnnDVPQZD8JwokNGt1` | `8CJPhy7xg4FAjeM7FqSBGMg9VeV28ELkbMmoab2i3MN1` | 18,333,333.333315 | 2.08% | Jupiter Lock |
| 12 | `9ot5APgSYobTfTyHVb1pFSiGyd7EaFdCF5m9kx7MBWXH` | `F8cfionqBpGYSEdk5KbFBAfazvD2v9YE8ciZYdvCcP1q` | 18,049,999.999962 | 2.04% | Jupiter Lock |
| 13 | `23cj9KNLZ9mQVT7CDu94iERPfDxtErLcC1gpzJ5m2fxq` | `6RjCHSkGut6yqyYCq94qhQCCkFSJdw3RWvJ3piMWwMc2` | 9,499,999.999962 | 1.08% | Jupiter Lock |
| 14 | `C6ZCS4uRcBiGnGUEHNb6q4qKbJC9fKTEZKTmVehAqQKm` | `iwYecboj4ndmXFJesGX5ojcPyxH8X9exX4eJSoHgoAo` | 6,708,337.166659 | 0.76% | Jupiter Lock |
| 15 | `Fxot2Q3NDDCm9jZ59hhT7HQA7o7DsjjjxZmjzdHpDBtE` | `G6qqhy358WzBfHAsUnnj3puPfUC6i7Ev3QaVBaaLMqoj` | 5,917,205.320002 | 0.67% | StakePoint |
| 16 | `5PVsW1G398TS7UhX28qpG8Mdvua4DBY5F46B4SDncXtW` | `83WKDEjBzQtZDLWYHXJfhfh5QxgU4FfMwDGY8ojc6hBq` | 5,833,337.5 | 0.66% | Jupiter Lock |
| 17 | `Fc3TfESvcEmNt9T9bYwj9KUuVwn3yqP842ctaJNMe23s` | `9jSRcv5D6NKYRVoVu8vT9vKLNwcJXneVwsHw2R1nkXHf` | 5,462,595.939561 | 0.62% | — |
| 18 | `6Sb1p5YV5XnYP3or1vAZSw66W5f8xSqGeUDnFihSx2ny` | `tTvpTo2EkdupVkUq9DF476MHHWce9J6WH11ojK8AKQQ` | 5,304,180.146695 | 0.60% | — |
| 19 | `45xxmToxGLYT2hpLnjaMqK8QLMnc3c7VdPTfQeiaSV4D` | `4mEe3AnkBJ4w8WCrwd1DK1APrSt5NMUuQDDZ3J9HVpyr` | 5,000,004.16666 | 0.57% | Jupiter Lock |
| 20 | `3g6h9h64nEuVdafNA5xZcDNg6zJyPKG26pGSC7SSy7M7` | `9qZCyEWdmZhyC8S4UJEUnjGDbw8tkZ6rmFf3BGzHmZr3` | 4,166,670.83333 | 0.47% | Jupiter Lock |

## Check the source

- [RugCheck](https://rugcheck.xyz/tokens/2pVmu5B3QAX7GdfDkq84dpbewGag1hZoEyYZcHFYpump)
- [Solscan mint](https://solscan.io/token/2pVmu5B3QAX7GdfDkq84dpbewGag1hZoEyYZcHFYpump)
- [Latest JSON](data/latest.json)
- [Daily history](data/history.csv)
- [Update script](scripts/update_transparency.py)

History columns: date (UTC), supply, burned, locked, circulating estimate.

GitHub Actions runs [the update workflow](.github/workflows/update.yml) every day at 14:00 UTC and on manual dispatch. It reads the public Solana RPC endpoints `https://api.mainnet-beta.solana.com` and `https://solana-rpc.publicnode.com`. There is no API key.

This file is generated by `scripts/update_transparency.py`.

---

Not financial advice.
