"""
Global Search Routes
Implements high-speed terminal search with fuzzy matching, autocomplete suggestions, and category routing.
"""

import re
from difflib import SequenceMatcher

from database.mongo import get_db
from flask import Blueprint, jsonify, request

search_bp = Blueprint("search", __name__, url_prefix="/api/v1/search")


def fuzzy_match(s1: str, s2: str) -> float:
    """Return a matching ratio between s1 and s2 for fuzzy searches."""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


@search_bp.route("/global", methods=["POST"])
def global_search():
    """
    Search across Bonds, Issuers, CUSIPs, Portfolios, News, Watchlists, and Macro indicators.
    Supports autocomplete, recommendations, and fuzzy fallbacks.
    """
    try:
        db = get_db()
        payload = request.get_json() or {}
        query_text = payload.get("query", "").strip()
        limit = payload.get("limit", 15)

        if not query_text:
            # Return suggestions / recent items when query is empty
            recent_bonds = list(db["bonds"].find().limit(5))
            for b in recent_bonds:
                b["_id"] = str(b["_id"])
            return jsonify(
                {
                    "success": True,
                    "suggestions": [
                        "10Y Treasury Yield",
                        "US Corporate High Yield",
                        "Inflation Rate (CPI)",
                        "Portfolio rebalancing",
                        "Risk Parity strategy",
                    ],
                    "results": {
                        "bonds": recent_bonds,
                        "news": [],
                        "portfolios": [],
                        "macro": [],
                    },
                }
            )

        escaped = re.escape(query_text)
        regex_filter = {"$regex": escaped, "$options": "i"}

        results = {
            "bonds": [],
            "news": [],
            "portfolios": [],
            "watchlists": [],
            "macro": [],
        }

        # 1. Search Bonds (by CUSIP, Issuer, Name)
        bonds_query = {
            "$or": [
                {"cusip": regex_filter},
                {"issuer": regex_filter},
                {"name": regex_filter},
                {"type": regex_filter},
            ]
        }
        bonds = list(db["bonds"].find(bonds_query).limit(10))
        for b in bonds:
            b["_id"] = str(b["_id"])
            results["bonds"].append(b)

        # 2. Search Portfolios (by Name)
        portfolios = list(db["portfolios"].find({"name": regex_filter}).limit(5))
        for p in portfolios:
            p["_id"] = str(p["_id"])
            for h in p.get("holdings", []):
                if "bond_id" in h:
                    h["bond_id"] = str(h["bond_id"])
            results["portfolios"].append(p)

        # 3. Search Watchlists (by Name)
        watchlists = list(db["watchlists"].find({"name": regex_filter}).limit(5))
        for w in watchlists:
            w["_id"] = str(w["_id"])
            results["watchlists"].append(w)

        # 4. Search News (by Title, Summary)
        news = list(
            db["news_articles"]
            .find({"$or": [{"title": regex_filter}, {"summary": regex_filter}]})
            .sort("fetched_at", -1)
            .limit(10)
        )
        for n in news:
            n["_id"] = str(n["_id"])
            results["news"].append(n)

        # 5. Search Macro Indicators (Fuzzy match on Economic series)
        from services.fred_service import ECONOMIC_SERIES, TREASURY_SERIES

        for key, meta in ECONOMIC_SERIES.items():
            if (
                fuzzy_match(query_text, meta["name"]) > 0.45
                or query_text.lower() in meta["name"].lower()
                or query_text.lower() in key.lower()
            ):
                results["macro"].append(
                    {
                        "id": key,
                        "name": meta["name"],
                        "category": meta["category"],
                        "type": "indicator",
                    }
                )

        for key in TREASURY_SERIES.keys():
            if (
                query_text.lower() in key.lower()
                or "treasury" in query_text.lower()
                or "yield" in query_text.lower()
            ):
                results["macro"].append(
                    {
                        "id": key,
                        "name": f"{key} Treasury Yield",
                        "category": "rates",
                        "type": "treasury",
                    }
                )

        # Remove duplicate macro entries if any
        seen_macro = set()
        unique_macro = []
        for m in results["macro"]:
            if m["id"] not in seen_macro:
                seen_macro.add(m["id"])
                unique_macro.append(m)
        results["macro"] = unique_macro[:5]

        # Fuzzy matching fallbacks if standard query yields nothing for bonds
        if not results["bonds"] and len(query_text) >= 3:
            all_bonds = list(db["bonds"].find().limit(150))
            matched_bonds = []
            for b in all_bonds:
                b["_id"] = str(b["_id"])
                score = max(
                    fuzzy_match(query_text, b.get("name", "")),
                    fuzzy_match(query_text, b.get("issuer", "")),
                    fuzzy_match(query_text, b.get("cusip", "")),
                )
                if score > 0.45:
                    b["fuzzy_score"] = score
                    matched_bonds.append(b)
            matched_bonds.sort(key=lambda x: x["fuzzy_score"], reverse=True)
            results["bonds"] = matched_bonds[:8]

        # Count total results
        total_count = sum(len(v) for v in results.values())

        return jsonify(
            {
                "success": True,
                "query": query_text,
                "total": total_count,
                "results": results,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
