"""Turn raw Companies House records into signals and a 0-100 score."""
from datetime import date

import config


def _parse(d):
    return date.fromisoformat(d) if d else None


def years_between(start, end):
    return (end - start).days / 365.25


def allotment_dates(capital_filings):
    """Dates of SH01 filings (return of allotment of shares), a sign of a funding round."""
    return sorted(_parse(f["date"]) for f in capital_filings
                  if f.get("type") == "SH01" and f.get("date"))


def active_directors(officers):
    return sum(1 for o in officers
               if "director" in o.get("officer_role", "") and not o.get("resigned_on"))


def university_link(psc_items, officers):
    """First owner or officer name that suggests a university connection, else ''."""
    names = [p.get("name", "") for p in psc_items if not p.get("ceased_on")]
    names += [o.get("name", "") for o in officers if not o.get("resigned_on")]
    for name in names:
        upper = name.upper()
        if any(key in upper for key in config.UNIVERSITY_LINK_NAMES):
            return name
    return ""


def stage_fit(age_years):
    """1.0 inside the growth band, tapering linearly to 0 at age 0 and at AGE_ZERO_AT."""
    lo, hi = config.GROWTH_BAND
    if age_years <= 0 or age_years >= config.AGE_ZERO_AT:
        return 0.0
    if age_years < lo:
        return age_years / lo
    if age_years <= hi:
        return 1.0
    return (config.AGE_ZERO_AT - age_years) / (config.AGE_ZERO_AT - hi)


def signals(company, capital_filings, officers, psc_items, today):
    allotments = allotment_dates(capital_filings)
    recent = [d for d in allotments if years_between(d, today) <= 2]
    incorporated = _parse(company.get("date_of_creation"))
    address = company.get("registered_office_address") or {}
    return {
        "company_name": company.get("company_name", ""),
        "company_number": company.get("company_number", ""),
        "incorporated": incorporated.isoformat() if incorporated else "",
        "age_years": round(years_between(incorporated, today), 1) if incorporated else 0.0,
        "sic_codes": " ".join(company.get("sic_codes") or []),
        "locality": address.get("locality", ""),
        "postcode": address.get("postal_code", ""),
        "allotments_24m": len(recent),
        "allotments_total": len(allotments),
        "last_allotment": allotments[-1].isoformat() if allotments else "",
        "active_directors": active_directors(officers),
        "university_link": university_link(psc_items, officers),
    }


def score(s):
    """Weighted score out of 100, plus the points from each signal."""
    w = config.WEIGHTS
    parts = {
        "funding_momentum": w["funding_momentum"] * min(s["allotments_24m"], config.MOMENTUM_CAP) / config.MOMENTUM_CAP,
        "funding_depth": w["funding_depth"] * min(s["allotments_total"], config.DEPTH_CAP) / config.DEPTH_CAP,
        "stage_fit": w["stage_fit"] * stage_fit(s["age_years"]),
        "team": w["team"] * min(s["active_directors"], config.TEAM_CAP) / config.TEAM_CAP,
        "university_link": w["university_link"] * (1 if s["university_link"] else 0),
    }
    return round(sum(parts.values()), 1), {k: round(v, 1) for k, v in parts.items()}
