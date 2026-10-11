# Startup screener

A Python tool that screens UK startups in a chosen sector using free Companies House data, then ranks them the way a venture capital analyst might at the first screening stage.

It looks for active private companies in a sector's SIC codes and asks three questions of each:

1. **Has it raised equity, and recently?** Each new share issue is filed with Companies House as an SH01 (return of allotment of shares), so SH01 filings are a public signal of funding rounds.
2. **Is it at growth stage?** Companies aged 3 to 8 years score highest.
3. **Who is behind it?** It counts active directors, and flags a university link when a university or university-backed investor appears among the company's owners or officers, a common sign of a spinout.

Sectors are mapped to the UN Sustainable Development Goals (climate tech to SDG 7 and 13, health to SDG 3), in line with impact investing.

## How the score works

Each company gets up to 100 points (weights are in `config.py`):

| Signal | Points | Full marks at |
|---|---|---|
| Funding momentum: share allotments in the last 24 months | 35 | 4 or more |
| Funding depth: share allotments since incorporation | 15 | 8 or more |
| Stage fit: company age | 20 | 3 to 8 years, tapering to 0 at 0 and 15 years |
| Team: active directors | 15 | 5 or more |
| University link | 15 | any match |

Only companies that have raised equity at least once are ranked.

## Running it

1. Get a free API key: register at <https://developer.company-information.service.gov.uk/>, create an application, and add a REST API key.
2. In Terminal, from this folder:

```bash
export CH_API_KEY=your-key
python3 screener.py --sector climate --location Oxford
```

Options: `--sector climate|health`, `--location` (town or postcode area), `--years` (incorporated in the last N years, default 10), `--max-companies` (cap on companies checked, default 300), `--top` (rows to print).

It prints a summary and the top companies, and saves the full ranking to `results/` as a CSV with each company's signals, points breakdown and Companies House link. No extra packages are needed: it uses only the Python standard library.

## Tests

```bash
python3 -m unittest discover tests
```

The tests use made-up companies, so they run without an API key.

## Limitations

- SIC codes describe what a company says it does, so some results will not be genuine climate or health innovators. The ranked list is a starting point for research, not a verdict.
- An SH01 shows that shares were issued, not how much was raised or from whom.
- The university-link check matches names, so it misses spinouts where the university holds a small stake that is not reported.
- The API allows 600 requests per 5 minutes, so the tool spaces out calls and checks at most `--max-companies` companies per run.
