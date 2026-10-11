"""Screen UK startups in a sector using Companies House data and rank them.

Usage:
    export CH_API_KEY=your-key
    python3 screener.py --sector climate --location Oxford

Pass 1 searches active private companies in the sector's SIC codes and checks
each one's capital filings for share allotments (a sign it has raised equity).
Pass 2 looks up directors and owners of the funded companies, scores them
(see scoring.py and config.py) and writes a ranked CSV.
"""
import argparse
import csv
import os
import sys
from datetime import date
from pathlib import Path

import config
import scoring
from companies_house import CompaniesHouseClient

COLUMNS = ["rank", "score", "company_name", "company_number", "incorporated", "age_years",
           "locality", "postcode", "sic_codes", "allotments_24m", "allotments_total",
           "last_allotment", "active_directors", "university_link",
           "pts_funding_momentum", "pts_funding_depth", "pts_stage_fit", "pts_team",
           "pts_university_link", "companies_house_link"]


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def run_screen(client, sector, today, years=10, location=None, max_companies=300):
    """Return (ranked rows, stats). `client` needs the CompaniesHouseClient methods."""
    spec = config.SECTORS[sector]
    start = date(today.year - years, today.month, min(today.day, 28))
    candidates = client.search_companies(spec["sic_codes"], start.isoformat(), today.isoformat(),
                                         location=location)
    log(f"Found {len(candidates)} active {spec['label'].lower()} companies; "
        f"checking funding for up to {max_companies}.")
    candidates = candidates[:max_companies]

    funded = []
    for i, company in enumerate(candidates, 1):
        filings = client.capital_filings(company["company_number"])
        if scoring.allotment_dates(filings):
            funded.append((company, filings))
        if i % 25 == 0:
            log(f"  pass 1: {i}/{len(candidates)} checked, {len(funded)} have raised equity")

    rows = []
    for i, (company, filings) in enumerate(funded, 1):
        number = company["company_number"]
        s = scoring.signals(company, filings, client.officers(number), client.psc(number), today)
        total, parts = scoring.score(s)
        s.update({f"pts_{k}": v for k, v in parts.items()})
        s["score"] = total
        s["companies_house_link"] = f"https://find-and-update.company-information.service.gov.uk/company/{number}"
        rows.append(s)
        if i % 25 == 0:
            log(f"  pass 2: {i}/{len(funded)} scored")

    rows.sort(key=lambda r: r["score"], reverse=True)
    for rank, r in enumerate(rows, 1):
        r["rank"] = rank
    stats = {"found": len(candidates), "funded": len(funded),
             "university_linked": sum(1 for r in rows if r["university_link"])}
    return rows, stats


def write_csv(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def print_top(rows, n):
    print(f"\n{'#':>3}  {'Score':>5}  {'Company':<40} {'Age':>4}  {'Rounds 24m':>10}  University link")
    for r in rows[:n]:
        print(f"{r['rank']:>3}  {r['score']:>5}  {r['company_name'][:40]:<40} {r['age_years']:>4}  "
              f"{r['allotments_24m']:>10}  {r['university_link'][:30]}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sector", choices=sorted(config.SECTORS), default="climate")
    p.add_argument("--location", help="registered office town or postcode area, e.g. Oxford")
    p.add_argument("--years", type=int, default=10, help="only companies incorporated in the last N years")
    p.add_argument("--max-companies", type=int, default=300, help="cap on companies checked in pass 1")
    p.add_argument("--top", type=int, default=15, help="how many to print")
    p.add_argument("--out", default="results", help="folder for the CSV")
    args = p.parse_args(argv)

    key = os.environ.get("CH_API_KEY")
    if not key:
        sys.exit("Set CH_API_KEY to your Companies House API key (free at developer.company-information.service.gov.uk).")

    today = date.today()
    client = CompaniesHouseClient(key)
    rows, stats = run_screen(client, args.sector, today, args.years, args.location, args.max_companies)

    place = f"_{args.location.lower().replace(' ', '-')}" if args.location else ""
    out = Path(args.out) / f"{args.sector}{place}_{today.isoformat()}.csv"
    write_csv(rows, out)
    spec = config.SECTORS[args.sector]
    print(f"{spec['label']} ({spec['sdgs']})")
    print(f"Screened {stats['found']} companies; {stats['funded']} have raised equity; "
          f"{stats['university_linked']} have a university link. API calls: {client.calls}.")
    print_top(rows, args.top)
    print(f"\nFull ranking: {out}")


if __name__ == "__main__":
    main()
