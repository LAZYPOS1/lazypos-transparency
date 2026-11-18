#!/usr/bin/env python3
"""Build the LAZYPOS on-chain transparency report from public Solana RPC data.

Reads supply, Jupiter Lock escrows, and the largest token accounts, then writes
data/latest.json, appends data/history.csv, and regenerates README.md.

Uses only the public endpoints below. No API key and no secret belongs here.
"""

from __future__ import annotations

import csv
import json
import time
import base64
import struct
import urllib.error
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from zoneinfo import ZoneInfo

MINT = "2pVmu5B3QAX7GdfDkq84dpbewGag1hZoEyYZcHFYpump"
ORIGINAL_SUPPLY_WHOLE = 1_000_000_000
LOCK_PROGRAM = "LocpQgucEQHbqNABEYvBvwoxCPsSbG91A1QaQhQQqjn"
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
# Reference escrow the report checks so a bad program id cannot publish quietly.
KNOWN_ESCROW = "51EH7rNnbU5ZRvcCNNDuk16kevwbQE22uV9AZsRan7om"

RPC_URLS = (
    "https://api.mainnet-beta.solana.com",
    "https://solana-rpc.publicnode.com",
)

# jupiter-lock-sdk VestingEscrow discriminator and layout (296 bytes).
VESTING_DISC = bytes((244, 119, 183, 4, 73, 116, 135, 195))
VESTING_LEN = 296
# jupiter-lock-sdk RootEscrow discriminator. Root accounts have no vesting schedule.
ROOT_DISC = bytes((253, 209, 220, 107, 206, 191, 71, 158))

# Token-account authority is labeled a liquidity pool only when that authority
# account is owned by one of these programs.
# Custody programs that are not liquidity pools. StakePoint accounts are labeled
# only as that program: the same program holds locks and staking positions, and
# this report does not decode which one a balance is.
OTHER_PROGRAMS = {
    "gLHaGJsZ6G7AXZxoDL9EsSWkRbKAWhFHi73gVfNXuzK": "StakePoint",
}

LIQUIDITY_PROGRAMS = {
    "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P": "Pump.fun bonding curve",
    "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA": "PumpSwap",
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "Raydium AMM v4",
    "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C": "Raydium CPMM",
    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": "Raydium CLMM",
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "Orca Whirlpool",
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo": "Meteora DLMM",
    "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB": "Meteora DAMM v1",
    "cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG": "Meteora DAMM v2",
}

RUGCHECK_URL = f"https://rugcheck.xyz/tokens/{MINT}"
SOLSCAN_URL = f"https://solscan.io/token/{MINT}"
US_CENTRAL = ZoneInfo("America/Chicago")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
LATEST_PATH = DATA_DIR / "latest.json"
HISTORY_PATH = DATA_DIR / "history.csv"
README_PATH = ROOT / "README.md"

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_B58_INDEX = {char: index for index, char in enumerate(_B58)}


class RpcError(Exception):
    pass


class RateLimited(RpcError):
    pass


class MethodNotAllowed(RpcError):
    pass


def b58encode(data: bytes) -> str:
    zeros = 0
    for byte in data:
        if byte == 0:
            zeros += 1
        else:
            break
    number = int.from_bytes(data, "big")
    chars: list[str] = []
    while number:
        number, rem = divmod(number, 58)
        chars.append(_B58[rem])
    return "1" * zeros + "".join(reversed(chars))


def b58decode(text: str) -> bytes:
    zeros = 0
    for char in text:
        if char == "1":
            zeros += 1
        else:
            break
    number = 0
    for char in text:
        try:
            number = number * 58 + _B58_INDEX[char]
        except KeyError as exc:
            raise RpcError(f"Invalid base58 pubkey: {text}") from exc
    body = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    return b"\x00" * zeros + body


def pubkey_bytes(text: str) -> bytes:
    raw = b58decode(text)
    if len(raw) != 32:
        raise RpcError(f"Pubkey is {len(raw)} bytes, expected 32: {text}")
    return raw


def self_check() -> None:
    system = "1" * 32
    if b58encode(b"\x00" * 32) != system or pubkey_bytes(system) != b"\x00" * 32:
        raise RpcError("base58 self-check failed for the system program")
    token = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    if b58encode(pubkey_bytes(token)) != token:
        raise RpcError("base58 self-check failed for the token program")
    if b58encode(pubkey_bytes(MINT)) != MINT:
        raise RpcError("base58 self-check failed for the LAZYPOS mint")
    if len(VESTING_DISC) != 8 or len(ROOT_DISC) != 8:
        raise RpcError("account discriminator length is not 8")


def ui_str(raw: int, decimals: int) -> str:
    sign = "-" if raw < 0 else ""
    whole, frac = divmod(abs(raw), 10**decimals)
    if frac == 0:
        return f"{sign}{whole}"
    frac_s = f"{frac:0{decimals}d}".rstrip("0")
    return f"{sign}{whole}.{frac_s}"


def ui_commas(raw: int, decimals: int) -> str:
    text = ui_str(raw, decimals)
    sign = ""
    if text.startswith("-"):
        sign, text = "-", text[1:]
    whole, dot, frac = text.partition(".")
    pretty = f"{int(whole):,}"
    return sign + pretty + (dot + frac if dot else "")


def percent_str(part: int, whole: int) -> str:
    if whole == 0:
        return "0.00"
    value = (Decimal(part) * Decimal(100) / Decimal(whole)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return f"{value:.2f}"


def fmt_ts(ts: int) -> str:
    moment = datetime.fromtimestamp(ts, timezone.utc)
    pattern = "%Y-%m-%d %H:%M:%S UTC" if moment.second else "%Y-%m-%d %H:%M UTC"
    return moment.strftime(pattern)


def plausible_time(ts: int) -> bool:
    return 1_500_000_000 <= ts <= 2_500_000_000


def human_frequency(seconds: int) -> str:
    if seconds > 0 and seconds % 86400 == 0:
        days = seconds // 86400
        unit = "day" if days == 1 else "days"
        return f"{days:,} {unit}"
    if seconds > 0 and 31_536_000 % seconds == 0:
        parts = 31_536_000 // seconds
        return f"{seconds:,} seconds (365/{parts} days)"
    return f"{seconds:,} seconds"


class RpcClient:
    def __init__(self, urls: tuple[str, ...]) -> None:
        self.urls = list(urls)
        self.blocked: dict[str, set[str]] = {url: set() for url in self.urls}
        self.last_call = 0.0

    def call(self, method: str, params: list, timeout: int = 90, attempts: int = 6):
        delay = 5.0
        last_error: Exception | None = None
        rate_limits = 0
        while rate_limits < attempts:
            candidates = [url for url in self.urls if method not in self.blocked[url]]
            if not candidates:
                raise RpcError(
                    f"{method} is not available on the configured public RPCs. Last error: {last_error}"
                )
            url = candidates[0]
            wait = 0.35 - (time.time() - self.last_call)
            if wait > 0:
                time.sleep(wait)
            try:
                result = self._post(url, method, params, timeout)
                self.last_call = time.time()
                return result
            except MethodNotAllowed as exc:
                self.blocked[url].add(method)
                last_error = exc
                print(f"rpc {method} not allowed on {url}; trying another endpoint", flush=True)
            except RateLimited as exc:
                rate_limits += 1
                last_error = exc
                message = str(exc).lower()
                if "specific rpc call" in message:
                    delay = max(delay, 20.0)
                print(f"rpc retry {rate_limits} for {method}: {exc}", flush=True)
                time.sleep(delay)
                delay = min(delay * 2, 60.0)
        raise RpcError(f"{method} failed after retries: {last_error}")

    def _post(self, url: str, method: str, params: list, timeout: int):
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode(errors="replace")
            lowered = raw.lower()
            if exc.code == 429 or "too many requests" in lowered or "rate limit" in lowered:
                raise RateLimited(f"{exc.code} {raw[:180]}")
            if exc.code == 403 or "personal token" in lowered or "indexed requests" in lowered:
                raise MethodNotAllowed(f"{exc.code} {raw[:180]}")
            if exc.code in (408, 500, 502, 503, 504):
                raise RateLimited(f"{exc.code} {raw[:180]}")
            raise RpcError(f"HTTP {exc.code} from {url}: {raw[:300]}")
        except urllib.error.URLError as exc:
            raise RateLimited(str(exc))

        if "error" in body:
            err = body["error"]
            message = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            code = err.get("code") if isinstance(err, dict) else None
            lowered = message.lower()
            if code == 429 or "too many requests" in lowered or "rate limit" in lowered:
                raise RateLimited(message)
            if "indexed requests" in lowered or "personal token" in lowered:
                raise MethodNotAllowed(message)
            if code in (-32005, -32016) or "secondary indexes" in lowered or "not available" in lowered:
                raise MethodNotAllowed(message)
            raise RpcError(message)
        return body["result"]


def account_data(account: dict | None) -> bytes | None:
    if not account:
        return None
    data = account.get("data")
    if isinstance(data, list) and data:
        return base64.b64decode(data[0])
    if isinstance(data, str):
        return base64.b64decode(data)
    return None


def get_account(rpc: RpcClient, pubkey: str) -> dict | None:
    result = rpc.call(
        "getAccountInfo",
        [pubkey, {"encoding": "base64", "commitment": "finalized"}],
    )
    return result["value"]


def u64_at(raw: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", raw, offset)[0]


def decode_vesting(raw: bytes) -> dict | None:
    """Return schedule fields when the account matches the published 296-byte layout."""
    if len(raw) != VESTING_LEN or raw[:8] != VESTING_DISC:
        return None
    if raw[40:72] != pubkey_bytes(MINT):
        return None
    fields = {
        "recipient": b58encode(raw[8:40]),
        "creator": b58encode(raw[72:104]),
        "base": b58encode(raw[104:136]),
        "escrow_bump": raw[136],
        "update_recipient_mode": raw[137],
        "cancel_mode": raw[138],
        "token_program_flag": raw[139],
        "cliff_time": u64_at(raw, 144),
        "frequency": u64_at(raw, 152),
        "cliff_unlock_amount": u64_at(raw, 160),
        "amount_per_period": u64_at(raw, 168),
        "number_of_period": u64_at(raw, 176),
        "total_claimed_amount": u64_at(raw, 184),
        "vesting_start_time": u64_at(raw, 192),
        "cancelled_at": u64_at(raw, 200),
    }
    if not schedule_is_reliable(fields):
        return None
    return fields


def schedule_is_reliable(fields: dict) -> bool:
    frequency = fields["frequency"]
    periods = fields["number_of_period"]
    if frequency == 0 or periods > 100_000:
        return False
    if frequency > 31_536_000 * 100:
        return False
    if not plausible_time(fields["cliff_time"]) or not plausible_time(fields["vesting_start_time"]):
        return False
    if fields["cancelled_at"] not in (0,) and not plausible_time(fields["cancelled_at"]):
        return False
    # Reject a layout that cannot represent its own total in a u64.
    try:
        total = fields["cliff_unlock_amount"] + fields["amount_per_period"] * periods
    except OverflowError:
        return False
    return 0 <= total <= 2**64 - 1


def projected_unlocks(fields: dict, now_ts: int) -> dict:
    """Jupiter Lock get_max_unlocked_amount, from the program rule.

    Before cliff_time the unlocked amount is 0. After that:
    periods = min(number_of_period, floor((now - cliff_time) / frequency))
    unlocked = cliff_unlock_amount + amount_per_period * periods
    The full amount is unlocked at cliff_time + frequency * number_of_period.
    """
    cliff = fields["cliff_time"]
    frequency = fields["frequency"]
    periods_total = fields["number_of_period"]
    cliff_amt = fields["cliff_unlock_amount"]
    per = fields["amount_per_period"]
    if now_ts < cliff:
        elapsed = 0
        unlocked = 0
    else:
        elapsed = min((now_ts - cliff) // frequency, periods_total)
        unlocked = cliff_amt + per * elapsed
    full_at = cliff + frequency * periods_total
    if fields["cancelled_at"]:
        next_at = None
    elif now_ts < cliff:
        next_at = cliff if cliff_amt > 0 else cliff + frequency
    elif elapsed >= periods_total:
        next_at = None
    else:
        next_at = cliff + (elapsed + 1) * frequency
    return {
        "unlocked_raw": unlocked,
        "periods_elapsed": elapsed,
        "fully_unlocked_at": full_at,
        "next_unlock_at": next_at,
        "projections": fields["cancelled_at"] == 0,
    }


def describe_schedule(fields: dict, projection: dict, decimals: int) -> str:
    per = ui_commas(fields["amount_per_period"], decimals)
    claimed = ui_commas(fields["total_claimed_amount"], decimals)
    freq = human_frequency(fields["frequency"])
    periods = fields["number_of_period"]
    period_word = "period" if periods == 1 else "periods"
    cliff = fmt_ts(fields["cliff_time"])
    if fields["cliff_unlock_amount"]:
        opening = (
            f"{ui_commas(fields['cliff_unlock_amount'], decimals)} unlocks at cliff {cliff}"
        )
    else:
        opening = f"Cliff {cliff} unlocks 0"
    sentence = f"{opening}; then {per} every {freq} for {periods} {period_word}"
    if projection["projections"]:
        sentence += f"; fully unlocks {fmt_ts(projection['fully_unlocked_at'])}"
        next_at = projection["next_unlock_at"]
        if next_at and next_at != projection["fully_unlocked_at"]:
            sentence += f"; next unlock {fmt_ts(next_at)}"
    else:
        sentence += f"; cancelled_at {fmt_ts(fields['cancelled_at'])}; later unlocks not projected"
    sentence += f"; claimed {claimed}"
    return sentence


def schedule_payload(fields: dict, projection: dict, decimals: int) -> dict:
    payload = {
        "vesting_start_time": fields["vesting_start_time"],
        "vesting_start_utc": fmt_ts(fields["vesting_start_time"]),
        "cliff_time": fields["cliff_time"],
        "cliff_utc": fmt_ts(fields["cliff_time"]),
        "frequency_seconds": fields["frequency"],
        "cliff_unlock_amount_raw": str(fields["cliff_unlock_amount"]),
        "cliff_unlock_amount": ui_str(fields["cliff_unlock_amount"], decimals),
        "amount_per_period_raw": str(fields["amount_per_period"]),
        "amount_per_period": ui_str(fields["amount_per_period"], decimals),
        "number_of_periods": fields["number_of_period"],
        "total_claimed_amount_raw": str(fields["total_claimed_amount"]),
        "total_claimed_amount": ui_str(fields["total_claimed_amount"], decimals),
        "cancelled_at": fields["cancelled_at"],
        "rule": (
            "Before cliff_time, unlocked is 0. After that, unlocked = "
            "cliff_unlock_amount + amount_per_period * min(number_of_periods, "
            "floor((now - cliff_time) / frequency)). Full unlock is at "
            "cliff_time + frequency * number_of_periods."
        ),
    }
    if projection["projections"]:
        payload["unlocked_amount_raw"] = str(projection["unlocked_raw"])
        payload["unlocked_amount"] = ui_str(projection["unlocked_raw"], decimals)
        payload["periods_elapsed"] = projection["periods_elapsed"]
        payload["fully_unlocked_utc"] = fmt_ts(projection["fully_unlocked_at"])
        if projection["next_unlock_at"]:
            payload["next_unlock_utc"] = fmt_ts(projection["next_unlock_at"])
    return payload


def fetch_program_accounts(rpc: RpcClient, filters: list) -> list:
    result = rpc.call(
        "getProgramAccounts",
        [
            LOCK_PROGRAM,
            {"encoding": "base64", "commitment": "finalized", "filters": filters},
        ],
        timeout=120,
    )
    return result


def token_accounts_of(rpc: RpcClient, owner: str) -> list[dict]:
    result = rpc.call(
        "getTokenAccountsByOwner",
        [
            owner,
            {"mint": MINT},
            {"encoding": "jsonParsed", "commitment": "finalized"},
        ],
    )
    accounts = []
    for item in result["value"]:
        info = item["account"]["data"]["parsed"]["info"]
        amount = int(info["tokenAmount"]["amount"])
        accounts.append({"address": item["pubkey"], "amount_raw": amount})
    return accounts


def collect_escrows(rpc: RpcClient, now_ts: int, decimals: int) -> tuple[list[dict], dict]:
    vesting_rows = fetch_program_accounts(
        rpc,
        [
            {"memcmp": {"offset": 0, "bytes": b58encode(VESTING_DISC)}},
            {"memcmp": {"offset": 40, "bytes": MINT}},
        ],
    )
    root_rows = fetch_program_accounts(
        rpc,
        [
            {"memcmp": {"offset": 0, "bytes": b58encode(ROOT_DISC)}},
            {"memcmp": {"offset": 8, "bytes": MINT}},
        ],
    )
    found: list[dict] = []
    decoded = 0
    for row in vesting_rows:
        raw = account_data(row["account"]) or b""
        fields = decode_vesting(raw)
        entry = {
            "escrow": row["pubkey"],
            "kind": "vesting_escrow",
            "owner_program": row["account"]["owner"],
            "fields": fields,
        }
        if fields:
            decoded += 1
            entry["projection"] = projected_unlocks(fields, now_ts)
        found.append(entry)
    for row in root_rows:
        found.append(
            {
                "escrow": row["pubkey"],
                "kind": "root_escrow",
                "owner_program": row["account"]["owner"],
                "fields": None,
            }
        )

    detailed = []
    for entry in found:
        if entry["owner_program"] != LOCK_PROGRAM:
            raise RpcError(f"Escrow {entry['escrow']} is not owned by the Jupiter Lock program")
        accounts = token_accounts_of(rpc, entry["escrow"])
        amount = sum(item["amount_raw"] for item in accounts)
        record = {
            "escrow": entry["escrow"],
            "kind": entry["kind"],
            "known_reference": entry["escrow"] == KNOWN_ESCROW,
            "token_accounts": [
                {
                    "address": item["address"],
                    "amount_raw": str(item["amount_raw"]),
                    "amount": ui_str(item["amount_raw"], decimals),
                }
                for item in accounts
            ],
            "amount_raw": amount,
            "schedule_decoded": entry["fields"] is not None,
        }
        fields = entry["fields"]
        if fields:
            record["recipient"] = fields["recipient"]
            record["creator"] = fields["creator"]
            record["schedule"] = schedule_payload(fields, entry["projection"], decimals)
            record["schedule_text"] = describe_schedule(fields, entry["projection"], decimals)
        detailed.append(record)

    meta = {
        "vesting_accounts": len(vesting_rows),
        "root_accounts": len(root_rows),
        "schedules_decoded": decoded,
    }
    return detailed, meta


def verify_program_and_known_escrow(rpc: RpcClient, escrow_ids: set[str]) -> dict:
    program = get_account(rpc, LOCK_PROGRAM)
    if not program or not program.get("executable"):
        raise RpcError(f"{LOCK_PROGRAM} is not an executable program account")
    known = get_account(rpc, KNOWN_ESCROW)
    if known is None:
        return {
            "program_id": LOCK_PROGRAM,
            "program_executable": True,
            "known_escrow": KNOWN_ESCROW,
            "known_escrow_on_chain": False,
            "note": "Lock program account is executable. The reference escrow account is not on-chain.",
        }
    owner = known.get("owner")
    if owner != LOCK_PROGRAM:
        raise RpcError(
            f"Reference escrow {KNOWN_ESCROW} is owned by {owner}, not {LOCK_PROGRAM}. "
            "Refusing to publish with an unverified Jupiter Lock program id."
        )
    if KNOWN_ESCROW not in escrow_ids:
        raise RpcError(
            f"Reference escrow {KNOWN_ESCROW} is a Jupiter Lock account but the mint scan did not return it. "
            "Refusing to publish a partial lock set."
        )
    return {
        "program_id": LOCK_PROGRAM,
        "program_executable": True,
        "known_escrow": KNOWN_ESCROW,
        "known_escrow_on_chain": True,
        "known_escrow_owner": owner,
        "note": (
            "Lock program account is executable. "
            f"Reference escrow {KNOWN_ESCROW} is owned by that program and is included in the scan."
        ),
    }


def fetch_largest(rpc: RpcClient) -> list[dict]:
    result = rpc.call(
        "getTokenLargestAccounts",
        [MINT, {"commitment": "finalized"}],
        attempts=3,
    )
    return result["value"]


def scan_largest_token_accounts(rpc: RpcClient, token_program: str, limit: int = 20) -> list[dict]:
    """Largest accounts by decoding every token account for the mint.

    Used when getTokenLargestAccounts is rate limited. dataSlice keeps the
    response to the owner pubkey and the amount.
    """
    filters: list[dict] = [{"memcmp": {"offset": 0, "bytes": MINT}}]
    if token_program == TOKEN_PROGRAM:
        filters.insert(0, {"dataSize": 165})
    rows = rpc.call(
        "getProgramAccounts",
        [
            token_program,
            {
                "encoding": "base64",
                "commitment": "finalized",
                "dataSlice": {"offset": 32, "length": 40},
                "filters": filters,
            },
        ],
        timeout=120,
    )
    decoded = []
    for row in rows:
        raw = account_data(row["account"]) or b""
        if len(raw) < 40:
            continue
        amount = struct.unpack_from("<Q", raw, 32)[0]
        decoded.append((amount, row["pubkey"], b58encode(raw[:32])))
    decoded.sort(key=lambda item: item[0], reverse=True)
    return [
        {"address": pubkey, "amount": str(amount), "owner": owner}
        for amount, pubkey, owner in decoded[:limit]
    ]


def fetch_accounts(rpc: RpcClient, pubkeys: list[str]) -> list[dict | None]:
    values: list[dict | None] = []
    for start in range(0, len(pubkeys), 100):
        chunk = pubkeys[start : start + 100]
        result = rpc.call(
            "getMultipleAccounts",
            [chunk, {"encoding": "base64", "commitment": "finalized"}],
        )
        values.extend(result["value"])
    return values


def token_account_owner(raw: bytes) -> str | None:
    if len(raw) < 64:
        return None
    return b58encode(raw[32:64])


def holder_rows(
    rpc: RpcClient,
    largest: list[dict],
    escrow_ids: set[str],
    decimals: int,
    supply_raw: int,
) -> list[dict]:
    owners: list[str | None] = []
    missing: list[int] = []
    for index, item in enumerate(largest):
        if item.get("owner"):
            owners.append(item["owner"])
        else:
            owners.append(None)
            missing.append(index)
    if missing:
        addresses = [largest[index]["address"] for index in missing]
        accounts = fetch_accounts(rpc, addresses)
        for index, account in zip(missing, accounts):
            raw = account_data(account)
            owners[index] = token_account_owner(raw) if raw else None

    unique = [owner for owner in dict.fromkeys(owners) if owner]
    owner_accounts = fetch_accounts(rpc, unique) if unique else []
    owner_program = {}
    for owner, account in zip(unique, owner_accounts):
        owner_program[owner] = None if account is None else account.get("owner")

    verified_programs: dict[str, bool] = {}

    def executable_program(program_id: str) -> bool:
        if program_id not in verified_programs:
            info = get_account(rpc, program_id)
            verified_programs[program_id] = bool(info and info.get("executable"))
        return verified_programs[program_id]

    rows = []
    for rank, (item, owner) in enumerate(zip(largest, owners), start=1):
        amount = int(item["amount"])
        program_id = owner_program.get(owner) if owner else None
        label = None
        if owner and (owner in escrow_ids or program_id == LOCK_PROGRAM):
            label = "Jupiter Lock"
        elif program_id and program_id in LIQUIDITY_PROGRAMS and executable_program(program_id):
            label = f"Liquidity pool ({LIQUIDITY_PROGRAMS[program_id]})"
        elif program_id and program_id in OTHER_PROGRAMS and executable_program(program_id):
            label = OTHER_PROGRAMS[program_id]
        if label and "burn" in label.lower():
            raise RpcError(f"Refusing holder label that calls an account burned: {label}")
        rows.append(
            {
                "rank": rank,
                "token_account": item["address"],
                "owner": owner,
                "owner_program": program_id,
                "amount_raw": str(amount),
                "amount": ui_str(amount, decimals),
                "percent_of_supply": percent_str(amount, supply_raw),
                "label": label,
            }
        )
    return rows


def build_readme(report: dict) -> str:
    decimals = report["token"]["decimals"]
    supply = int(report["supply"]["raw"])
    burned = int(report["burned"]["raw"])
    locked = int(report["jupiter_lock"]["locked_raw"])
    circulating = int(report["circulating_estimate"]["raw"])
    original = int(report["token"]["original_supply_raw"])
    updated = report["updated_at"]

    def metric_row(name: str, raw: int, share: str) -> str:
        return f"| {name} | {ui_commas(raw, decimals)} | {share} |"

    lock_lines = [
        "| Escrow | Amount | % of supply | Unlock schedule |",
        "| --- | ---: | ---: | --- |",
    ]
    shown = [item for item in report["jupiter_lock"]["escrows"] if int(item["amount_raw"]) > 0]
    if not shown:
        lock_lines.append("| — | 0 | 0.00 | No escrow token account currently holds this token. |")
    for item in shown:
        schedule = item.get("schedule_text") or "Amount only"
        lock_lines.append(
            f"| `{item['escrow']}` | {ui_commas(int(item['amount_raw']), decimals)} | "
            f"{item['percent_of_supply']}% | {schedule} |"
        )

    holder_lines = [
        "| # | Token account | Owner | Amount | % of supply | Label |",
        "| ---: | --- | --- | ---: | ---: | --- |",
    ]
    for item in report["holders_top20"]:
        owner = f"`{item['owner']}`" if item["owner"] else "—"
        label = item["label"] or "—"
        holder_lines.append(
            f"| {item['rank']} | `{item['token_account']}` | {owner} | "
            f"{ui_commas(int(item['amount_raw']), decimals)} | "
            f"{item['percent_of_supply']}% | {label} |"
        )

    zero = report["jupiter_lock"]["zero_balance_escrow_count"]
    zero_sentence = ""
    if zero:
        noun = "account" if zero == 1 else "accounts"
        zero_sentence = (
            f" {zero} Jupiter Lock {noun} for this mint "
            f"{'has' if zero == 1 else 'have'} a zero token balance and "
            f"{'is' if zero == 1 else 'are'} not included in the locked total."
        )

    text = f"""# LAZYPOS Transparency - Don't trust us. Check us.

Figures are read straight from the Solana blockchain and updated daily.

Last updated: {updated['utc']} and {updated['us_central']} (US Central). Supply slot {report['supply']['slot']}.

| Metric | Tokens | Share |
| --- | ---: | --- |
{metric_row("Current supply", supply, "100% of current supply")}
{metric_row("Burned", burned, report['burned']['percent_of_original'] + "% of original 1,000,000,000")}
{metric_row("Jupiter locked", locked, report['jupiter_lock']['percent_of_supply'] + "% of current supply")}
{metric_row("Circulating estimate", circulating, report['circulating_estimate']['percent_of_supply'] + "% of current supply")}

Burned tokens are already removed from current supply (original supply minus `getTokenSupply`). Jupiter-locked tokens are still inside current supply. Circulating estimate = current supply − Jupiter locked. This is an estimate. Staking pools are not separately identified yet, so staked tokens are still included. Liquidity-pool balances are still included too.

Original supply used for the burn figure: {ui_commas(original, decimals)} tokens. On-chain decimals: {decimals}.

## Jupiter Lock

Program `{LOCK_PROGRAM}` (executable account, confirmed this run). {report['jupiter_lock']['verification']['note']}

These are escrow token-account balances. They are not burned.{zero_sentence}

Unlock times are shown only when the escrow account matches the Jupiter Lock vesting layout and the timestamps decode cleanly. The projection rule is: nothing is unlocked before `cliff_time`; after that, unlocked = cliff amount + amount per period × completed periods, and completed periods = min(number of periods, floor((now − cliff time) / frequency)). A root escrow, or any account that does not match that layout, is listed with its amount only.

{chr(10).join(lock_lines)}

## Top 20 holders

{report["holders_source"]} The owner is read from each token account. Percent is of current supply. A Jupiter Lock label means that owner is one of the escrows above. A StakePoint label means the owner account is owned by the StakePoint program. Those balances are not split into staking versus locks here, and they are not removed from the circulating estimate.

{chr(10).join(holder_lines)}

## Check the source

- [RugCheck]({RUGCHECK_URL})
- [Solscan mint]({SOLSCAN_URL})
- [Latest JSON](data/latest.json)
- [Daily history](data/history.csv)
- [Update script](scripts/update_transparency.py)

History columns: date (UTC), supply, burned, locked, circulating estimate.

GitHub Actions runs [the update workflow](.github/workflows/update.yml) every day at 14:00 UTC and on manual dispatch. It reads the public Solana RPC endpoints `https://api.mainnet-beta.solana.com` and `https://solana-rpc.publicnode.com`. There is no API key.

This file is generated by `scripts/update_transparency.py`.

---

Not financial advice.
"""
    return text


def write_outputs(report: dict, decimals: int) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    serializable = json.loads(json.dumps(report))
    # amount_raw on escrows is still an int in `report`; convert via the copy below.
    LATEST_PATH.write_text(json.dumps(serializable, indent=2) + "\n", encoding="utf-8")

    date = report["updated_at"]["date_utc"]
    row = [
        date,
        ui_str(int(report["supply"]["raw"]), decimals),
        ui_str(int(report["burned"]["raw"]), decimals),
        ui_str(int(report["jupiter_lock"]["locked_raw"]), decimals),
        ui_str(int(report["circulating_estimate"]["raw"]), decimals),
    ]
    new_file = not HISTORY_PATH.exists()
    with HISTORY_PATH.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(["date", "supply", "burned", "locked", "circulating_est"])
        writer.writerow(row)

    README_PATH.write_text(build_readme(report), encoding="utf-8")


def as_public(report: dict) -> dict:
    """JSON-safe copy: raw token amounts are strings."""
    locks = []
    for item in report["jupiter_lock"]["escrows"]:
        copied = dict(item)
        copied["amount_raw"] = str(item["amount_raw"])
        locks.append(copied)
    public = dict(report)
    public["jupiter_lock"] = dict(report["jupiter_lock"])
    public["jupiter_lock"]["escrows"] = locks
    return public


def main() -> None:
    self_check()
    rpc = RpcClient(RPC_URLS)
    now = datetime.now(timezone.utc)
    now_ts = int(now.timestamp())

    supply_result = rpc.call("getTokenSupply", [MINT, {"commitment": "finalized"}])
    supply_raw = int(supply_result["value"]["amount"])
    decimals = int(supply_result["value"]["decimals"])
    slot = supply_result["context"]["slot"]
    if not 0 <= decimals <= 18:
        raise RpcError(f"Unexpected mint decimals: {decimals}")

    mint_account = get_account(rpc, MINT)
    if not mint_account:
        raise RpcError("Mint account was not found")
    token_program = mint_account["owner"]

    escrows, scan_meta = collect_escrows(rpc, now_ts, decimals)
    verification = verify_program_and_known_escrow(rpc, {item["escrow"] for item in escrows})

    original_raw = ORIGINAL_SUPPLY_WHOLE * (10**decimals)
    burned_raw = original_raw - supply_raw
    positive = [item for item in escrows if item["amount_raw"] > 0]
    zero = [item for item in escrows if item["amount_raw"] <= 0]
    locked_raw = sum(item["amount_raw"] for item in positive)
    circulating_raw = supply_raw - locked_raw

    for item in escrows:
        item["percent_of_supply"] = percent_str(item["amount_raw"], supply_raw)
    positive.sort(key=lambda item: item["amount_raw"], reverse=True)
    ordered = positive + zero

    escrow_ids = {item["escrow"] for item in escrows}
    try:
        largest = fetch_largest(rpc)
        holders_source = "Largest token accounts come from getTokenLargestAccounts."
    except RpcError as exc:
        print(f"getTokenLargestAccounts unavailable ({exc}); scanning token accounts", flush=True)
        largest = scan_largest_token_accounts(rpc, token_program)
        holders_source = (
            "Largest token accounts were taken from a full getProgramAccounts scan of this mint, "
            "sorted by balance, because getTokenLargestAccounts was rate limited on the public RPC."
        )
    holders = holder_rows(rpc, largest, escrow_ids, decimals, supply_raw)

    central = now.astimezone(US_CENTRAL)
    report = {
        "token": {
            "symbol": "LAZYPOS",
            "mint": MINT,
            "decimals": decimals,
            "token_program": token_program,
            "original_supply": str(ORIGINAL_SUPPLY_WHOLE),
            "original_supply_raw": str(original_raw),
        },
        "updated_at": {
            "date_utc": now.strftime("%Y-%m-%d"),
            "utc": now.strftime("%Y-%m-%d %H:%M UTC"),
            "us_central": central.strftime("%Y-%m-%d %H:%M %Z"),
            "unix": now_ts,
        },
        "rpc_endpoints": list(RPC_URLS),
        "supply": {
            "raw": str(supply_raw),
            "ui": ui_str(supply_raw, decimals),
            "slot": slot,
        },
        "burned": {
            "raw": str(burned_raw),
            "ui": ui_str(burned_raw, decimals),
            "percent_of_original": percent_str(burned_raw, original_raw),
            "definition": "original supply minus current getTokenSupply. Not a holder balance and not a Jupiter escrow.",
        },
        "jupiter_lock": {
            "locked_raw": str(locked_raw),
            "locked_ui": ui_str(locked_raw, decimals),
            "percent_of_supply": percent_str(locked_raw, supply_raw),
            "escrow_count_with_balance": len(positive),
            "zero_balance_escrow_count": len(zero),
            "vesting_accounts_scanned": scan_meta["vesting_accounts"],
            "root_accounts_scanned": scan_meta["root_accounts"],
            "schedules_decoded": scan_meta["schedules_decoded"],
            "verification": verification,
            "escrows": ordered,
        },
        "circulating_estimate": {
            "raw": str(circulating_raw),
            "ui": ui_str(circulating_raw, decimals),
            "percent_of_supply": percent_str(circulating_raw, supply_raw),
            "definition": (
                "current supply minus Jupiter Lock token-account balances. "
                "Estimate: staking pools are not separately identified, and liquidity-pool tokens are not subtracted."
            ),
        },
        "holders_top20": holders,
        "holders_source": holders_source,
        "links": {"rugcheck": RUGCHECK_URL, "solscan": SOLSCAN_URL},
    }

    public = as_public(report)
    write_outputs(public, decimals)
    print("decimals", decimals, flush=True)
    print("supply", ui_str(supply_raw, decimals), flush=True)
    print("burned", ui_str(burned_raw, decimals), percent_str(burned_raw, original_raw) + "%", flush=True)
    print("locked", ui_str(locked_raw, decimals), "escrows_with_balance", len(positive), flush=True)
    print("circulating_est", ui_str(circulating_raw, decimals), flush=True)
    print(
        "schedules_decoded",
        scan_meta["schedules_decoded"],
        "of",
        scan_meta["vesting_accounts"],
        "vesting accounts;",
        scan_meta["root_accounts"],
        "root accounts",
        flush=True,
    )
    print("holders", len(holders), flush=True)
    for item in holders:
        print(
            f"  #{item['rank']} {item['amount']} {item['percent_of_supply']}% "
            f"label={item['label'] or '-'} program={item['owner_program']}",
            flush=True,
        )


if __name__ == "__main__":
    main()
