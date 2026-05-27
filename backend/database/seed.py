"""
YieldLens Bond Universe Seeder
Generates 500+ realistic bonds across all types.
"""

import hashlib
import logging
import random
from datetime import datetime, timedelta

logger = logging.getLogger("yieldlens.seed")


def _cusip():
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "".join(random.choice(chars) for _ in range(9))


def _id(name, i):
    return hashlib.md5(f"{name}-{i}".encode()).hexdigest()[:24]


TREASURY_MATURITIES = [
    ("1-Month", 1 / 12),
    ("3-Month", 0.25),
    ("6-Month", 0.5),
    ("1-Year", 1),
    ("2-Year", 2),
    ("3-Year", 3),
    ("5-Year", 5),
    ("7-Year", 7),
    ("10-Year", 10),
    ("20-Year", 20),
    ("30-Year", 30),
]

CORP_ISSUERS = [
    ("Apple Inc.", "AAPL", "Technology", "AA+"),
    ("Microsoft Corp.", "MSFT", "Technology", "AAA"),
    ("Alphabet Inc.", "GOOGL", "Technology", "AA+"),
    ("Amazon.com Inc.", "AMZN", "Technology", "AA"),
    ("Meta Platforms Inc.", "META", "Technology", "AA-"),
    ("NVIDIA Corp.", "NVDA", "Technology", "A+"),
    ("JPMorgan Chase & Co.", "JPM", "Financials", "A+"),
    ("Goldman Sachs Group", "GS", "Financials", "A+"),
    ("Bank of America Corp.", "BAC", "Financials", "A"),
    ("Morgan Stanley", "MS", "Financials", "A"),
    ("Citigroup Inc.", "C", "Financials", "A-"),
    ("Wells Fargo & Co.", "WFC", "Financials", "A"),
    ("Johnson & Johnson", "JNJ", "Healthcare", "AAA"),
    ("Pfizer Inc.", "PFE", "Healthcare", "A+"),
    ("UnitedHealth Group", "UNH", "Healthcare", "A+"),
    ("Abbott Laboratories", "ABT", "Healthcare", "AA-"),
    ("Eli Lilly & Co.", "LLY", "Healthcare", "A+"),
    ("Procter & Gamble Co.", "PG", "Consumer Staples", "AA-"),
    ("Coca-Cola Co.", "KO", "Consumer Staples", "A+"),
    ("PepsiCo Inc.", "PEP", "Consumer Staples", "A+"),
    ("Walmart Inc.", "WMT", "Consumer Staples", "AA"),
    ("Costco Wholesale", "COST", "Consumer Staples", "A+"),
    ("Exxon Mobil Corp.", "XOM", "Energy", "AA-"),
    ("Chevron Corp.", "CVX", "Energy", "AA-"),
    ("ConocoPhillips", "COP", "Energy", "A"),
    ("AT&T Inc.", "T", "Communication Services", "BBB"),
    ("Verizon Communications", "VZ", "Communication Services", "BBB+"),
    ("Walt Disney Co.", "DIS", "Communication Services", "A-"),
    ("Caterpillar Inc.", "CAT", "Industrials", "A"),
    ("Honeywell International", "HON", "Industrials", "A"),
    ("3M Company", "MMM", "Industrials", "A+"),
    ("Union Pacific Corp.", "UNP", "Industrials", "A"),
    ("Boeing Co.", "BA", "Industrials", "BBB-"),
    ("Lockheed Martin", "LMT", "Industrials", "A-"),
    ("Duke Energy Corp.", "DUK", "Utilities", "A-"),
    ("Southern Company", "SO", "Utilities", "A-"),
    ("NextEra Energy", "NEE", "Utilities", "A-"),
    ("Dominion Energy", "D", "Utilities", "BBB+"),
    ("American Tower Corp.", "AMT", "Real Estate", "BBB+"),
    ("Prologis Inc.", "PLD", "Real Estate", "A"),
    ("Simon Property Group", "SPG", "Real Estate", "A-"),
    ("Ford Motor Co.", "F", "Consumer Discretionary", "BB+"),
    ("General Motors Co.", "GM", "Consumer Discretionary", "BBB"),
    ("Tesla Inc.", "TSLA", "Consumer Discretionary", "BBB-"),
    ("Home Depot Inc.", "HD", "Consumer Discretionary", "A"),
    ("Nike Inc.", "NKE", "Consumer Discretionary", "AA-"),
]

HY_ISSUERS = [
    ("Carnival Corp.", "CCL", "Consumer Discretionary", "B+"),
    ("AMC Entertainment", "AMC", "Communication Services", "CCC+"),
    ("Bed Bath & Beyond", "BBBY", "Consumer Discretionary", "CCC"),
    ("Gap Inc.", "GPS", "Consumer Discretionary", "BB-"),
    ("Macy's Inc.", "M", "Consumer Discretionary", "BB+"),
    ("Occidental Petroleum", "OXY", "Energy", "BB+"),
    ("Spirit Airlines", "SAVE", "Industrials", "B-"),
    ("Dish Network", "DISH", "Communication Services", "B-"),
    ("Carvana Co.", "CVNA", "Consumer Discretionary", "CCC+"),
    ("Community Health Systems", "CYH", "Healthcare", "CCC+"),
]

MUNI_ISSUERS = [
    ("State of California", "CA", "General Obligation"),
    ("State of New York", "NY", "General Obligation"),
    ("State of Texas", "TX", "General Obligation"),
    ("State of Florida", "FL", "General Obligation"),
    ("State of Illinois", "IL", "General Obligation"),
    ("City of Chicago", "IL", "Revenue"),
    ("City of Los Angeles", "CA", "Revenue"),
    ("City of New York", "NY", "Revenue"),
    ("State of New Jersey", "NJ", "General Obligation"),
    ("State of Pennsylvania", "PA", "General Obligation"),
    ("State of Massachusetts", "MA", "General Obligation"),
    ("State of Ohio", "OH", "General Obligation"),
    ("State of Georgia", "GA", "General Obligation"),
    ("State of Virginia", "VA", "General Obligation"),
    ("State of Washington", "WA", "General Obligation"),
    ("MTA New York", "NY", "Revenue"),
    ("LA Dept Water & Power", "CA", "Revenue"),
    ("Bay Area Toll Authority", "CA", "Revenue"),
    ("Port Authority NY/NJ", "NY", "Revenue"),
    ("Chicago O'Hare Airport", "IL", "Revenue"),
    ("State of Michigan", "MI", "General Obligation"),
    ("State of Arizona", "AZ", "General Obligation"),
    ("State of Colorado", "CO", "General Obligation"),
    ("State of Maryland", "MD", "General Obligation"),
    ("State of Connecticut", "CT", "General Obligation"),
]

BOND_ETFS = [
    ("iShares Core U.S. Aggregate Bond ETF", "AGG", 87.50, 3.85),
    ("Vanguard Total Bond Market ETF", "BND", 72.10, 3.92),
    ("iShares 20+ Year Treasury Bond ETF", "TLT", 95.30, 4.45),
    ("iShares iBoxx $ Investment Grade Corporate Bond ETF", "LQD", 108.20, 4.65),
    ("iShares iBoxx $ High Yield Corporate Bond ETF", "HYG", 77.80, 6.20),
    ("iShares National Muni Bond ETF", "MUB", 107.50, 3.15),
    ("iShares 1-3 Year Treasury Bond ETF", "SHY", 82.10, 4.50),
    ("iShares 7-10 Year Treasury Bond ETF", "IEF", 93.40, 4.25),
    ("iShares TIPS Bond ETF", "TIP", 105.60, 2.35),
    ("Vanguard Short-Term Corporate Bond ETF", "VCSH", 77.30, 4.55),
    ("SPDR Bloomberg High Yield Bond ETF", "JNK", 94.50, 6.35),
    ("Vanguard Intermediate-Term Corporate Bond ETF", "VCIT", 81.20, 4.70),
    ("iShares 0-3 Month Treasury Bond ETF", "SGOV", 100.05, 5.25),
    ("Vanguard Long-Term Corporate Bond ETF", "VCLT", 78.60, 5.10),
    ("SPDR Bloomberg 1-3 Month T-Bill ETF", "BIL", 91.50, 5.20),
]


def generate_bonds():
    """Generate 500+ realistic bonds."""
    random.seed(42)
    bonds = []
    now = datetime.utcnow()
    idx = 0

    # === TREASURY BONDS (55 bonds: 5 per maturity) ===
    for mat_name, mat_years in TREASURY_MATURITIES:
        for series in range(5):
            idx += 1
            coupon = round(random.uniform(1.5, 5.5), 3)
            price = round(random.uniform(92, 108), 4)
            issue_offset = random.randint(30, 365 * 2)
            maturity_offset = int(mat_years * 365)
            bonds.append(
                {
                    "_id": _id("UST", idx),
                    "cusip": _cusip(),
                    "issuer": "U.S. Treasury",
                    "ticker": "UST",
                    "name": f"U.S. Treasury {mat_name} {coupon:.3f}% {(now + timedelta(days=maturity_offset)).strftime('%m/%Y')}",
                    "type": "treasury",
                    "subtype": mat_name,
                    "coupon_rate": coupon,
                    "maturity_date": (
                        now + timedelta(days=maturity_offset)
                    ).isoformat(),
                    "issue_date": (now - timedelta(days=issue_offset)).isoformat(),
                    "face_value": 1000,
                    "price": price,
                    "currency": "USD",
                    "sector": "Government",
                    "country": "US",
                    "state": None,
                    "rating": "AAA",
                    "callable": False,
                    "tax_exempt": False,
                    "frequency": 2,
                }
            )

    # === CORPORATE INVESTMENT GRADE (180 bonds: ~4 per issuer) ===
    for issuer_name, ticker, sector, rating in CORP_ISSUERS:
        for series in range(4):
            idx += 1
            mat_years = random.choice([2, 3, 5, 7, 10, 15, 20, 30])
            coupon = round(random.uniform(2.5, 6.5), 3)
            price = round(random.uniform(88, 112), 4)
            bonds.append(
                {
                    "_id": _id("CORP", idx),
                    "cusip": _cusip(),
                    "issuer": issuer_name,
                    "ticker": ticker,
                    "name": f"{issuer_name} {coupon:.3f}% {(now + timedelta(days=mat_years*365)).strftime('%m/%Y')}",
                    "type": "corporate",
                    "subtype": "investment_grade",
                    "coupon_rate": coupon,
                    "maturity_date": (
                        now + timedelta(days=mat_years * 365)
                    ).isoformat(),
                    "issue_date": (
                        now - timedelta(days=random.randint(60, 365 * 3))
                    ).isoformat(),
                    "face_value": 1000,
                    "price": price,
                    "currency": "USD",
                    "sector": sector,
                    "country": "US",
                    "state": None,
                    "rating": rating,
                    "callable": random.random() > 0.6,
                    "tax_exempt": False,
                    "frequency": 2,
                }
            )

    # === HIGH YIELD (50 bonds: 5 per issuer) ===
    for issuer_name, ticker, sector, rating in HY_ISSUERS:
        for series in range(5):
            idx += 1
            mat_years = random.choice([3, 5, 7, 10])
            coupon = round(random.uniform(5.5, 10.0), 3)
            price = round(random.uniform(70, 102), 4)
            bonds.append(
                {
                    "_id": _id("HY", idx),
                    "cusip": _cusip(),
                    "issuer": issuer_name,
                    "ticker": ticker,
                    "name": f"{issuer_name} {coupon:.3f}% {(now + timedelta(days=mat_years*365)).strftime('%m/%Y')}",
                    "type": "corporate",
                    "subtype": "high_yield",
                    "coupon_rate": coupon,
                    "maturity_date": (
                        now + timedelta(days=mat_years * 365)
                    ).isoformat(),
                    "issue_date": (
                        now - timedelta(days=random.randint(30, 365 * 2))
                    ).isoformat(),
                    "face_value": 1000,
                    "price": price,
                    "currency": "USD",
                    "sector": sector,
                    "country": "US",
                    "state": None,
                    "rating": rating,
                    "callable": random.random() > 0.4,
                    "tax_exempt": False,
                    "frequency": 2,
                }
            )

    # === MUNICIPAL BONDS (125 bonds: 5 per issuer) ===
    for issuer_name, state, subtype in MUNI_ISSUERS:
        for series in range(5):
            idx += 1
            mat_years = random.choice([5, 7, 10, 15, 20, 25, 30])
            coupon = round(random.uniform(2.0, 5.0), 3)
            price = round(random.uniform(95, 110), 4)
            rating = random.choice(
                ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB"]
            )
            bonds.append(
                {
                    "_id": _id("MUNI", idx),
                    "cusip": _cusip(),
                    "issuer": issuer_name,
                    "ticker": f"MUNI-{state}",
                    "name": f"{issuer_name} {subtype} {coupon:.3f}% {(now + timedelta(days=mat_years*365)).strftime('%m/%Y')}",
                    "type": "municipal",
                    "subtype": subtype.lower().replace(" ", "_"),
                    "coupon_rate": coupon,
                    "maturity_date": (
                        now + timedelta(days=mat_years * 365)
                    ).isoformat(),
                    "issue_date": (
                        now - timedelta(days=random.randint(60, 365 * 5))
                    ).isoformat(),
                    "face_value": 5000,
                    "price": price,
                    "currency": "USD",
                    "sector": "Municipal",
                    "country": "US",
                    "state": state,
                    "rating": rating,
                    "callable": random.random() > 0.3,
                    "tax_exempt": True,
                    "frequency": 2,
                }
            )

    # === TIPS (20 bonds) ===
    for series in range(20):
        idx += 1
        mat_years = random.choice([5, 10, 20, 30])
        coupon = round(random.uniform(0.125, 2.5), 3)
        price = round(random.uniform(96, 110), 4)
        bonds.append(
            {
                "_id": _id("TIPS", idx),
                "cusip": _cusip(),
                "issuer": "U.S. Treasury",
                "ticker": "TIPS",
                "name": f"U.S. TIPS {coupon:.3f}% {(now + timedelta(days=mat_years*365)).strftime('%m/%Y')}",
                "type": "tips",
                "subtype": f"{mat_years}Y TIPS",
                "coupon_rate": coupon,
                "maturity_date": (now + timedelta(days=mat_years * 365)).isoformat(),
                "issue_date": (
                    now - timedelta(days=random.randint(30, 365 * 3))
                ).isoformat(),
                "face_value": 1000,
                "price": price,
                "currency": "USD",
                "sector": "Government",
                "country": "US",
                "state": None,
                "rating": "AAA",
                "callable": False,
                "tax_exempt": False,
                "frequency": 2,
            }
        )

    # === BOND ETFs (15 bonds) ===
    for etf_name, ticker, nav, dist_yield in BOND_ETFS:
        idx += 1
        bonds.append(
            {
                "_id": _id("ETF", idx),
                "cusip": _cusip(),
                "issuer": etf_name.split(" ")[0] + " " + etf_name.split(" ")[1],
                "ticker": ticker,
                "name": etf_name,
                "type": "bond_etf",
                "subtype": "etf",
                "coupon_rate": dist_yield,
                "maturity_date": None,
                "issue_date": (
                    now - timedelta(days=random.randint(365 * 3, 365 * 15))
                ).isoformat(),
                "face_value": None,
                "price": nav,
                "currency": "USD",
                "sector": "Multi-Sector",
                "country": "US",
                "state": None,
                "rating": "N/A",
                "callable": False,
                "tax_exempt": False,
                "frequency": 12,
            }
        )

    # === PREFERRED STOCKS (20 bonds) ===
    pref_issuers = [
        ("Bank of America Corp.", "BAC", "Financials"),
        ("JPMorgan Chase & Co.", "JPM", "Financials"),
        ("Wells Fargo & Co.", "WFC", "Financials"),
        ("AT&T Inc.", "T", "Communication Services"),
        ("Duke Energy Corp.", "DUK", "Utilities"),
    ]
    for issuer_name, ticker, sector in pref_issuers:
        for series in range(4):
            idx += 1
            coupon = round(random.uniform(4.5, 7.5), 3)
            price = round(random.uniform(20, 28), 2)
            bonds.append(
                {
                    "_id": _id("PREF", idx),
                    "cusip": _cusip(),
                    "issuer": issuer_name,
                    "ticker": f"{ticker}.PR{chr(65+series)}",
                    "name": f"{issuer_name} Series {chr(65+series)} Preferred {coupon:.3f}%",
                    "type": "preferred",
                    "subtype": f"series_{chr(97+series)}",
                    "coupon_rate": coupon,
                    "maturity_date": None,
                    "issue_date": (
                        now - timedelta(days=random.randint(365, 365 * 8))
                    ).isoformat(),
                    "face_value": 25,
                    "price": price,
                    "currency": "USD",
                    "sector": sector,
                    "country": "US",
                    "state": None,
                    "rating": random.choice(["BBB+", "BBB", "BBB-", "BB+"]),
                    "callable": True,
                    "tax_exempt": False,
                    "frequency": 4,
                }
            )

    # === CDs (20 bonds) ===
    cd_banks = [
        "Ally Bank",
        "Marcus by Goldman Sachs",
        "Capital One",
        "Discover Bank",
        "Synchrony Bank",
        "Barclays",
        "CIT Bank",
        "American Express Bank",
        "Bread Financial",
        "Sallie Mae Bank",
    ]
    for bank in cd_banks:
        for term in [1, 2]:
            idx += 1
            mat_years = random.choice([0.5, 1, 2, 3, 5])
            apy = round(random.uniform(4.0, 5.5), 2)
            bonds.append(
                {
                    "_id": _id("CD", idx),
                    "cusip": _cusip(),
                    "issuer": bank,
                    "ticker": "CD",
                    "name": f"{bank} {mat_years}Y CD {apy}% APY",
                    "type": "cd",
                    "subtype": f"{mat_years}Y",
                    "coupon_rate": apy,
                    "maturity_date": (
                        now + timedelta(days=int(mat_years * 365))
                    ).isoformat(),
                    "issue_date": now.isoformat(),
                    "face_value": 1000,
                    "price": 100.0,
                    "currency": "USD",
                    "sector": "Banking",
                    "country": "US",
                    "state": None,
                    "rating": "N/A",
                    "callable": False,
                    "tax_exempt": False,
                    "frequency": 1 if mat_years <= 1 else 2,
                }
            )

    # === MONEY MARKET (10 bonds) ===
    mm_funds = [
        "Vanguard Federal Money Market",
        "Fidelity Government Money Market",
        "Schwab Value Advantage Money",
        "JPMorgan Prime Money Market",
        "BlackRock Liquidity FedFund",
        "Goldman Sachs FS Government",
        "American Century Capital Preservation",
        "T. Rowe Price Government Money",
        "USAA Money Market Fund",
        "Invesco Government Money Market",
    ]
    for fund in mm_funds:
        idx += 1
        seven_day = round(random.uniform(4.8, 5.4), 2)
        bonds.append(
            {
                "_id": _id("MM", idx),
                "cusip": _cusip(),
                "issuer": fund.split(" ")[0],
                "ticker": "MMF",
                "name": fund,
                "type": "money_market",
                "subtype": "government",
                "coupon_rate": seven_day,
                "maturity_date": None,
                "issue_date": (
                    now - timedelta(days=random.randint(365 * 5, 365 * 20))
                ).isoformat(),
                "face_value": 1,
                "price": 1.00,
                "currency": "USD",
                "sector": "Money Market",
                "country": "US",
                "state": None,
                "rating": "AAA",
                "callable": False,
                "tax_exempt": False,
                "frequency": 365,
            }
        )

    random.shuffle(bonds)
    return bonds


def seed_database(db):
    """Seed the database with bonds and sample user data."""
    bonds_coll = db["bonds"]
    users_coll = db["users"]
    portfolios_coll = db["portfolios"]
    watchlists_coll = db["watchlists"]

    if bonds_coll.count_documents({}) > 0:
        logger.info(
            f"Database already seeded ({bonds_coll.count_documents({})} bonds). Skipping."
        )
        return

    logger.info("Generating bond universe...")
    bonds = generate_bonds()
    bonds_coll.insert_many(bonds)
    logger.info(f"Inserted {len(bonds)} bonds.")

    # Sample user
    import bcrypt

    password_hash = bcrypt.hashpw("demo123".encode(), bcrypt.gensalt()).decode()
    sample_user = {
        "_id": "demo_user_001",
        "email": "demo@yieldlens.com",
        "name": "Demo User",
        "password_hash": password_hash,
        "created_at": datetime.utcnow().isoformat(),
        "settings": {
            "theme": "dark",
            "default_currency": "USD",
            "tax_bracket": 0.32,
        },
    }
    users_coll.replace_one({"_id": sample_user["_id"]}, sample_user, upsert=True)
    logger.info("Created demo user (demo@yieldlens.com / demo123)")

    # Sample portfolio
    bond_ids = [b["_id"] for b in bonds[:5]]
    sample_portfolio = {
        "_id": "demo_portfolio_001",
        "user_id": "demo_user_001",
        "name": "Core Fixed Income Portfolio",
        "created_at": datetime.utcnow().isoformat(),
        "holdings": [
            {
                "bond_id": bond_ids[0],
                "quantity": 10,
                "avg_price": 98.50,
                "added_at": datetime.utcnow().isoformat(),
            },
            {
                "bond_id": bond_ids[1],
                "quantity": 5,
                "avg_price": 102.25,
                "added_at": datetime.utcnow().isoformat(),
            },
            {
                "bond_id": bond_ids[2],
                "quantity": 20,
                "avg_price": 95.00,
                "added_at": datetime.utcnow().isoformat(),
            },
            {
                "bond_id": bond_ids[3],
                "quantity": 15,
                "avg_price": 100.50,
                "added_at": datetime.utcnow().isoformat(),
            },
            {
                "bond_id": bond_ids[4],
                "quantity": 8,
                "avg_price": 105.75,
                "added_at": datetime.utcnow().isoformat(),
            },
        ],
    }
    portfolios_coll.replace_one(
        {"_id": sample_portfolio["_id"]}, sample_portfolio, upsert=True
    )
    logger.info("Created sample portfolio with 5 holdings")

    # Sample watchlist
    sample_watchlist = {
        "_id": "demo_watchlist_001",
        "user_id": "demo_user_001",
        "name": "Rate Movers Watch",
        "created_at": datetime.utcnow().isoformat(),
        "bonds": [
            {"bond_id": bond_ids[0], "added_at": datetime.utcnow().isoformat()},
            {"bond_id": bond_ids[2], "added_at": datetime.utcnow().isoformat()},
            {"bond_id": bond_ids[4], "added_at": datetime.utcnow().isoformat()},
        ],
    }
    watchlists_coll.replace_one(
        {"_id": sample_watchlist["_id"]}, sample_watchlist, upsert=True
    )
    logger.info("Created sample watchlist")
    logger.info("Database seeding complete!")
