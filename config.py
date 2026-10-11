"""Screening settings: sectors, scoring weights and university-link names.

Edit this file to change what the screener looks for. Nothing else needs to change.
"""

# Each sector maps to UK SIC 2007 codes (the activity codes companies give
# Companies House) and the UN Sustainable Development Goals it serves.
# SIC codes are a rough proxy: they say what a company does, not how novel it is.
SECTORS = {
    "climate": {
        "label": "Climate tech",
        "sic_codes": [
            "27110",  # Manufacture of electric motors, generators and transformers
            "27200",  # Manufacture of batteries and accumulators
            "28250",  # Manufacture of non-domestic cooling and ventilation equipment (incl. heat pumps)
            "35110",  # Production of electricity
            "38320",  # Recovery of sorted materials
            "72190",  # Other research and experimental development on natural sciences and engineering
        ],
        "sdgs": "SDG 7 (Affordable and clean energy), SDG 13 (Climate action)",
    },
    "health": {
        "label": "Health and life sciences",
        "sic_codes": [
            "21100",  # Manufacture of basic pharmaceutical products
            "21200",  # Manufacture of pharmaceutical preparations
            "32500",  # Manufacture of medical and dental instruments and supplies
            "72110",  # Research and experimental development on biotechnology
        ],
        "sdgs": "SDG 3 (Good health and well-being)",
    },
}

# Points available for each signal. They add up to 100.
WEIGHTS = {
    "funding_momentum": 35,  # share allotments (SH01) in the last 24 months
    "funding_depth": 15,     # share allotments since incorporation
    "stage_fit": 20,         # company age: growth stage scores highest
    "team": 15,              # number of active directors
    "university_link": 15,   # a university or university-backed investor among owners/officers
}

# Caps: a company at or above the cap gets full marks for that signal.
MOMENTUM_CAP = 4   # allotments in 24 months
DEPTH_CAP = 8      # allotments ever
TEAM_CAP = 5       # active directors

# Ages (years) that count as growth stage. Full marks inside the band,
# tapering to zero at 0 years and at AGE_ZERO_AT years.
GROWTH_BAND = (3, 8)
AGE_ZERO_AT = 15

# Names that suggest a university spinout when they appear among a company's
# persons with significant control or officers. Matching is case-insensitive
# and on substrings, so "UNIVERSITY" catches "University of Oxford" etc.
UNIVERSITY_LINK_NAMES = [
    "UNIVERSITY",
    "IMPERIAL COLLEGE",
    "OXFORD SCIENCE ENTERPRISES",
    "CAMBRIDGE ENTERPRISE",
    "CAMBRIDGE INNOVATION CAPITAL",
    "UCL BUSINESS",
    "IP2IPO",
    "PARKWALK",
    "NORTHERN GRITSTONE",
]
