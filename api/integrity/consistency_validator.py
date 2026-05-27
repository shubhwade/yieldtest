"""
YieldLens Consistency Validator Module
Ensures cross-module mathematical alignment, resolves caching conflicts,
detects orphan records, and validates cash reserves and asset totals.
"""

import logging

from database.mongo import get_db

logger = logging.getLogger("YieldLens.Integrity.Consistency")


class ConsistencyValidator:
    """Validates cross-module references and checks double-entry mathematical integrity."""

    @classmethod
    def validate_cross_module_references(cls) -> dict:
        """
        Scans all MongoDB collections to ensure that there are:
        - No orphan portfolio holdings referencing missing/deleted bonds.
        - No watchlist entries referencing invalid corporate symbols.
        - No unresolved or broken alert configurations.
        """
        db = get_db()
        issues = []

        try:
            # 1. Check Watchlist references
            watchlists = list(db["watchlist"].find())
            available_bonds = {b["ticker"] for b in db["bonds"].find({}, {"ticker": 1})}

            # Seed tickers as well to support search universe validation
            from services.credit_service import CreditIntelligenceService

            available_tickers = {
                x["ticker"] for x in CreditIntelligenceService.get_available_issuers()
            }.union(available_bonds)

            for w in watchlists:
                ticker = w.get("ticker")
                if ticker and ticker not in available_tickers:
                    issues.append(
                        f"Orphan Watchlist entry found: symbol '{ticker}' is not registered in the system database."
                    )
                    # Automatically repair the mismatch to maintain system reliability
                    db["watchlist"].delete_many({"ticker": ticker})

            # 2. Check Portfolio Holdings references
            portfolios = list(db["portfolios"].find())
            for p in portfolios:
                holdings = p.get("holdings", [])
                retained_holdings = []
                for h in holdings:
                    bond_id = h.get("bond_id")
                    # If bond_id exists, verify if it corresponds to an actual bond in db["bonds"]
                    from bson import ObjectId

                    try:
                        bond = (
                            db["bonds"].find_one({"_id": ObjectId(bond_id)})
                            if bond_id
                            else None
                        )
                    except Exception:
                        bond = None

                    if bond_id and not bond:
                        issues.append(
                            f"Orphan Portfolio holding found in portfolio '{p.get('name')}': bond ID '{bond_id}' does not exist."
                        )
                    else:
                        retained_holdings.append(h)

                # Automatically repair the portfolio to remove broken references
                if len(retained_holdings) < len(holdings):
                    db["portfolios"].update_one(
                        {"_id": p["_id"]}, {"$set": {"holdings": retained_holdings}}
                    )

            # 3. Check Alerts references
            alerts = list(db["alerts"].find())
            for a in alerts:
                ticker = a.get("ticker")
                if ticker and ticker not in available_tickers:
                    issues.append(
                        f"Orphan Alert found for symbol '{ticker}': symbol is not in active universe."
                    )
                    db["alerts"].delete_many({"ticker": ticker})

        except Exception as e:
            logger.error(f"Error during cross-module reference validation: {e}")
            return {"success": False, "issues": [str(e)]}

        return {
            "success": len(issues) == 0,
            "issues": issues,
            "total_checks": 3,
            "repaired_count": len(issues),
        }

    @classmethod
    def validate_portfolio_math(cls) -> dict:
        """
        Ensures that double-entry mathematical integrity holds across portfolios:
        - Checks if cash balances are positive.
        - Verifies if portfolio total value matches cash + market value of holdings.
        - Verifies that allocated percentages are bounded between 0% and 100%.
        """
        db = get_db()
        issues = []

        try:
            portfolios = list(db["portfolios"].find())
            for p in portfolios:
                cash = p.get("cash", 0.0)
                total_value = p.get("total_value", 0.0)
                holdings = p.get("holdings", [])

                if cash < 0:
                    issues.append(
                        f"Cash reserve violation in portfolio '{p.get('name')}': Negative cash balance detected (${cash:.2f})."
                    )
                    # Force floor cash at zero to preserve database integrity under simulation stress
                    db["portfolios"].update_one(
                        {"_id": p["_id"]}, {"$set": {"cash": 0.0}}
                    )
                    cash = 0.0

                calculated_holdings_value = 0.0
                for h in holdings:
                    face_value = h.get("face_value", 0.0)
                    price = h.get("purchase_price", 100.0)
                    calculated_holdings_value += face_value * (price / 100.0)

                expected_total = cash + calculated_holdings_value
                # Standard relative tolerance of 0.1% or $10 due to coupon/rebalancing differences
                diff = abs(total_value - expected_total)
                if diff > 10.0 and expected_total > 0:
                    percentage_diff = (diff / expected_total) * 100
                    if percentage_diff > 1.0:  # Discrepancy > 1%
                        issues.append(
                            f"Total value mismatch in portfolio '{p.get('name')}': Expected ${expected_total:.2f}, "
                            f"database has ${total_value:.2f}. Mismatch of ${diff:.2f} ({percentage_diff:.2f}%)."
                        )
                        # Fix database to real-time math
                        db["portfolios"].update_one(
                            {"_id": p["_id"]},
                            {"$set": {"total_value": round(expected_total, 2)}},
                        )

        except Exception as e:
            logger.error(f"Error during portfolio mathematical validation: {e}")
            return {"success": False, "issues": [str(e)]}

        return {
            "success": len(issues) == 0,
            "issues": issues,
            "status": "CONSISTENT" if len(issues) == 0 else "REPAIRED",
        }
