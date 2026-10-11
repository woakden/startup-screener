"""Tests with made-up companies (no network). Run: python3 -m unittest discover tests"""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scoring  # noqa: E402
from screener import run_screen  # noqa: E402

TODAY = date(2026, 10, 11)


def sh01(d):
    return {"type": "SH01", "date": d}


class FakeClient:
    """Stands in for CompaniesHouseClient with fictional test data."""

    companies = [
        {"company_name": "TEST GROWTH LTD", "company_number": "T0000001", "date_of_creation": "2020-03-01",
         "sic_codes": ["72190"], "registered_office_address": {"locality": "Oxford", "postal_code": "OX1 1AA"}},
        {"company_name": "TEST SEED LTD", "company_number": "T0000002", "date_of_creation": "2025-06-01",
         "sic_codes": ["35110"], "registered_office_address": {"locality": "Leeds"}},
        {"company_name": "TEST UNFUNDED LTD", "company_number": "T0000003", "date_of_creation": "2019-01-01",
         "sic_codes": ["27200"]},
    ]
    filings = {
        "T0000001": [sh01("2026-05-01"), sh01("2025-11-01"), sh01("2023-01-15"), {"type": "SH19", "date": "2022-01-01"}],
        "T0000002": [sh01("2025-09-01")],
        "T0000003": [],
    }
    officer_data = {
        "T0000001": [{"name": "A DIRECTOR", "officer_role": "director"},
                     {"name": "B DIRECTOR", "officer_role": "director"},
                     {"name": "C FORMER", "officer_role": "director", "resigned_on": "2024-01-01"},
                     {"name": "D SECRETARY", "officer_role": "secretary"}],
        "T0000002": [{"name": "E DIRECTOR", "officer_role": "director"}],
    }
    psc_data = {"T0000001": [{"name": "Test University Innovation Limited"}]}

    def __init__(self):
        self.calls = 0

    def search_companies(self, sic_codes, incorporated_from, incorporated_to, location=None):
        return list(self.companies)

    def capital_filings(self, n):
        return self.filings.get(n, [])

    def officers(self, n):
        return self.officer_data.get(n, [])

    def psc(self, n):
        return self.psc_data.get(n, [])


class ScoringTests(unittest.TestCase):
    def test_counts_only_sh01_allotments(self):
        self.assertEqual(len(scoring.allotment_dates(FakeClient.filings["T0000001"])), 3)

    def test_ignores_resigned_and_non_directors(self):
        self.assertEqual(scoring.active_directors(FakeClient.officer_data["T0000001"]), 2)

    def test_university_link_found_in_owners(self):
        self.assertEqual(scoring.university_link(FakeClient.psc_data["T0000001"], []),
                         "Test University Innovation Limited")

    def test_ceased_owner_does_not_count(self):
        self.assertEqual(scoring.university_link([{"name": "University X", "ceased_on": "2020-01-01"}], []), "")

    def test_stage_fit_shape(self):
        self.assertEqual(scoring.stage_fit(5), 1.0)
        self.assertAlmostEqual(scoring.stage_fit(1.5), 0.5)
        self.assertEqual(scoring.stage_fit(20), 0.0)

    def test_score_never_exceeds_100(self):
        s = {"allotments_24m": 10, "allotments_total": 20, "age_years": 5,
             "active_directors": 9, "university_link": "UNIVERSITY"}
        total, _ = scoring.score(s)
        self.assertEqual(total, 100)


class PipelineTests(unittest.TestCase):
    def test_ranks_funded_companies_only(self):
        rows, stats = run_screen(FakeClient(), "climate", TODAY)
        self.assertEqual(stats, {"found": 3, "funded": 2, "university_linked": 1})
        self.assertEqual([r["company_number"] for r in rows], ["T0000001", "T0000002"])
        self.assertEqual(rows[0]["rank"], 1)
        self.assertEqual(rows[0]["allotments_24m"], 2)
        self.assertGreater(rows[0]["score"], rows[1]["score"])


if __name__ == "__main__":
    unittest.main()
