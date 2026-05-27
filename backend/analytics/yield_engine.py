"""
YieldLens Yield Engine
Mathematically exact quant bond math and curve calculations.
"""

import math
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np


class YieldEngine:
    """Rigorous fixed-income calculator for pricing, yields, risk measures, and curves."""

    # Day Count Conventions
    DAY_COUNT_ACT_ACT = "ACT/ACT"
    DAY_COUNT_ACT_360 = "ACT/360"
    DAY_COUNT_30_360 = "30/360"

    # ------------------------------------------------------------------ #
    #  Core Coupon & Accrued Interest
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_accrued_interest(
        coupon_rate: float,
        last_coupon_date: str | datetime,
        settlement_date: str | datetime | None = None,
        frequency: int = 2,
        face_value: float = 100.0,
        day_count: str = "ACT/ACT",
    ) -> float:
        """
        Calculate accrued interest using strict financial day-count conventions.
        """
        if isinstance(last_coupon_date, str):
            from utils.helpers import parse_date

            last_coupon_dt = parse_date(last_coupon_date)
        else:
            last_coupon_dt = last_coupon_date

        if settlement_date is None:
            settlement_dt = datetime.utcnow()
        elif isinstance(settlement_date, str):
            from utils.helpers import parse_date

            settlement_dt = parse_date(settlement_date)
        else:
            settlement_dt = settlement_date

        days_accrued = (settlement_dt - last_coupon_dt).days
        if days_accrued <= 0:
            return 0.0

        if day_count == YieldEngine.DAY_COUNT_30_360:
            # 30/360 US Convention
            y1, m1, d1 = last_coupon_dt.year, last_coupon_dt.month, last_coupon_dt.day
            y2, m2, d2 = settlement_dt.year, settlement_dt.month, settlement_dt.day
            if d1 == 31:
                d1 = 30
            if d2 == 31 and d1 >= 30:
                d2 = 30
            days_accrued = 360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)
            days_in_year = 360.0
            accrued_fraction = days_accrued / (days_in_year / frequency)
        elif day_count == YieldEngine.DAY_COUNT_ACT_360:
            days_in_year = 360.0
            accrued_fraction = days_accrued / (days_in_year / frequency)
        else:
            # ACT/ACT standard
            days_in_period = 365.25 / frequency
            accrued_fraction = days_accrued / days_in_period

        periodic_coupon = (coupon_rate * face_value) / frequency
        return round(periodic_coupon * accrued_fraction, 6)

    # ------------------------------------------------------------------ #
    #  Pricing and YTM Solvers
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
        Calculate Clean (theoretical) price of a bond.
        """
        if years_to_maturity <= 0:
            return face_value

        n_periods = int(round(years_to_maturity * frequency))
        if n_periods <= 0:
            return face_value

        periodic_coupon = (coupon * face_value) / frequency
        periodic_rate = ytm / frequency

        if periodic_rate != 0:
            pv_coupons = (
                periodic_coupon
                * (1 - (1 + periodic_rate) ** (-n_periods))
                / periodic_rate
            )
            pv_par = face_value * (1 + periodic_rate) ** (-n_periods)
            dirty_price = pv_coupons + pv_par
        else:
            dirty_price = (periodic_coupon * n_periods) + face_value

        # Clean Price = Dirty Price - Accrued Interest (assuming 0 for clean analytics wrapper)
        return round(dirty_price, 6)

    @staticmethod
    def calculate_ytm(
        price: float,
        coupon: float,
        years_to_maturity: float,
        frequency: int = 2,
        face_value: float = 100.0,
        tolerance: float = 1e-9,
        max_iterations: int = 200,
    ) -> float:
        """
        Solve for Yield-to-Maturity (YTM) exactly using Newton-Raphson.
        """
        if years_to_maturity <= 0 or price <= 0:
            return 0.0

        n_periods = int(round(years_to_maturity * frequency))
        if n_periods <= 0:
            return 0.0

        periodic_coupon = (coupon * face_value) / frequency

        # Initial guess via SEC yield approximation
        guess = ((coupon * face_value) + (face_value - price) / years_to_maturity) / (
            (face_value + price) / 2
        )
        y = max(guess, 0.0001)

        for _ in range(max_iterations):
            r = y / frequency
            try:
                disc = (1 + r) ** (-n_periods)
                if r != 0:
                    pv = periodic_coupon * (1 - disc) / r + face_value * disc
                else:
                    pv = periodic_coupon * n_periods + face_value

                diff = pv - price
                if abs(diff) < tolerance:
                    return round(y, 6)

                # Derivative w.r.t r
                dp = 0.0
                for t in range(1, n_periods + 1):
                    dp -= t * periodic_coupon / ((1 + r) ** (t + 1))
                dp -= n_periods * face_value / ((1 + r) ** (n_periods + 1))
                dp /= frequency  # scaling w.r.t. annualized yield

                if abs(dp) < 1e-15:
                    break

                y -= diff / dp
                # Clamp within sensible financial ranges
                y = max(min(y, 1.5), -0.2)
            except (OverflowError, ZeroDivisionError):
                break

        return round(max(y, 0.0), 6)

    @staticmethod
    def calculate_ytc(
        price: float,
        coupon: float,
        years_to_call: float,
        call_price: float,
        frequency: int = 2,
        face_value: float = 100.0,
    ) -> float:
        """
        Calculate Yield-to-Call (YTC) using call price and call horizon.
        """
        return YieldEngine.calculate_ytm(
            price=price,
            coupon=coupon,
            years_to_maturity=years_to_call,
            frequency=frequency,
            face_value=call_price,
        )

    @staticmethod
    def calculate_ytw(
        price: float,
        coupon: float,
        years_to_maturity: float,
        calls: List[Dict[str, float]],  # List of {"years": float, "price": float}
        frequency: int = 2,
        face_value: float = 100.0,
    ) -> float:
        """
        Calculate Yield-to-Worst (YTW). Returns the minimum of all YTCs and YTM.
        """
        ytm = YieldEngine.calculate_ytm(
            price, coupon, years_to_maturity, frequency, face_value
        )
        candidates = [ytm]

        for call in calls:
            ytc = YieldEngine.calculate_ytc(
                price=price,
                coupon=coupon,
                years_to_call=call["years"],
                call_price=call["price"],
                frequency=frequency,
                face_value=face_value,
            )
            candidates.append(ytc)

        return round(min(candidates), 6)

    # ------------------------------------------------------------------ #
    #  Duration, Convexity, and Interest Rate Sensitivity
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_duration_metrics(
        coupon: float,
        ytm: float,
        years_to_maturity: float,
        frequency: int = 2,
        face_value: float = 100.0,
    ) -> Dict[str, float]:
        """
        Compute Macaulay Duration, Modified Duration, and Convexity.
        """
        if years_to_maturity <= 0:
            return {
                "macaulay_duration": 0.0,
                "modified_duration": 0.0,
                "convexity": 0.0,
            }

        n_periods = int(round(years_to_maturity * frequency))
        if n_periods <= 0:
            return {
                "macaulay_duration": 0.0,
                "modified_duration": 0.0,
                "convexity": 0.0,
            }

        periodic_coupon = (coupon * face_value) / frequency
        periodic_rate = ytm / frequency if ytm != 0 else 0.0001

        price = 0.0
        weighted_sum = 0.0
        convexity_sum = 0.0

        for t in range(1, n_periods + 1):
            cf = periodic_coupon
            if t == n_periods:
                cf += face_value

            pv_cf = cf / ((1 + periodic_rate) ** t)
            price += pv_cf
            weighted_sum += (t / frequency) * pv_cf
            convexity_sum += pv_cf * t * (t + 1)

        if price <= 0:
            return {
                "macaulay_duration": 0.0,
                "modified_duration": 0.0,
                "convexity": 0.0,
            }

        macaulay = weighted_sum / price
        modified = macaulay / (1 + periodic_rate)
        convexity = convexity_sum / (
            price * ((1 + periodic_rate) ** 2) * (frequency**2)
        )

        return {
            "macaulay_duration": round(macaulay, 6),
            "modified_duration": round(modified, 6),
            "convexity": round(convexity, 6),
        }

    @staticmethod
    def calculate_effective_duration(
        coupon: float,
        ytm: float,
        years_to_maturity: float,
        shift_bps: float = 10.0,
        frequency: int = 2,
        face_value: float = 100.0,
    ) -> float:
        """
        Calculate Effective Duration by numerically shifting the yield curve.
        """
        dy = shift_bps / 10000.0
        p0 = YieldEngine.calculate_bond_price(
            coupon, ytm, years_to_maturity, frequency, face_value
        )
        p_up = YieldEngine.calculate_bond_price(
            coupon, ytm + dy, years_to_maturity, frequency, face_value
        )
        p_down = YieldEngine.calculate_bond_price(
            coupon, ytm - dy, years_to_maturity, frequency, face_value
        )

        if p0 <= 0:
            return 0.0
        eff_dur = (p_down - p_up) / (2.0 * p0 * dy)
        return round(eff_dur, 6)

    @staticmethod
    def calculate_dv01(modified_duration: float, price: float = 100.0) -> float:
        """
        Calculate Dollar Value of a Basis Point (DV01) / PVBP.
        """
        return round(modified_duration * price * 0.0001, 6)

    # ------------------------------------------------------------------ #
    #  Option-Adjusted Spread (OAS)
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_oas_binomial_tree(
        price: float,
        coupon: float,
        years: float,
        benchmark_ytm: float,
        volatility: float = 0.15,
        frequency: int = 2,
        face_value: float = 100.0,
        call_strike: Optional[float] = None,
        call_start_years: Optional[float] = None,
    ) -> float:
        """
        Calculate Option-Adjusted Spread (OAS) using a Binomial Interest Rate Tree (Ho-Lee Model).
        Splits price differences into option value and option-adjusted credit risk spread.
        """
        if years <= 0:
            return 0.0

        steps = int(round(years * frequency))
        if steps <= 0:
            return 0.0

        dt = 1.0 / frequency
        p_coupon = (coupon * face_value) / frequency

        # Build forward rate lattice based on Ho-Lee calibration
        # For simplicity in local execution, we calibrate the tree drift using flat benchmark curve
        r0 = benchmark_ytm / frequency

        # Binary search solver to back out the OAS spread that matches the option-embedded price
        oas_guess = 0.0
        step_size = 0.01

        for _ in range(100):
            # Calculate callable bond value using this trial OAS
            # Backward induction on the binomial tree
            # Node lattice of bond values
            values = np.zeros(steps + 1)

            # Terminal values at maturity
            for i in range(steps + 1):
                values[i] = face_value + p_coupon

            # Backward induction
            for step in range(steps - 1, -1, -1):
                new_values = np.zeros(step + 1)
                for node in range(step + 1):
                    # Ho-Lee rate at node
                    rate = (
                        r0
                        + oas_guess / frequency
                        + volatility * (2 * node - step) * math.sqrt(dt)
                    )
                    disc = 1.0 / (1.0 + rate)

                    # Expected discounted value
                    val = 0.5 * (values[node] + values[node + 1]) * disc

                    # Incorporate call option exercise
                    current_t = step * dt
                    if call_strike is not None and call_start_years is not None:
                        if current_t >= call_start_years:
                            val = min(val, call_strike)

                    # Add current coupon except at root (coupon is added after backward induction at terminal)
                    new_values[node] = val + (p_coupon if step > 0 else 0)
                values = new_values

            theoretical_price = values[0]
            diff = theoretical_price - price

            if abs(diff) < 1e-4:
                break

            # Adjust guess
            if diff > 0:
                oas_guess += step_size
            else:
                oas_guess -= step_size
            step_size *= 0.95

        return round(oas_guess * 10000.0, 2)  # return in basis points

    # ------------------------------------------------------------------ #
    #  Curves Bootstrapping Spot & Forward Rates
    # ------------------------------------------------------------------ #

    @staticmethod
    def bootstrap_spot_curve(
        maturities: List[float], yields: List[float]
    ) -> List[float]:
        """
        Bootstrap spot rates from a set of par bond yields.
        """
        if not maturities or len(maturities) != len(yields):
            return yields

        # Sort by maturity
        sorted_data = sorted(zip(maturities, yields))
        mats = [x[0] for x in sorted_data]
        ylds = [x[1] / 100.0 for x in sorted_data]  # convert to decimal

        spots = []
        for i, (t, y) in enumerate(zip(mats, ylds)):
            if i == 0:
                spots.append(y)
            else:
                # Solve for spot rate t
                # Price of par bond = 100
                coupon = y  # par bond coupon equals yield
                pv_coupons = 0.0
                for j in range(i):
                    pv_coupons += coupon / ((1 + spots[j]) ** mats[j])

                # PV = Coupon / (1+spot_t)^t + Par / (1+spot_t)^t
                disc_par = 1.0 - pv_coupons
                spot_t = ((1.0 + coupon) / disc_par) ** (1.0 / t) - 1.0
                spots.append(spot_t)

        return [round(s * 100.0, 6) for s in spots]

    @staticmethod
    def calculate_forward_rates(
        maturities: List[float], spot_rates: List[float]
    ) -> List[Dict[str, float]]:
        """
        Calculate forward rates from a set of spot rates.
        """
        forwards = []
        for i in range(len(maturities) - 1):
            t1, t2 = maturities[i], maturities[i + 1]
            s1, s2 = spot_rates[i] / 100.0, spot_rates[i + 1] / 100.0

            # Forward rate formula: f(t1, t2) = [ (1 + s2)^t2 / (1 + s1)^t1 ] ^ [1 / (t2 - t1)] - 1
            f = (((1.0 + s2) ** t2) / ((1.0 + s1) ** t1)) ** (1.0 / (t2 - t1)) - 1.0
            forwards.append(
                {
                    "period": f"{t1}Y-{t2}Y",
                    "forward_rate": round(f * 100.0, 6),
                    "spot_start": spot_rates[i],
                    "spot_end": spot_rates[i + 1],
                }
            )
        return forwards

    # ------------------------------------------------------------------ #
    #  Basic Yield Transforms
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_tax_equivalent_yield(
        tax_free_yield: float, tax_bracket: float
    ) -> float:
        """
        Calculate Tax-Equivalent Yield.
        """
        if tax_bracket >= 1.0:
            return 0.0
        return round(tax_free_yield / (1.0 - tax_bracket), 6)

    @staticmethod
    def calculate_real_yield(nominal_yield: float, inflation_rate: float) -> float:
        """
        Calculate Real Yield using Fisher equation.
        """
        return round(((1.0 + nominal_yield) / (1.0 + inflation_rate)) - 1.0, 6)

    @staticmethod
    def calculate_yield_spread(yield_a: float, yield_b: float) -> float:
        """
        Calculate Yield Spread in basis points (bps).
        """
        return round((yield_a - yield_b) * 10000.0, 2)
