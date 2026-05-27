"""
YieldLens Scenario Engine
Run various yield-curve and spread scenarios on a set of bonds.
"""

from analytics.bond_math import BondCalculator
from utils.helpers import calculate_years_to_maturity, safe_float


class ScenarioEngine:
    """Pre-built yield-curve and spread scenario generators."""

    _calc = BondCalculator

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    @classmethod
    def _bond_metrics(cls, bond: dict) -> dict:
        """Extract standard metrics from a bond dict."""
        coupon = safe_float(bond.get("coupon_rate", 0)) / 100
        price = safe_float(bond.get("price", 100))
        face = safe_float(bond.get("face_value", 100))
        years = calculate_years_to_maturity(bond.get("maturity_date", "2030-01-01"))
        ytm = cls._calc.calculate_ytm(price, coupon, years, 2, face)
        mac, mod = cls._calc.calculate_duration(coupon, ytm, years, 2, face)
        cx = cls._calc.calculate_convexity(coupon, ytm, years, 2, face)
        return {
            "coupon": coupon,
            "price": price,
            "face": face,
            "years": years,
            "ytm": ytm,
            "mod_duration": mod,
            "convexity": cx,
            "name": bond.get("name", "Unknown"),
            "id": bond.get("id", ""),
        }

    @classmethod
    def _apply_shift(cls, bonds: list[dict], shift_fn) -> dict:
        """Apply a per-bond yield shift function and return impact summary."""
        results = []
        for bond in bonds:
            m = cls._bond_metrics(bond)
            shift = shift_fn(m)
            new_price = cls._calc.calculate_bond_price(
                m["coupon"], m["ytm"] + shift, m["years"], 2, m["face"]
            )
            pct_change = (
                ((new_price - m["price"]) / m["price"]) * 100 if m["price"] else 0
            )
            results.append(
                {
                    "id": m["id"],
                    "name": m["name"],
                    "original_price": round(m["price"], 4),
                    "new_price": round(new_price, 4),
                    "price_change_pct": round(pct_change, 4),
                    "yield_shift_bps": round(shift * 10000, 1),
                    "duration": m["mod_duration"],
                }
            )

        avg_impact = (
            sum(r["price_change_pct"] for r in results) / len(results) if results else 0
        )
        return {
            "bonds": results,
            "average_impact_pct": round(avg_impact, 4),
            "bonds_affected": len(results),
        }

    # ------------------------------------------------------------------ #
    #  Parallel Shift
    # ------------------------------------------------------------------ #

    @classmethod
    def parallel_shift(cls, bonds: list[dict], shift_bps: float) -> dict:
        """
        Shift all yields by the same amount.

        Args:
            bonds: List of bond dicts.
            shift_bps: Shift in basis points (e.g. 100 = +1%).

        Returns:
            Impact summary.
        """
        shift = shift_bps / 10000
        result = cls._apply_shift(bonds, lambda m: shift)
        result["scenario"] = "Parallel Shift"
        result["shift_bps"] = shift_bps
        return result

    # ------------------------------------------------------------------ #
    #  Curve Steepener
    # ------------------------------------------------------------------ #

    @classmethod
    def curve_steepener(
        cls, bonds: list[dict], short_shift: float, long_shift: float
    ) -> dict:
        """
        Steepen the curve: short rates move one way, long rates the other.

        Args:
            bonds: List of bond dicts.
            short_shift: BPS shift for ≤ 2-year bonds.
            long_shift: BPS shift for ≥ 10-year bonds.

        Returns:
            Impact summary.
        """

        def shift_fn(m: dict) -> float:
            yrs = m["years"]
            if yrs <= 2:
                return short_shift / 10000
            elif yrs >= 10:
                return long_shift / 10000
            else:
                # Linear interpolation
                frac = (yrs - 2) / 8
                return ((1 - frac) * short_shift + frac * long_shift) / 10000

        result = cls._apply_shift(bonds, shift_fn)
        result["scenario"] = "Curve Steepener"
        result["short_shift_bps"] = short_shift
        result["long_shift_bps"] = long_shift
        return result

    # ------------------------------------------------------------------ #
    #  Curve Flattener
    # ------------------------------------------------------------------ #

    @classmethod
    def curve_flattener(
        cls, bonds: list[dict], short_shift: float, long_shift: float
    ) -> dict:
        """
        Flatten the curve: short rates rise, long rates fall (or less rise).

        Args:
            bonds: List of bond dicts.
            short_shift: BPS shift for short end.
            long_shift: BPS shift for long end.

        Returns:
            Impact summary.
        """

        def shift_fn(m: dict) -> float:
            yrs = m["years"]
            if yrs <= 2:
                return short_shift / 10000
            elif yrs >= 10:
                return long_shift / 10000
            else:
                frac = (yrs - 2) / 8
                return ((1 - frac) * short_shift + frac * long_shift) / 10000

        result = cls._apply_shift(bonds, shift_fn)
        result["scenario"] = "Curve Flattener"
        result["short_shift_bps"] = short_shift
        result["long_shift_bps"] = long_shift
        return result

    # ------------------------------------------------------------------ #
    #  Spread Widening
    # ------------------------------------------------------------------ #

    @classmethod
    def spread_widening(cls, bonds: list[dict], spread_change_bps: float) -> dict:
        """
        Widen credit spreads — affects non-government bonds more.

        Args:
            bonds: List of bond dicts.
            spread_change_bps: Spread change in basis points.

        Returns:
            Impact summary.
        """

        def shift_fn(m: dict) -> float:
            # Treasuries unaffected; others shifted by spread change
            bond_type = m.get("type", "corporate")
            if bond_type in ("treasury", "tips"):
                return 0.0
            return spread_change_bps / 10000

        # We need type info in metrics — patch _apply_shift input
        enriched = []
        for bond in bonds:
            enriched.append(bond)

        results = []
        for bond in bonds:
            m = cls._bond_metrics(bond)
            m["type"] = bond.get("type", "corporate")
            shift = shift_fn(m)
            new_price = cls._calc.calculate_bond_price(
                m["coupon"], m["ytm"] + shift, m["years"], 2, m["face"]
            )
            pct_change = (
                ((new_price - m["price"]) / m["price"]) * 100 if m["price"] else 0
            )
            results.append(
                {
                    "id": m["id"],
                    "name": m["name"],
                    "original_price": round(m["price"], 4),
                    "new_price": round(new_price, 4),
                    "price_change_pct": round(pct_change, 4),
                    "yield_shift_bps": round(shift * 10000, 1),
                    "duration": m["mod_duration"],
                    "type": m["type"],
                }
            )

        avg_impact = (
            sum(r["price_change_pct"] for r in results) / len(results) if results else 0
        )
        return {
            "scenario": "Spread Widening",
            "spread_change_bps": spread_change_bps,
            "bonds": results,
            "average_impact_pct": round(avg_impact, 4),
            "bonds_affected": len(results),
        }

    # ------------------------------------------------------------------ #
    #  Inflation Shock
    # ------------------------------------------------------------------ #

    @classmethod
    def inflation_shock(cls, bonds: list[dict], inflation_change: float) -> dict:
        """
        Model an inflation shock: rates rise, TIPS benefit.

        Args:
            bonds: List of bond dicts.
            inflation_change: Change in inflation rate (decimal, e.g. 0.02 = 2%).

        Returns:
            Impact summary.
        """
        results = []
        for bond in bonds:
            m = cls._bond_metrics(bond)
            bond_type = bond.get("type", "corporate")

            if bond_type == "tips":
                # TIPS principal adjusts upward; price impact mitigated
                shift = inflation_change * 0.3  # partial pass-through
            else:
                # Nominal bonds: rates rise roughly 1:1 with inflation surprise
                shift = inflation_change

            new_price = cls._calc.calculate_bond_price(
                m["coupon"], m["ytm"] + shift, m["years"], 2, m["face"]
            )
            pct_change = (
                ((new_price - m["price"]) / m["price"]) * 100 if m["price"] else 0
            )
            results.append(
                {
                    "id": m["id"],
                    "name": m["name"],
                    "original_price": round(m["price"], 4),
                    "new_price": round(new_price, 4),
                    "price_change_pct": round(pct_change, 4),
                    "yield_shift_bps": round(shift * 10000, 1),
                    "type": bond_type,
                }
            )

        avg_impact = (
            sum(r["price_change_pct"] for r in results) / len(results) if results else 0
        )
        return {
            "scenario": "Inflation Shock",
            "inflation_change_pct": round(inflation_change * 100, 2),
            "bonds": results,
            "average_impact_pct": round(avg_impact, 4),
            "bonds_affected": len(results),
        }

    # ------------------------------------------------------------------ #
    #  Run All Scenarios
    # ------------------------------------------------------------------ #

    @classmethod
    def run_all_scenarios(cls, bonds: list[dict]) -> dict:
        """
        Run the full suite of standard scenarios.

        Args:
            bonds: List of bond dicts.

        Returns:
            Dict with all scenario results.
        """
        return {
            "parallel_up_100": cls.parallel_shift(bonds, 100),
            "parallel_down_100": cls.parallel_shift(bonds, -100),
            "parallel_up_200": cls.parallel_shift(bonds, 200),
            "steepener": cls.curve_steepener(bonds, -50, 100),
            "flattener": cls.curve_flattener(bonds, 100, -50),
            "spread_widening_50": cls.spread_widening(bonds, 50),
            "spread_widening_100": cls.spread_widening(bonds, 100),
            "inflation_shock_2pct": cls.inflation_shock(bonds, 0.02),
            "bond_count": len(bonds),
        }
