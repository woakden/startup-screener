"""Minimal client for the Companies House public data API (standard library only).

Get a free API key at https://developer.company-information.service.gov.uk/
The API allows 600 requests per 5 minutes, so calls are spaced out and a
429 (rate limited) response waits and retries.
"""
import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://api.company-information.service.gov.uk"


class CompaniesHouseClient:
    def __init__(self, api_key, min_interval=0.55, max_retries=5):
        token = base64.b64encode(f"{api_key}:".encode()).decode()
        self._auth = f"Basic {token}"
        self._min_interval = min_interval
        self._max_retries = max_retries
        self._last_call = 0.0
        self.calls = 0

    def _get(self, path, params=None):
        url = BASE_URL + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        for attempt in range(self._max_retries):
            wait = self._min_interval - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()
            self.calls += 1
            req = urllib.request.Request(url, headers={"Authorization": self._auth})
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.load(resp)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return {}
                if e.code == 429:
                    time.sleep(30 * (attempt + 1))
                    continue
                if e.code == 401:
                    raise SystemExit("Companies House rejected the API key (401). Check CH_API_KEY.")
                raise
        raise RuntimeError(f"Gave up after {self._max_retries} rate-limited attempts: {path}")

    def search_companies(self, sic_codes, incorporated_from, incorporated_to, location=None, limit=5000):
        """Active private limited companies with any of the SIC codes, incorporated in the window."""
        params = {
            "sic_codes": ",".join(sic_codes),
            "company_status": "active",
            "company_type": "ltd",
            "incorporated_from": incorporated_from,
            "incorporated_to": incorporated_to,
            "size": min(limit, 5000),
        }
        if location:
            params["location"] = location
        return self._get("/advanced-search/companies", params).get("items", [])[:limit]

    def capital_filings(self, number):
        return self._get(f"/company/{number}/filing-history",
                         {"category": "capital", "items_per_page": 100}).get("items", [])

    def officers(self, number):
        return self._get(f"/company/{number}/officers", {"items_per_page": 100}).get("items", [])

    def psc(self, number):
        return self._get(f"/company/{number}/persons-with-significant-control",
                         {"items_per_page": 100}).get("items", [])
