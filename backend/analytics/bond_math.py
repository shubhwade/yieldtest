"""
YieldLens Bond Mathematics Engine
Complete fixed-income analytics using Newton-Raphson and numpy.
"""

from datetime import datetime

from utils.helpers import calculate_years_to_maturity, rating_to_score, safe_float


class BondCalculator:
    """Full-featured bond calculator for fixed-income analytics."""

    # ------------------------------------------------------------------ #
    #  Core Pricing & Yield
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_bond_price(
        coupon: float,
        ytm: float,
        years_to_maturity: float,
        frequency: int = 2,
        face_value: float = 100.0,
    ) -> float:
        """
        Calculate the theoretical (clean) price of a bond.

        Args:
            coupon: Annual coupon rate as a decimal (e.g. 0.05 for 5%).
            ytm: Yield to maturity as a decimal.
            years_to_maturity: Years until the bond matures.
            frequency: Coupon payments per year (default 2 = semi-annual).
            face_value: Par / face value (default 100).

        Returns:
            Bond price as a float.
        """
        if years_to_maturity <= 0:
            return face_value
        if ytm == 0:
            return face_value + coupon * face_value * years_to_maturity

        n_periods = int(round(years_to_maturity * frequency))
        if n_periods <= 0:
            return face_value

        periodic_coupon = (coupon * face_value) / frequency
        periodic_rate = ytm / frequency

        # PV of coupon stream
        if periodic_rate != 0:
            pv_coupons = (
                periodic_coupon
                * (1 - (1 + periodic_rate) ** (-n_periods))
                / periodic_rate
            )
        else:
            pv_coupons = periodic_coupon * n_periods

        # PV of par
        pv_par = face_value / (1 + periodic_rate) ** n_periods

        return pv_coupons + pv_par

    @staticmethod
    def calculate_ytm(
        price: float,
        coupon: float,
        years_to_maturity: float,
        frequency: int = 2,
        face_value: float = 100.0,
        tolerance: float = 1e-8,
        max_iterations: int = 200,
    ) -> float:
        """
        Calculate Yield to Maturity using Newton-Raphson method.

        Args:
            price: Current market price.
            coupon: Annual coupon rate as decimal (e.g. 0.05).
            years_to_maturity: Years to maturity.
            frequency: Payments per year.
            face_value: Face value.
            tolerance: Convergence tolerance.
            max_iterations: Maximum iterations.

        Returns:
            YTM as a decimal (e.g. 0.045 for 4.5%).
        """
        if years_to_maturity <= 0 or price <= 0:
            return 0.0

        n_periods = int(round(years_to_maturity * frequency))
        if n_periods <= 0:
            return 0.0

        periodic_coupon = (coupon * face_value) / frequency

        # Initial guess using current yield approximation
        if price != 0:
            guess = (
                (coupon * face_value) + (face_value - price) / years_to_maturity
            ) / ((face_value + price) / 2)
        else:
            guess = coupon

        ytm_guess = max(guess, 0.0001)

        for _ in range(max_iterations):
            r = ytm_guess / frequency
            if r <= -1:
                r = 0.0001

            # Price function
            try:
                disc = (1 + r) ** (-n_periods)
                if r != 0:
                    pv = periodic_coupon * (1 - disc) / r + face_value * disc
                else:
                    pv = periodic_coupon * n_periods + face_value
            except (OverflowError, ZeroDivisionError):
                break

            diff = pv - price

            if abs(diff) < tolerance:
                return max(ytm_guess, 0.0)

            # Derivative of price w.r.t. r
            try:
                dpv = 0.0
                for t in range(1, n_periods + 1):
                    dpv -= t * periodic_coupon / ((1 + r) ** (t + 1))
                dpv -= n_periods * face_value / ((1 + r) ** (n_periods + 1))
                dpv /= frequency
            except (OverflowError, ZeroDivisionError):
                break

            if abs(dpv) < 1e-15:
                break

            ytm_guess -= diff / dpv

            # Clamp to reasonable range
            ytm_guess = max(ytm_guess, -0.05)
            ytm_guess = min(ytm_guess, 1.0)

        return max(ytm_guess, 0.0)

    @staticmethod
    def calculate_current_yield(annual_coupon: float, price: float) -> float:
        """
        Calculate current yield.

        Args:
            annual_coupon: Annual coupon payment in dollars.
            price: Current market price.

        Returns:
            Current yield as a decimal.
        """
        if price <= 0:
            return 0.0
        return annual_coupon / price

    # ------------------------------------------------------------------ #
    #  Duration & Convexity
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_duration(
        coupon: float,
        ytm: float,
        years_to_maturity: float,
        frequency: int = 2,
        face_value: float = 100.0,
    ) -> tuple[float, float]:
        """
        Calculate Macaulay and Modified duration.

        Args:
            coupon: Annual coupon rate as decimal.
            ytm: YTM as decimal.
            years_to_maturity: Years to maturity.
            frequency: Payments per year.
            face_value: Face value.

        Returns:
            Tuple of (macaulay_duration, modified_duration) in years.
        """
        if years_to_maturity <= 0:
            return (0.0, 0.0)

        n_periods = int(round(years_to_maturity * frequency))
        if n_periods <= 0:
            return (0.0, 0.0)

        periodic_coupon = (coupon * face_value) / frequency
        periodic_rate = ytm / frequency if ytm != 0 else 0.0001

        price = 0.0
        weighted_sum = 0.0

        for t in range(1, n_periods + 1):
            cf = periodic_coupon
            if t == n_periods:
                cf += face_value
            pv_cf = cf / (1 + periodic_rate) ** t
            price += pv_cf
            weighted_sum += (t / frequency) * pv_cf

        if price <= 0:
            return (0.0, 0.0)

        macaulay = weighted_sum / price
        modified = macaulay / (1 + periodic_rate)

        return (round(macaulay, 4), round(modified, 4))

    @staticmethod
    def calculate_dv01(modified_duration: float, price: float = 100.0) -> float:
        """
        Calculate DV01 (Dollar Value of a Basis Point).

        Args:
            modified_duration: Modified duration in years.
            price: Current price.

        Returns:
            DV01 value.
        """
        return modified_duration * price * 0.0001

    @staticmethod
    def calculate_convexity(
        coupon: float,
        ytm: float,
        years_to_maturity: float,
        frequency: int = 2,
        face_value: float = 100.0,
    ) -> float:
        """
        Calculate bond convexity.

        Args:
            coupon: Annual coupon rate as decimal.
            ytm: YTM as decimal.
            years_to_maturity: Years to maturity.
            frequency: Payments per year.
            face_value: Face value.

        Returns:
            Convexity value.
        """
        if years_to_maturity <= 0:
            return 0.0

        n_periods = int(round(years_to_maturity * frequency))
        if n_periods <= 0:
            return 0.0

        periodic_coupon = (coupon * face_value) / frequency
        periodic_rate = ytm / frequency if ytm != 0 else 0.0001

        price = 0.0
        convexity_sum = 0.0

        for t in range(1, n_periods + 1):
            cf = periodic_coupon
            if t == n_periods:
                cf += face_value
            pv_cf = cf / (1 + periodic_rate) ** t
            price += pv_cf
            convexity_sum += pv_cf * t * (t + 1)

        if price <= 0:
            return 0.0

        convexity = convexity_sum / (price * (1 + periodic_rate) ** 2 * frequency**2)
        return round(convexity, 4)

    # ------------------------------------------------------------------ #
    #  Yield Transforms
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_tax_equivalent_yield(
        tax_free_yield: float, tax_bracket: float
    ) -> float:
        """
        Calculate tax-equivalent yield for municipal bonds.

        Args:
            tax_free_yield: Tax-free yield as decimal.
            tax_bracket: Marginal tax rate as decimal (e.g. 0.37).

        Returns:
            Tax-equivalent yield as decimal.
        """
        if tax_bracket >= 1.0:
            return 0.0
        return tax_free_yield / (1 - tax_bracket)

    @staticmethod
    def calculate_real_yield(nominal_yield: float, inflation_rate: float) -> float:
        """
        Calculate real (inflation-adjusted) yield using Fisher equation.

        Args:
            nominal_yield: Nominal yield as decimal.
            inflation_rate: Inflation rate as decimal.

        Returns:
            Real yield as decimal.
        """
        return ((1 + nominal_yield) / (1 + inflation_rate)) - 1

    @staticmethod
    def calculate_spread(bond_yield: float, benchmark_yield: float) -> float:
        """
        Calculate yield spread in basis points.

        Args:
            bond_yield: Bond yield as decimal.
            benchmark_yield: Benchmark yield as decimal.

        Returns:
            Spread in basis points.
        """
        return (bond_yield - benchmark_yield) * 10000

    # ------------------------------------------------------------------ #
    #  Risk Metrics
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_risk_score(
        ytm: float,
        duration: float,
        credit_rating: str,
        spread: float,
    ) -> int:
        """
        Calculate a composite risk score from 0 (safest) to 100 (riskiest).

        Args:
            ytm: Yield to maturity as decimal.
            duration: Modified duration in years.
            credit_rating: Credit rating string.
            spread: Spread in basis points.

        Returns:
            Risk score 0–100.
        """
        credit_score = rating_to_score(credit_rating)
        credit_risk = 100 - credit_score  # Higher rating → lower risk

        duration_risk = min(duration * 5, 40)  # Max 40 pts
        spread_risk = min(spread / 20, 30)  # Max 30 pts
        yield_risk = min(ytm * 100, 20)  # Max 20 pts

        raw = (
            credit_risk * 0.35
            + duration_risk * 0.25
            + spread_risk * 0.25
            + yield_risk * 0.15
        )
        return int(min(max(round(raw), 0), 100))

    @staticmethod
    def calculate_sharpe_ratio(
        return_rate: float,
        risk_free_rate: float,
        volatility: float,
    ) -> float:
        """
        Calculate the Sharpe ratio.

        Args:
            return_rate: Expected return as decimal.
            risk_free_rate: Risk-free rate as decimal.
            volatility: Standard deviation of returns.

        Returns:
            Sharpe ratio.
        """
        if volatility <= 0:
            return 0.0
        return (return_rate - risk_free_rate) / volatility

    @staticmethod
    def estimate_price_change(
        modified_duration: float,
        convexity: float,
        yield_change: float,
    ) -> float:
        """
        Estimate percentage price change for a given yield shift.

        Args:
            modified_duration: Modified duration.
            convexity: Convexity.
            yield_change: Yield change as decimal (e.g. 0.01 = 100 bps).

        Returns:
            Estimated price change as percentage.
        """
        duration_effect = -modified_duration * yield_change
        convexity_effect = 0.5 * convexity * yield_change**2
        return (duration_effect + convexity_effect) * 100

    # ------------------------------------------------------------------ #
    #  Scenario Analysis
    # ------------------------------------------------------------------ #

    @staticmethod
    def scenario_analysis(
        coupon: float,
        current_ytm: float,
        years_to_maturity: float,
        yield_scenarios: list[float],
        frequency: int = 2,
        face_value: float = 100.0,
    ) -> dict:
        """
        Run scenario analysis across multiple yield levels.

        Args:
            coupon: Annual coupon rate as decimal.
            current_ytm: Current YTM as decimal.
            years_to_maturity: Years to maturity.
            yield_scenarios: List of yield levels (decimals) to test.
            frequency: Payments per year.
            face_value: Face value.

        Returns:
            Dict with current price and list of scenario results.
        """
        calc = BondCalculator
        current_price = calc.calculate_bond_price(
            coupon, current_ytm, years_to_maturity, frequency, face_value
        )
        mac_dur, mod_dur = calc.calculate_duration(
            coupon, current_ytm, years_to_maturity, frequency, face_value
        )
        convexity = calc.calculate_convexity(
            coupon, current_ytm, years_to_maturity, frequency, face_value
        )

        results = []
        for scenario_yield in yield_scenarios:
            new_price = calc.calculate_bond_price(
                coupon, scenario_yield, years_to_maturity, frequency, face_value
            )
            price_change_pct = (
                ((new_price - current_price) / current_price) * 100
                if current_price > 0
                else 0
            )
            yield_change = scenario_yield - current_ytm
            estimated_change = calc.estimate_price_change(
                mod_dur, convexity, yield_change
            )
            results.append(
                {
                    "yield": round(scenario_yield * 100, 2),
                    "price": round(new_price, 4),
                    "price_change_pct": round(price_change_pct, 4),
                    "yield_change_bps": round(yield_change * 10000, 1),
                    "estimated_change_pct": round(estimated_change, 4),
                }
            )

        return {
            "current_price": round(current_price, 4),
            "current_ytm": round(current_ytm * 100, 4),
            "macaulay_duration": mac_dur,
            "modified_duration": mod_dur,
            "convexity": convexity,
            "scenarios": results,
        }

    # ------------------------------------------------------------------ #
    #  Accrued Interest
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_accrued_interest(
        coupon_rate: float,
        last_coupon_date: str | datetime,
        settlement_date: str | datetime | None = None,
        frequency: int = 2,
        face_value: float = 100.0,
    ) -> float:
        """
        Calculate accrued interest using the actual/actual day-count convention.

        Args:
            coupon_rate: Annual coupon rate as decimal.
            last_coupon_date: Date of last coupon payment.
            settlement_date: Settlement date (default: today).
            frequency: Payments per year.
            face_value: Face value.

        Returns:
            Accrued interest in dollars.
        """
        if isinstance(last_coupon_date, str):
            from utils.helpers import parse_date

            last_coupon_date = parse_date(last_coupon_date)
        if settlement_date is None:
            settlement_date = datetime.utcnow()
        elif isinstance(settlement_date, str):
            from utils.helpers import parse_date

            settlement_date = parse_date(settlement_date)

        days_accrued = (settlement_date - last_coupon_date).days
        period_days = 365.25 / frequency
        accrued_fraction = days_accrued / period_days
        periodic_coupon = (coupon_rate * face_value) / frequency

        return round(periodic_coupon * accrued_fraction, 4)

    # ------------------------------------------------------------------ #
    #  Full Bond Analytics
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_full_bond_analytics(bond: dict) -> dict:
        """
        Calculate all analytics for a bond dictionary.

        Expected bond keys: coupon_rate, price, maturity_date, face_value, rating,
        type, tax_exempt.

        Args:
            bond: Bond dictionary from the database.

        Returns:
            Dict with all computed analytics merged onto the bond data.
        """
        calc = BondCalculator

        coupon = safe_float(bond.get("coupon_rate", 0)) / 100  # stored as pct
        price = safe_float(bond.get("price", 100))
        face_value = safe_float(bond.get("face_value", 1000))
        maturity_str = bond.get("maturity_date")
        rating = bond.get("rating", "BBB")
        bond_type = bond.get("type", "corporate")
        frequency = 2

        # ETFs, money market funds, and preferred stocks without maturity dates
        # cannot have meaningful duration/YTM calculations
        if bond_type in ("bond_etf", "money_market") or maturity_str is None:
            return {
                "ytm": round(coupon * 100, 4) if coupon else None,
                "current_yield": round(coupon * 100, 4) if coupon else None,
                "macaulay_duration": None,
                "modified_duration": None,
                "convexity": None,
                "dv01": None,
                "spread_bps": None,
                "risk_score": None,
                "tax_equivalent_yield": None,
                "scenarios": [],
                "accrued_interest": None,
                "years_to_maturity": None,
                "rating": rating,
                "bond_type": bond_type,
                "note": "Analytics not applicable for this instrument type",
            }

        years = calculate_years_to_maturity(maturity_str)

        # Core metrics
        ytm = calc.calculate_ytm(price, coupon, years, frequency, face_value)
        current_yield = calc.calculate_current_yield(coupon * face_value, price)
        mac_dur, mod_dur = calc.calculate_duration(
            coupon, ytm, years, frequency, face_value
        )
        convexity = calc.calculate_convexity(coupon, ytm, years, frequency, face_value)
        dv01 = calc.calculate_dv01(mod_dur, price)

        # Spread vs generic 10Y benchmark (assume 4.25% if unavailable)
        benchmark = 0.0425
        spread = calc.calculate_spread(ytm, benchmark)

        # Risk
        risk_score = calc.calculate_risk_score(ytm, mod_dur, rating, spread)

        # Tax-equiv yield for munis
        tax_equiv_yield = None
        if bond.get("tax_exempt"):
            tax_equiv_yield = round(
                calc.calculate_tax_equivalent_yield(ytm, 0.37) * 100, 4
            )

        # Scenario quick look
        scenario_yields = [ytm - 0.02, ytm - 0.01, ytm, ytm + 0.01, ytm + 0.02]
        scenarios = calc.scenario_analysis(
            coupon, ytm, years, scenario_yields, frequency, face_value
        )

        analytics = {
            "ytm": round(ytm * 100, 4),
            "current_yield": round(current_yield * 100, 4),
            "macaulay_duration": mac_dur,
            "modified_duration": mod_dur,
            "convexity": convexity,
            "dv01": round(dv01, 4),
            "spread_bps": round(spread, 2),
            "risk_score": risk_score,
            "years_to_maturity": round(years, 2),
            "tax_equivalent_yield": tax_equiv_yield,
            "scenarios": scenarios,
        }

        return analytics
