"""Regression tests for DeyeCloud daily-bucket handling."""

from importlib.util import module_from_spec, spec_from_file_location
from datetime import datetime
from pathlib import Path
import unittest
from zoneinfo import ZoneInfo


MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "deyecloud"
    / "data.py"
)
SPEC = spec_from_file_location("deyecloud_data", MODULE_PATH)
DATA = module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(DATA)


class DailyBucketTests(unittest.TestCase):
    """Cover the stale-bucket sequence captured in issue #14."""

    def setUp(self):
        self.yesterday = {
            "generationValue": 12.2,
            "consumptionValue": 17.3,
            "gridValue": 0,
            "purchaseValue": 5.1,
            "chargeValue": 0,
            "dischargeValue": 0,
        }
        self.placeholder = DATA.empty_daily_record("2026-07-05")

    def test_rejects_yesterday_bucket_after_old_two_hour_window(self):
        """A placeholder keeps the guard active until real data is published."""
        self.assertTrue(
            DATA.should_reject_stale_today(
                dict(self.yesterday),
                self.yesterday,
                self.placeholder,
                in_midnight_guard=False,
            )
        )

    def test_rejects_slightly_drifted_stale_snapshot(self):
        stale = dict(self.yesterday)
        stale["generationValue"] = 12.1
        stale["consumptionValue"] = 17.1
        self.assertTrue(
            DATA.should_reject_stale_today(
                stale,
                self.yesterday,
                self.placeholder,
                in_midnight_guard=False,
            )
        )

    def test_accepts_genuine_current_day_bucket(self):
        current = {
            "generationValue": 0,
            "consumptionValue": 5.4,
            "gridValue": 0,
            "purchaseValue": 5.4,
            "chargeValue": 0,
            "dischargeValue": 0,
        }
        self.assertFalse(
            DATA.should_reject_stale_today(
                current,
                self.yesterday,
                self.placeholder,
                in_midnight_guard=False,
            )
        )

    def test_stops_extended_guard_after_real_bucket_is_accepted(self):
        accepted_today = {
            "date": "2026-07-05",
            "generationValue": 1.0,
            "consumptionValue": 2.0,
        }
        self.assertFalse(
            DATA.should_reject_stale_today(
                dict(self.yesterday),
                self.yesterday,
                accepted_today,
                in_midnight_guard=False,
            )
        )

    def test_solar_only_station_needs_one_matching_nonzero_counter(self):
        yesterday = {"generationValue": 8.5}
        self.assertTrue(
            DATA.should_reject_stale_today(
                {"generationValue": 8.5},
                yesterday,
                self.placeholder,
                in_midnight_guard=False,
            )
        )

    def test_midday_missing_data_is_unavailable_without_cache(self):
        self.assertIsNone(
            DATA.resolve_today_record(
                "2026-07-05",
                None,
                self.yesterday,
                None,
                in_midnight_guard=False,
            )
        )

    def test_midnight_missing_data_creates_placeholder(self):
        result = DATA.resolve_today_record(
            "2026-07-05",
            None,
            self.yesterday,
            None,
            in_midnight_guard=True,
        )
        self.assertEqual(self.placeholder, result)

    def test_midday_outage_preserves_same_date_cache(self):
        cached = {"date": "2026-07-05", "generationValue": 3.4}
        self.assertIs(
            cached,
            DATA.resolve_today_record(
                "2026-07-05",
                None,
                self.yesterday,
                cached,
                in_midnight_guard=False,
            ),
        )

    def test_recovery_after_missing_data_has_no_synthetic_zero(self):
        missing = DATA.resolve_today_record(
            "2026-07-05",
            None,
            self.yesterday,
            None,
            in_midnight_guard=False,
        )
        recovered = {"date": "2026-07-05", "generationValue": 8.1}
        self.assertIsNone(missing)
        self.assertIs(
            recovered,
            DATA.resolve_today_record(
                "2026-07-05",
                recovered,
                self.yesterday,
                missing,
                in_midnight_guard=False,
            ),
        )

    def test_stale_candidate_preserves_real_cache_during_guard(self):
        cached = {"date": "2026-07-05", "generationValue": 0.5}
        self.assertIs(
            cached,
            DATA.resolve_today_record(
                "2026-07-05",
                dict(self.yesterday),
                self.yesterday,
                cached,
                in_midnight_guard=True,
            ),
        )

    def test_stale_candidate_preserves_placeholder(self):
        self.assertIs(
            self.placeholder,
            DATA.resolve_today_record(
                "2026-07-05",
                dict(self.yesterday),
                self.yesterday,
                self.placeholder,
                in_midnight_guard=True,
            ),
        )


class ApiDateTests(unittest.TestCase):
    """Equivalent instants resolve to the same Home Assistant local date."""

    def test_aware_timestamp_shapes_use_local_timezone(self):
        local_timezone = ZoneInfo("America/Los_Angeles")
        instant = datetime.fromisoformat("2026-07-05T00:30:00+00:00")
        epoch_seconds = int(instant.timestamp())
        expected = datetime(2026, 7, 4).date()

        values = (
            epoch_seconds,
            epoch_seconds * 1000,
            "2026-07-05T00:30:00Z",
            "2026-07-05T02:30:00+02:00",
            instant,
        )
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(
                    expected,
                    DATA.parse_api_date(value, local_timezone),
                )

    def test_plain_date_and_naive_datetime_keep_calendar_date(self):
        local_timezone = ZoneInfo("America/Los_Angeles")
        expected = datetime(2026, 7, 5).date()
        self.assertEqual(
            expected,
            DATA.parse_api_date("2026-07-05", local_timezone),
        )
        self.assertEqual(
            expected,
            DATA.parse_api_date(datetime(2026, 7, 5, 0, 30), local_timezone),
        )


class DeviceBatchTests(unittest.TestCase):
    """The official /device/latest endpoint accepts at most ten serials."""

    def test_splits_more_than_ten_devices_without_losing_order(self):
        serials = [str(index) for index in range(25)]
        batches = DATA.batched_device_serials(serials)
        self.assertEqual([10, 10, 5], [len(batch) for batch in batches])
        self.assertEqual(serials, [serial for batch in batches for serial in batch])


if __name__ == "__main__":
    unittest.main()
