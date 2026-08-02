"""Pure data helpers for the DeyeCloud integration."""

from datetime import date, datetime

_DAILY_ZERO_RECORD_KEYS = (
    "generationValue",
    "consumptionValue",
    "gridValue",
    "purchaseValue",
    "chargeValue",
    "dischargeValue",
)

_FLOAT_EPSILON = 0.001


def batched_device_serials(device_serials: list[str]) -> list[list[str]]:
    """Split serials into the maximum batch accepted by /device/latest."""
    return [
        device_serials[offset : offset + 10]
        for offset in range(0, len(device_serials), 10)
    ]


def empty_daily_record(day: str) -> dict:
    """Return an integration-generated zero daily record."""
    record = {
        "date": day,
        "_deyecloud_placeholder": True,
    }
    for key in _DAILY_ZERO_RECORD_KEYS:
        record[key] = 0.0
    return record


def parse_api_date(value, local_timezone) -> date | None:
    """Parse a DeyeCloud date-like value into its local calendar date."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(local_timezone)
        return value.date()
    if isinstance(value, date):
        return value

    # Some API regions return epoch timestamps (seconds or milliseconds).
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            timestamp = float(value)
            if timestamp > 1e12:  # milliseconds
                timestamp /= 1000.0
            if timestamp > 1e8:  # plausible epoch seconds (>1973)
                return datetime.fromtimestamp(timestamp, tz=local_timezone).date()
        except (ValueError, OverflowError, OSError):
            return None
        return None

    text = str(value).strip()
    if not text:
        return None

    # Epoch given as a numeric string.
    if text.isdigit() and len(text) >= 10:
        return parse_api_date(int(text), local_timezone)

    # Keep date-only and intentionally naive values as calendar values. Aware
    # ISO timestamps represent instants and must first move into HA's timezone.
    text = text.replace("/", "-")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(local_timezone)
        return parsed.date()
    except ValueError:
        pass

    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _numeric_value(record: dict | None, key: str) -> float | None:
    """Return a numeric value from a daily/monthly record if possible."""
    if not record:
        return None
    try:
        value = record.get(key)
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def records_look_like_same_daily_bucket(
    record: dict | None,
    reference: dict | None,
) -> bool:
    """Detect a daily record that is likely copied from the reference day."""
    if not record or not reference:
        return False

    matched_non_zero_values = 0
    reference_non_zero_keys = 0
    for key in _DAILY_ZERO_RECORD_KEYS:
        current = _numeric_value(record, key)
        previous = _numeric_value(reference, key)
        if previous is not None and previous > _FLOAT_EPSILON:
            reference_non_zero_keys += 1
        if current is None or previous is None:
            continue

        # The cloud can serve a slightly older snapshot of yesterday rather
        # than an exact copy, so allow the same 2% drift seen in issue logs.
        tolerance = max(_FLOAT_EPSILON, previous * 0.02)
        if previous > _FLOAT_EPSILON and abs(current - previous) <= tolerance:
            matched_non_zero_values += 1

    if reference_non_zero_keys == 0:
        return False

    required_matches = min(2, reference_non_zero_keys)
    return matched_non_zero_values >= required_matches


def should_reject_stale_today(
    record: dict | None,
    yesterday: dict | None,
    cached_today: dict | None,
    *,
    in_midnight_guard: bool,
) -> bool:
    """Return whether a Today candidate is demonstrably yesterday's bucket."""
    guarding_placeholder = bool(
        cached_today and cached_today.get("_deyecloud_placeholder")
    )
    return (
        (in_midnight_guard or guarding_placeholder)
        and records_look_like_same_daily_bucket(record, yesterday)
    )


def resolve_today_record(
    day: str,
    candidate: dict | None,
    yesterday: dict | None,
    cached_today: dict | None,
    *,
    in_midnight_guard: bool,
) -> dict | None:
    """Choose a trustworthy Today record without inventing intraday zeroes."""
    if candidate is not None and not should_reject_stale_today(
        candidate,
        yesterday,
        cached_today,
        in_midnight_guard=in_midnight_guard,
    ):
        return candidate
    if cached_today is not None:
        return cached_today
    if in_midnight_guard:
        return empty_daily_record(day)
    return None
