"""
Economic data fetcher — live API with CSV fallback.
Priority:
  1. Try live APIs (Numbeo-style free endpoints, World Bank, REST Countries)
  2. Fall back to synthetic CSV if API fails or city not found
"""
import requests
import pandas as pd
import os

_CACHE = {}  # in-memory cache per session
_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "economic_data.csv")

# ── Load synthetic dataset once ───────────────────────────────────────────────
def _load_csv():
    df = pd.read_csv(_CSV_PATH)
    return {row["city"].lower(): row.to_dict() for _, row in df.iterrows()}

_CSV_DATA = _load_csv()

# ── World Bank API (free, no key needed) ─────────────────────────────────────
WB_COUNTRY_MAP = {
    # city → ISO2 country code for World Bank API
    "delhi":"IN","mumbai":"IN","chennai":"IN","bangalore":"IN","kolkata":"IN",
    "hyderabad":"IN","pune":"IN","ahmedabad":"IN","noida":"IN",
    "dubai":"AE","abu dhabi":"AE","sharjah":"AE","doha":"QA",
    "riyadh":"SA","jeddah":"SA","kuwait city":"KW","muscat":"OM","manama":"BH",
    "los angeles":"US","san francisco":"US","new york":"US","chicago":"US",
    "houston":"US","seattle":"US","boston":"US","miami":"US","dallas":"US",
    "toronto":"CA","vancouver":"CA","montreal":"CA",
    "paris":"FR","madrid":"ES","rome":"IT","barcelona":"ES","vienna":"AT",
    "zurich":"CH","budapest":"HU","athens":"GR","tel aviv":"IL",
    "tokyo":"JP","osaka":"JP","seoul":"KR","beijing":"CN","shanghai":"CN",
    "hong kong":"HK","singapore":"SG","bangkok":"TH","kuala lumpur":"MY",
    "jakarta":"ID","manila":"PH","hanoi":"VN","ho chi minh city":"VN",
    "sydney":"AU","melbourne":"AU","brisbane":"AU","perth":"AU",
    "cairo":"EG","cape town":"ZA","johannesburg":"ZA","nairobi":"KE",
    "lagos":"NG","accra":"GH","casablanca":"MA","addis ababa":"ET",
    "sao paulo":"BR","rio de janeiro":"BR","buenos aires":"AR",
    "santiago":"CL","lima":"PE","bogota":"CO",
}

def _fetch_worldbank_gdp(city_lower: str) -> float | None:
    """Fetch GDP per capita (current USD) from World Bank for the city's country."""
    iso = WB_COUNTRY_MAP.get(city_lower)
    if not iso:
        return None
    url = f"https://api.worldbank.org/v2/country/{iso}/indicator/NY.GDP.PCAP.CD?format=json&mrv=1"
    try:
        r = requests.get(url, timeout=6)
        data = r.json()
        val = data[1][0].get("value")
        return round(float(val), 0) if val else None
    except Exception:
        return None

def _fetch_unemployment(city_lower: str) -> float | None:
    """Fetch unemployment rate from World Bank."""
    iso = WB_COUNTRY_MAP.get(city_lower)
    if not iso:
        return None
    url = f"https://api.worldbank.org/v2/country/{iso}/indicator/SL.UEM.TOTL.ZS?format=json&mrv=1"
    try:
        r = requests.get(url, timeout=6)
        data = r.json()
        val = data[1][0].get("value")
        return round(float(val), 1) if val else None
    except Exception:
        return None

# ── Main public function ──────────────────────────────────────────────────────
def get_economic_data(city_name: str, use_live: bool = True) -> dict:
    """
    Returns full economic data dict for a city.
    Tries live World Bank API first, enriches with CSV data, fills gaps from CSV.

    Returns dict with keys:
      gdp_per_capita_usd, avg_monthly_salary_usd, cost_of_living_index,
      rent_1bhk_usd, meal_cost_usd, transport_monthly_usd,
      unemployment_rate, tech_hub_score, industry_diversity_score,
      affordability_score, job_market_score, overall_livability_v2,
      data_source  ("live_api+csv" | "csv_only")
    """
    city_key = city_name.lower().strip()

    if city_key in _CACHE:
        return _CACHE[city_key]

    # ── Step 1: Start with CSV base ───────────────────────────────────────────
    # fuzzy match — find closest city name in CSV
    base = None
    for k, v in _CSV_DATA.items():
        if city_key in k or k in city_key:
            base = dict(v)
            break

    if base is None:
        # Default fallback for unknown cities
        base = {
            "city": city_name,
            "gdp_per_capita_usd":       3500,
            "avg_monthly_salary_usd":   350,
            "cost_of_living_index":     30.0,
            "rent_1bhk_usd":            180,
            "meal_cost_usd":            2.5,
            "transport_monthly_usd":    15,
            "unemployment_rate":        8.5,
            "tech_hub_score":           4.0,
            "industry_diversity_score": 5.0,
            "affordability_score":      40.0,
            "job_market_score":         35.0,
            "overall_livability_v2":    30.0,
        }

    source = "csv_only"

    # ── Step 2: Try enriching with live World Bank data ───────────────────────
    if use_live:
        gdp_live = _fetch_worldbank_gdp(city_key)
        if gdp_live:
            base["gdp_per_capita_usd"] = int(gdp_live)
            # Re-estimate salary from GDP (city salary ≈ GDP_pc / 12 * urban_premium)
            base["avg_monthly_salary_usd"] = int(gdp_live / 12 * 0.65)
            source = "live_api+csv"

        unemp_live = _fetch_unemployment(city_key)
        if unemp_live:
            base["unemployment_rate"] = unemp_live
            source = "live_api+csv"

    # ── Step 3: Recompute derived scores with updated values ──────────────────
    sal   = base["avg_monthly_salary_usd"]
    cost  = base["cost_of_living_index"]
    unemp = base["unemployment_rate"]
    tech  = base["tech_hub_score"]
    div   = base["industry_diversity_score"]

    base["affordability_score"] = round(min(100, (sal / max(cost, 1)) * 3.5), 1)
    base["job_market_score"]    = round(
        min(100, tech * 0.3 + div * 0.25 + (1 - unemp / 35) * 45), 1
    )
    base["data_source"] = source

    _CACHE[city_key] = base
    return base


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    for city in ["Chennai", "Dubai", "San Francisco", "Lagos", "Zurich"]:
        d = get_economic_data(city, use_live=False)  # use_live=False for offline test
        print(f"{city:20} salary=${d['avg_monthly_salary_usd']:,}  "
              f"cost={d['cost_of_living_index']}  "
              f"afford={d['affordability_score']}  "
              f"jobs={d['job_market_score']}  "
              f"source={d['data_source']}")
