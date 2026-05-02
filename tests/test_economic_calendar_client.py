from __future__ import annotations

from unittest import TestCase

from investbot.data_sources.economic_calendar import FmpEconomicCalendarClient


class EconomicCalendarClientTests(TestCase):
    def test_parse_events_handles_common_fmp_shape(self) -> None:
        client = FmpEconomicCalendarClient(api_keys="")

        events = client._parse_events(
            [
                {
                    "date": "2026-05-06 18:00:00",
                    "country": "US",
                    "event": "FOMC Statement",
                    "impact": "high",
                },
                {
                    "date": "2026-05-07",
                    "country": "US",
                    "event": "Initial Jobless Claims",
                    "impact": "medium",
                },
            ]
        )

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].title, "FOMC Statement")
        self.assertEqual(events[0].country, "US")
        self.assertEqual(events[0].impact, "high")
