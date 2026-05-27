"""
AI Service — Resilient Multi-Provider Intelligence Engine
Provides AI-powered analysis with 3-tier failover:
  1. Google Gemini Flash (primary — large free tier)
  2. OpenRouter (secondary — model rotation)
  3. Local rule-based fallback (always works)

All responses follow structured output format with:
  summary, risk_analysis, portfolio_impact, related_holdings,
  recommended_actions, sources, confidence_score
"""

import json
import logging

import httpx
from config import Config
from database.cache import cache

logger = logging.getLogger("YieldLens.AI")

# ── Pre-generated fallback content ────────────────────────────────────────────

FALLBACK_MARKET_BRIEF = """## Daily Fixed Income Market Brief

**Treasury Market**: The yield curve continues to show signs of normalization after extended inversion periods. The 10-year Treasury note is trading around 4.25%, while the 2-year note sits at approximately 4.45%, maintaining a modestly inverted spread.

**Credit Markets**: Investment-grade corporate spreads remain relatively tight at around 95-105 basis points over Treasuries, signaling continued confidence in corporate credit quality. High-yield spreads have compressed to approximately 350-380 bps, reflecting risk appetite in the market.

**Key Themes**:
- Federal Reserve maintaining current rate stance with data-dependent approach
- TIPS breakeven rates suggest inflation expectations anchored near 2.3-2.5%
- Municipal bond yields attractive for high-tax-bracket investors
- Short-duration instruments still offering competitive yields vs. duration risk

**Outlook**: Watch for upcoming employment data and CPI releases which may influence Fed rate path expectations. The Treasury auction calendar is active this week with 2Y, 5Y, and 7Y note offerings."""

FALLBACK_CREDIT_ANALYSIS = {
    "summary": "Based on publicly available financial data, this issuer maintains a solid credit profile with stable revenue generation and manageable debt levels. The company's interest coverage ratio suggests adequate ability to service debt obligations.",
    "strengths": [
        "Strong market position and brand recognition",
        "Consistent free cash flow generation",
        "Diversified revenue streams",
        "Investment-grade credit rating",
    ],
    "risks": [
        "Sensitivity to macroeconomic conditions",
        "Industry-specific regulatory risks",
        "Interest rate exposure on floating-rate obligations",
        "Potential earnings volatility",
    ],
    "recommendation": "Hold — Credit fundamentals remain stable with no near-term catalysts for rating changes.",
}

# ── System prompts ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are YieldLens AI, a senior fixed-income analyst at a top-tier investment bank.
You provide Bloomberg-quality market intelligence for professional bond investors.

Core expertise:
- Treasury markets, yield curve analysis, duration risk
- Corporate credit (IG/HY), municipal bonds, structured products
- Fed policy, macro indicators, inflation dynamics
- Portfolio construction and risk management

Communication style:
- Professional, concise, data-driven
- Use specific numbers and basis points
- Reference relevant benchmarks and historical context
- Always include confidence level and data sources
- Format responses with markdown for readability

IMPORTANT: When portfolio data is provided, always reference the user's specific holdings, sectors, and exposures in your analysis."""

STRUCTURED_OUTPUT_PROMPT = """
Respond with a JSON object containing these fields:
- "summary": 2-3 sentence executive summary
- "risk_analysis": key risks identified (1-2 sentences)
- "portfolio_impact": how this affects the user's portfolio (1-2 sentences, reference specific holdings if provided)
- "related_holdings": array of specific bond/holding names affected (from portfolio context, or empty array)
- "recommended_actions": array of 2-3 actionable recommendations
- "sources": array of data sources referenced (e.g., "FRED", "Treasury.gov", "Finnhub")
- "confidence_score": integer 1-100 representing confidence in analysis

Return ONLY valid JSON, no markdown code blocks."""


class AIService:
    """AI service with multi-provider failover and structured output."""

    def __init__(self):
        self.gemini_key = Config.GEMINI_API_KEY
        self.openrouter_key = Config.OPENROUTER_API_KEY
        self.openrouter_models = Config.OPENROUTER_MODELS
        self.model = None
        self._init_gemini()

    def _init_gemini(self):
        """Initialize Google Gemini SDK."""
        if self.gemini_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.gemini_key)
                self.model = genai.GenerativeModel("gemini-2.0-flash")
                logger.info("[AI] Gemini API initialized")
            except Exception as e:
                logger.error(f"[AI] Gemini init failed: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # GENERATION — 3-TIER FAILOVER
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_gemini(self, prompt: str, max_tokens: int = 1024) -> str:
        """Tier 1: Generate via Google Gemini."""
        if not self.model:
            return None
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"max_output_tokens": max_tokens, "temperature": 0.7},
            )
            text = response.text
            if text and len(text.strip()) > 10:
                logger.info("[AI] Gemini response OK")
                return text
        except Exception as e:
            logger.warning(f"[AI] Gemini error: {e}")
        return None

    def _generate_openrouter(self, prompt: str, max_tokens: int = 1024) -> str:
        """Tier 2: Generate via OpenRouter with model rotation."""
        if not self.openrouter_key:
            return None

        for model_name in self.openrouter_models:
            try:
                with httpx.Client(timeout=20.0) as client:
                    res = client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.openrouter_key}",
                            "HTTP-Referer": "https://yieldlens.app",
                            "X-Title": "YieldLens",
                        },
                        json={
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": prompt},
                            ],
                            "max_tokens": max_tokens,
                            "temperature": 0.7,
                        },
                    )
                    if res.status_code == 200:
                        text = res.json()["choices"][0]["message"]["content"]
                        if text and len(text.strip()) > 10:
                            logger.info(f"[AI] OpenRouter ({model_name}) response OK")
                            return text
            except Exception as e:
                logger.warning(f"[AI] OpenRouter ({model_name}) error: {e}")
                continue

        return None

    def _generate_local_fallback(self, query: str, context: dict = None) -> str:
        """Tier 3: Rule-based local fallback using actual data from context with a semantic keyword router."""
        ctx = context or {}
        q = query.lower()

        # Dynamic context stats
        holdings = ctx.get("portfolio_holdings", [])
        holdings_count = len(holdings)
        sectors = list(set(h.get("sector", "") for h in holdings if h.get("sector")))
        sectors_str = ", ".join(sectors) if sectors else "Multiple Sectors"

        # Get active yields from context if possible
        treasury = ctx.get("treasury_data", {})
        curve = treasury.get("curve", {})
        ten_y_val = "4.25%"
        two_y_val = "4.45%"
        if curve:
            if isinstance(curve.get("10Y"), dict) and curve["10Y"].get("value"):
                ten_y_val = f"{curve['10Y']['value']}%"
            elif isinstance(curve.get("10Y"), (int, float)):
                ten_y_val = f"{curve['10Y']}%"
            if isinstance(curve.get("2Y"), dict) and curve["2Y"].get("value"):
                two_y_val = f"{curve['2Y']['value']}%"
            elif isinstance(curve.get("2Y"), (int, float)):
                two_y_val = f"{curve['2Y']}%"

        # Initialize fallback variables
        response_data = None

        # 1. Why are my bonds falling?
        if any(
            w in q
            for w in [
                "fall",
                "drop",
                "down",
                "loss",
                "losing",
                "decrease",
                "performance",
                "falling",
            ]
        ):
            response_data = {
                "response": f"### Why Are Your Bonds Falling?\n\nFixed-income asset prices move **inversely** to interest rates. Due to the Federal Reserve's restrictive monetary policy tightening cycle, benchmark Treasury yields have risen significantly (e.g., 2-Year Treasury is at **{two_y_val}** and 10-Year is at **{ten_y_val}**).\n\nWhen new bonds are issued at these higher yields, existing bonds with lower coupons become less attractive, forcing their market price to decline to realign their yield-to-maturity with the market. This is known as **duration risk** or **interest rate risk**.\n\n#### Portfolio Impact:\n- Your portfolio holds **{holdings_count}** active positions, which are subject to duration-based price volatility.\n- Longer-maturity bonds in your portfolio will experience larger clean price drawdowns compared to shorter-maturity instruments.",
                "summary": f"Your bond prices are falling because interest rates have risen (10-Year Treasury at {ten_y_val}). Existing lower-coupon bonds lose market value to align their yield-to-maturity with newer, higher-yielding issues. This duration risk is typical during monetary tightening cycles.",
                "risk_analysis": f"Duration risk is currently elevated. A 100 bps parallel rise in rates would cause price drawdowns proportional to each bond's modified duration.",
                "portfolio_impact": f"Your portfolio with {holdings_count} positions in {sectors_str} is exposed to rate volatility. Shorter-duration holdings are relatively insulated.",
                "related_holdings": (
                    [h.get("issuer", "") for h in holdings[:3]]
                    if holdings
                    else ["Corporate Bonds", "Treasury Notes"]
                ),
                "recommended_actions": [
                    "Shift exposure to short-duration instruments (1-3Y tenors) to reduce interest rate sensitivity.",
                    "Establish a rolling bond ladder to reinvest maturing cash at higher prevailing rates.",
                    "Allocate a portion to floating-rate notes (FRNs) that adjust coupon payouts upward with interest rates.",
                ],
                "sources": ["FRED", "Treasury.gov", "YieldLens Quant Engine"],
                "confidence_score": 95,
            }

        # 2. Show safest bonds under 5 years
        elif any(
            w in q
            for w in [
                "safe",
                "safest",
                "under 5",
                "short term",
                "low risk",
                "preservation",
            ]
        ):
            response_data = {
                "response": f"### Safest Bonds under 5 Years\n\nFor capital preservation and liquidity, the safest fixed-income assets with maturities under 5 years include:\n\n1. **U.S. Treasury Bills & Notes**: Backed by the full faith and credit of the U.S. government, offering virtually zero default risk. Currently, U.S. Treasury Bills yield between **4.30%** and **4.50%**.\n2. **AAA/AA Corporate Commercial Paper**: Extremely short-term, prime-grade debt issued by blue-chip financial and industrial corporations.\n3. **High-Grade Municipal Bonds**: Particularly pre-refunded or AAA-rated general obligation (GO) municipal issues, which offer tax-free interest income for high-bracket investors.\n\n#### Portfolio Recommendation:\n- Transitioning a portion of your portfolio's cash or maturing proceeds to U.S. Treasury Bills is highly recommended to secure high yields with zero credit risk.",
                "summary": "The safest bonds under 5 years are U.S. Treasury Bills/Notes and AAA corporate paper. They carry zero default risk and offer attractive yields (currently ~4.40%) during an inverted yield curve.",
                "risk_analysis": "Default risk is negligible. The primary risks are reinvestment risk (rates dropping before maturity) and inflation/purchasing-power risk.",
                "portfolio_impact": f"Adding safe, short-duration assets stabilizes your {holdings_count}-position portfolio value and increases immediate cash equivalents.",
                "related_holdings": (
                    [h.get("issuer", "") for h in holdings[:2]]
                    if holdings
                    else ["US Treasury Bills", "AAA Prime Paper"]
                ),
                "recommended_actions": [
                    "Allocate to 3-Month and 6-Month U.S. Treasury Bills to lock in yields above 4.40% with zero credit risk.",
                    "Use short-term Treasury ETFs to maintain excellent liquidity.",
                    "Establish a short-term Treasury ladder to ensure rolling liquidity.",
                ],
                "sources": ["Treasury.gov", "Bloomberg Credit", "FRED"],
                "confidence_score": 98,
            }

        # 3. Compare TIPS vs Treasury for inflation protection
        elif any(
            w in q
            for w in [
                "tips",
                "inflation",
                "protection",
                "breakeven",
                "real yield",
                "nominal",
            ]
        ):
            response_data = {
                "response": f"### TIPS vs. Nominal Treasuries\n\n**Treasury Inflation-Protected Securities (TIPS)** differ from nominal Treasuries in how they manage purchasing power risk:\n\n- **TIPS**: The principal value of TIPS adjusts dynamically in line with the Consumer Price Index (CPI). When inflation rises, the principal increases, and the coupon payment (which is a fixed % of the adjusted principal) also rises. At maturity, you receive either the adjusted principal or original par value, whichever is greater.\n- **Nominal Treasuries**: Pay a fixed coupon and static principal at maturity, meaning their real purchasing power is severely eroded during unexpected inflationary spikes.\n\n#### The Breakeven Inflation Rate:\n- The key decision metric is the **10-Year Breakeven Inflation Rate** (currently around **2.35%**). If realized CPI inflation averages *above* this rate, TIPS will outperform nominal Treasuries. If inflation is lower, nominal Treasuries will outperform.",
                "summary": "TIPS adjust their principal value with the CPI to protect purchasing power, while nominal Treasuries pay a static coupon. TIPS outperform nominal Treasuries if realized CPI exceeds the market breakeven inflation rate (~2.35%).",
                "risk_analysis": "TIPS are still vulnerable to duration risk from rising real interest rates. If inflation declines rapidly, nominal Treasuries will deliver higher real returns.",
                "portfolio_impact": "Integrating TIPS introduces an explicit hedge against unexpected inflation shocks, protecting the real purchasing power of your portfolio.",
                "related_holdings": ["TIPS ETFs", "Nominal US Treasuries"],
                "recommended_actions": [
                    "Overweight TIPS if you project inflation to remain structural or exceed the 2.35% breakeven rate.",
                    "Maintain nominal Treasuries to hedge against deflationary or recessionary market corrections.",
                    "Utilize shorter-duration TIPS to isolate the inflation protection while muting duration volatility.",
                ],
                "sources": [
                    "FRED",
                    "Bureau of Labor Statistics",
                    "YieldLens Quant Engine",
                ],
                "confidence_score": 92,
            }

        # 4. Explain convexity
        elif any(
            w in q
            for w in ["convexity", "second-order", "duration", "curve", "curvature"]
        ):
            response_data = {
                "response": "### Understanding Bond Convexity\n\n**Convexity** is a critical second-order measure of the relationship between bond prices and interest rates, indicating how a bond's duration changes in response to yield shifts:\n\n- **The Curvature Concept**: While *duration* assumes a linear relation (a straight tangent line) between price and yield, the actual relation is curved (convex). Duration is the first derivative, and convexity is the second derivative of the price-yield function.\n- **Positive Convexity**: Standard non-callable bonds possess positive convexity. This means that when interest rates fall, the price increases at a *faster* rate than duration would predict. Conversely, when rates rise, the price falls at a *slower* rate. Positive convexity is highly beneficial to investors.\n- **Negative Convexity**: Bonds with embedded options (such as callable corporate bonds or mortgage-backed securities) display negative convexity. When rates drop, their price rise is capped because they are likely to be called/prepaid.",
                "summary": "Convexity is a second-order risk measure showing how a bond's duration changes as yields change. Positive convexity means bond prices rise faster as rates drop and fall slower as rates rise—providing a beneficial buffer.",
                "risk_analysis": "Negative convexity is a key concern for callable corporate bonds, exposing investors to call risk and extension risk under shifting interest rate environments.",
                "portfolio_impact": f"Your portfolio contains {holdings_count} positions. Calculating portfolio-weighted convexity ensures non-linear rate sensitivity is within targets.",
                "related_holdings": (
                    [h.get("issuer", "") for h in holdings[:2]]
                    if holdings
                    else ["Long-Term Treasuries", "Callable Corporates"]
                ),
                "recommended_actions": [
                    "Target non-callable, high-convexity long-term Treasuries to maximize capital gains in falling-rate environments.",
                    "Limit exposure to highly callable corporate issues when interest rate volatility is high.",
                    "Include portfolio-weighted convexity in standard risk reports alongside modified duration.",
                ],
                "sources": ["YieldLens Quant Engine", "BlackRock Aladdin Analytics"],
                "confidence_score": 94,
            }

        # 5. What happens to bond prices if the Fed cuts rates?
        elif any(
            w in q for w in ["cut", "rate cut", "cuts rates", "easing", "policy change"]
        ):
            response_data = {
                "response": f"### Impact of a Federal Reserve Rate Cut\n\nWhen the Federal Reserve cuts the federal funds rate, it triggers a chain of events across the fixed-income markets:\n\n1. **Bond Price Appreciation**: Clean prices of existing fixed-rate bonds will **increase** as market yields move lower to match the Fed's stance. This is because existing coupons become more valuable relative to newly issued bonds.\n2. **Duration Sensitivity**: Longer-duration bonds will capture the largest capital gains. For example, a bond with a 10-year duration will appreciate approximately **10%** for a 1.00% drop in yields.\n3. **Reinvestment Risk**: Short-term yields (T-Bills, money market funds) will drop immediately, meaning matured principal and coupon income must be reinvested at lower prevailing rates.",
                "summary": "When the Fed cuts rates, bond yields drop and existing bond prices rise. Longer-duration bonds experience the largest capital gains, while short-term yields fall quickly, introducing reinvestment risk for cash holdings.",
                "risk_analysis": "Reinvestment risk becomes the primary threat, as incoming cash flows will be deployed into significantly lower-yielding instruments.",
                "portfolio_impact": f"A Fed easing cycle will boost the market value of your {holdings_count}-position portfolio, particularly in longer-maturity holdings.",
                "related_holdings": (
                    [h.get("issuer", "") for h in holdings[:3]]
                    if holdings
                    else ["Treasury Notes", "IG Corporate Bonds"]
                ),
                "recommended_actions": [
                    "Extend portfolio duration prior to the first rate cut to lock in high yields and maximize clean price appreciation.",
                    "Overweight high-quality corporate bonds to benefit from the spread compression that typically accompanies monetary easing.",
                    "Transition excess cash out of money market instruments into intermediate-term bonds.",
                ],
                "sources": ["Federal Reserve FOMC", "YieldLens Quant Engine", "FRED"],
                "confidence_score": 96,
            }

        # 6. Explain the yield curve inversion
        elif any(
            w in q
            for w in [
                "inversion",
                "inverted",
                "yield curve",
                "10y2y",
                "2-year",
                "10-year",
                "recession",
            ]
        ):
            response_data = {
                "response": f"### The Inverted Yield Curve Explained\n\nA **yield curve inversion** occurs when short-term interest rates exceed long-term interest rates. The most closely monitored spread is the **2-Year vs 10-Year Treasury Yield Spread (10Y2Y)**, which is currently inverted at **{two_y_val} (2Y)** vs **{ten_y_val} (10Y)**.\n\n#### Why It Matters:\n- **Recession Indicator**: Historically, a sustained inversion of the 10Y2Y spread has been a highly reliable leading indicator of an economic recession, typically preceding a downturn by 12 to 18 months.\n- **Market Expectations**: It signals that investors expect economic growth to slow down and inflation to cool, which will eventually force the central bank to cut rates in the future.\n- **Banking Stress**: Inversion squeezes bank net interest margins, as banks typically borrow short-term (paying high rates) and lend long-term (receiving lower rates).",
                "summary": f"A yield curve inversion occurs when short-term yields (2Y at {two_y_val}) exceed long-term yields (10Y at {ten_y_val}). It indicates market expectations of slowing growth and future rate cuts, and acts as a reliable leading recession indicator.",
                "risk_analysis": "Economic contraction risk is elevated. Credit default risks generally increase in the quarters following a curve inversion.",
                "portfolio_impact": "An inverted curve lets you capture high short-term yields with minimal interest rate risk, but exposes the portfolio to credit risks if a recession ensues.",
                "related_holdings": ["US 2-Year Treasury", "US 10-Year Treasury"],
                "recommended_actions": [
                    "Lock in high risk-free yields in short-term instruments (T-Bills, 2Y Notes) while the inversion persists.",
                    "Formulate a plan to shift into long-duration bonds as the curve begins to steepen ('disinversion'), which historically occurs right at the onset of a recession.",
                    "Focus portfolio allocations on high-credit-quality issuers (IG or Treasury) to cushion against default risk.",
                ],
                "sources": [
                    "FRED",
                    "National Bureau of Economic Research (NBER)",
                    "YieldLens Research",
                ],
                "confidence_score": 97,
            }

        # 7. Credit quality / risk / credit analysis queries
        elif any(
            w in q
            for w in [
                "credit",
                "rating",
                "corporate",
                "default",
                "spreads",
                "z-score",
                "merton",
            ]
        ):
            response_data = {
                "response": f"### Corporate Credit Risk & Spread Analysis\n\nCorporate credit analysis requires examining both financial metrics and market-implied pricing spreads over risk-free Treasuries (IG spreads currently around **100 bps**):\n\n1. **Solvency & Capital Structure**: Leverage ratios (Total Debt/EBITDA) and interest coverage ratios (EBITDA/Interest Expense) define an issuer's default buffer.\n2. **Quantitative Scores**: The **Altman Z-Score** measures corporate bankruptcy risk, while the **Merton Distance-to-Default** combines capital structure with stock volatility to estimate physical default probabilities.\n3. **Credit Spreads**: High-yield spreads (~360 bps) compensate for default volatility. Wider spreads imply credit deterioration.",
                "summary": "Corporate credit risk is evaluated via balance sheet leverage, interest coverage ratios, Altman Z-Scores, and physical default models. Credit spreads compensate investors for default volatility.",
                "risk_analysis": "Credit spread widening reflects macroeconomic stress, driving down corporate bond prices even if benchmark interest rates remain flat.",
                "portfolio_impact": f"Your portfolio has {holdings_count} positions. Active monitoring of rating migrations protects against credit downgrades.",
                "related_holdings": (
                    [h.get("issuer", "") for h in holdings[:3]]
                    if holdings
                    else ["Corporate Issuers", "High-Yield Bonds"]
                ),
                "recommended_actions": [
                    "Assess all holdings' Altman Z-Scores to identify potential default candidates.",
                    "Overweight investment-grade corporate bonds with robust interest coverage during macroeconomic uncertainty.",
                    "Monitor rating agency outlooks to preemptively manage downgrade exposure.",
                ],
                "sources": [
                    "Bloomberg Credit",
                    "Moody's Analytics",
                    "YieldLens Credit Engine",
                ],
                "confidence_score": 94,
            }

        # 8. Dynamic Fallback for General Queries
        if not response_data:
            response_data = {
                "response": f"### Fixed-Income Analysis: '{query}'\n\nThank you for your inquiry regarding **'{query}'** within the fixed-income ecosystem.\n\nBased on your query, here is a professional, data-driven analysis compiled from active market intelligence:\n\n- **Interest Rate Environment**: Benchmark Treasury yields are currently trading at **{two_y_val} (2-Year)** and **{ten_y_val} (10-Year)**, maintaining a spread that reflects monetary policy expectations.\n- **Asset Sensitivity**: Duration management remains paramount. In this environment, yield curves continue to adjust to incoming macro indicators (inflation, employment, and central bank commentary).\n- **Portfolio Context**: Your portfolio consists of **{holdings_count}** active positions across **{sectors_str}**. Managing the weighted average maturity and duration of these holdings is highly recommended to protect clean price valuations.",
                "summary": f"Active analysis regarding '{query}'. The yield curve remains the core driver of pricing (10Y at {ten_y_val}), requiring active duration and credit risk monitoring across your portfolio.",
                "risk_analysis": "Macro indicators and Federal Reserve policy updates pose the primary near-term risk to fixed-income valuations.",
                "portfolio_impact": f"Review duration sensitivity and credit exposure of your {holdings_count} holdings to hedge against sudden interest rate or spread shocks.",
                "related_holdings": (
                    [h.get("issuer", "") for h in holdings[:3]]
                    if holdings
                    else ["Treasury Notes", "Corporate Bonds"]
                ),
                "recommended_actions": [
                    "Calibrate portfolio duration with current yield curve expectations.",
                    "Monitor incoming macro data (CPI, non-farm payrolls) for directional rate cues.",
                    "Diversify corporate exposure to mitigate issuer-specific credit risks.",
                ],
                "sources": ["FRED", "YieldLens Quant Engine", "Bloomberg Market Brief"],
                "confidence_score": 85,
            }

        # Return as structured JSON string so it parses perfectly!
        return json.dumps(response_data)

    def _generate_with_failover(
        self,
        prompt: str,
        max_tokens: int = 1024,
        context: dict = None,
        query: str = None,
    ) -> tuple:
        """Generate with full 3-tier failover. Returns (text, source_model)."""
        # Tier 1: Gemini
        result = self._generate_gemini(prompt, max_tokens)
        if result:
            return result, "gemini-2.0-flash"

        # Tier 2: OpenRouter
        result = self._generate_openrouter(prompt, max_tokens)
        if result:
            return result, "openrouter"

        # Tier 3: Local fallback
        fallback_query = (
            query or prompt[:200]
        )  # Extract approximate query if not provided
        result = self._generate_local_fallback(fallback_query, context)
        return result, "local-fallback"

    # ══════════════════════════════════════════════════════════════════════════
    # CONTEXT ENGINE
    # ══════════════════════════════════════════════════════════════════════════

    def _build_rich_context(self, extra_context: dict = None) -> dict:
        """Build comprehensive context from all available data sources."""
        context = extra_context.copy() if extra_context else {}

        # 1. Treasury data from cache
        try:
            treasury = cache.get("fred_yield_curve")
            if treasury:
                context["treasury_data"] = treasury
        except Exception:
            pass

        # 2. Macro indicators from cache
        try:
            macro = cache.get("fred_economic_indicators")
            if macro:
                context["macro_data"] = macro
        except Exception:
            pass

        # 3. Recent news from MongoDB
        try:
            from database.mongo import get_db

            db = get_db()
            recent_news = list(
                db["news_articles"]
                .find({}, {"title": 1, "categories": 1, "source": 1, "_id": 0})
                .sort("fetched_at", -1)
                .limit(5)
            )
            if recent_news:
                context["recent_news"] = recent_news
        except Exception:
            pass

        # 4. Portfolio data
        try:
            from database.mongo import get_db

            db = get_db()
            portfolios = list(db["portfolios"].find().limit(3))
            all_holdings = []
            for pf in portfolios:
                for h in pf.get("holdings", []):
                    bond_id = h.get("bond_id")
                    if bond_id:
                        bond = db["bonds"].find_one({"_id": bond_id})
                        if bond:
                            all_holdings.append(
                                {
                                    "bond_id": str(bond_id),
                                    "bond_name": bond.get("issuer", "")
                                    + " "
                                    + str(bond.get("coupon_rate", "")),
                                    "issuer": bond.get("issuer", ""),
                                    "sector": bond.get("sector", ""),
                                    "type": bond.get("type", ""),
                                    "rating": bond.get("rating", ""),
                                    "coupon_rate": bond.get("coupon_rate"),
                                    "maturity_date": bond.get("maturity_date", ""),
                                    "quantity": h.get("quantity", 0),
                                    "purchase_price": h.get("purchase_price"),
                                }
                            )
            context["portfolio_holdings"] = all_holdings
            context["has_portfolio"] = len(all_holdings) > 0

            # Calculate sector exposure
            sector_counts = {}
            for h in all_holdings:
                sector = h.get("sector", "Other")
                sector_counts[sector] = sector_counts.get(sector, 0) + 1
            context["sector_exposure"] = sector_counts

        except Exception:
            context["portfolio_holdings"] = []
            context["has_portfolio"] = False

        # 5. Watchlists
        try:
            from database.mongo import get_db

            db = get_db()
            watchlists = list(db["watchlists"].find().limit(3))
            wl_bonds = []
            for wl in watchlists:
                for bid in wl.get("bonds", []):
                    bond = db["bonds"].find_one({"_id": bid})
                    if bond:
                        wl_bonds.append(
                            bond.get("issuer", "")
                            + " "
                            + str(bond.get("coupon_rate", ""))
                        )
            context["watchlist_items"] = wl_bonds
        except Exception:
            context["watchlist_items"] = []

        # 6. Active alerts
        try:
            from database.mongo import get_db

            db = get_db()
            active_alerts = db["alerts"].count_documents({"triggered": False})
            context["active_alerts"] = active_alerts
        except Exception:
            context["active_alerts"] = 0

        return context

    def _format_context_for_prompt(self, context: dict) -> str:
        """Format context dict into a concise prompt section."""
        parts = []

        # Treasury
        treasury = context.get("treasury_data", {})
        if treasury:
            curve = treasury.get("curve", {})
            rates = []
            for tenor in ["2Y", "5Y", "10Y", "30Y"]:
                data = curve.get(tenor, {})
                if isinstance(data, dict) and data.get("value") is not None:
                    change = data.get("change", 0)
                    rates.append(f"{tenor}: {data['value']}% (Δ {change:+.2f})")
            if rates:
                parts.append(f"Treasury Yields: {', '.join(rates)}")

        # Portfolio
        holdings = context.get("portfolio_holdings", [])
        if holdings:
            parts.append(f"Portfolio: {len(holdings)} positions")
            sectors = context.get("sector_exposure", {})
            if sectors:
                parts.append(f"Sector Exposure: {json.dumps(sectors)}")
            for h in holdings[:8]:
                parts.append(
                    f"  - {h.get('issuer', '?')} {h.get('coupon_rate', '?')}% {h.get('rating', '?')} ({h.get('type', '?')}, {h.get('sector', '?')})"
                )

        # Watchlists
        wl = context.get("watchlist_items", [])
        if wl:
            parts.append(f"Watchlist: {', '.join(wl[:5])}")

        # Macro
        macro = context.get("macro_data", {})
        if macro:
            key_indicators = []
            for key in ["FEDFUNDS", "CPIAUCSL", "UNRATE", "T10Y2Y", "BAMLC0A0CM"]:
                data = macro.get(key, {})
                if isinstance(data, dict) and data.get("value") is not None:
                    key_indicators.append(f"{data.get('name', key)}: {data['value']}")
            if key_indicators:
                parts.append(f"Macro: {', '.join(key_indicators)}")

        # News
        news = context.get("recent_news", [])
        if news:
            headlines = [n.get("title", "") for n in news[:3] if n.get("title")]
            if headlines:
                parts.append(f"Recent News: {' | '.join(headlines)}")

        # Alerts
        alerts = context.get("active_alerts", 0)
        if alerts:
            parts.append(f"Active Alerts: {alerts}")

        return "\n".join(parts) if parts else "No additional context available."

    # ══════════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ══════════════════════════════════════════════════════════════════════════

    def answer_query(self, query: str, context: dict = None) -> dict:
        """
        Answer a user query with full context and structured output.
        Uses 3-tier failover. NEVER returns empty/error.
        """
        cache_key = f"ai_query_{hash(query)}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Build rich context
        rich_ctx = self._build_rich_context(context)
        ctx_str = self._format_context_for_prompt(rich_ctx)

        # Build prompt
        prompt = f"""{SYSTEM_PROMPT}

Current Market Context:
{ctx_str}

User Query: {query}

{STRUCTURED_OUTPUT_PROMPT}"""

        # Generate with failover
        raw_result, source_model = self._generate_with_failover(
            prompt, max_tokens=1024, context=rich_ctx, query=query
        )

        # Try to parse structured JSON
        response = self._parse_structured_response(
            raw_result, query, source_model, rich_ctx
        )
        response["source"] = source_model

        cache.set(cache_key, response, ttl=Config.AI_CACHE_TTL)
        return response

    def generate_market_brief(
        self, treasury_data: dict = None, macro_data: dict = None
    ) -> str:
        """Generate a daily market brief."""
        cache_key = "ai_market_brief"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Build context
        context_parts = []
        if treasury_data:
            curve = treasury_data.get("curve", {})
            rates_str = ", ".join(
                [
                    f"{k}: {v.get('value', 'N/A')}% (Δ {v.get('change', 0):+.3f})"
                    for k, v in curve.items()
                    if isinstance(v, dict) and v.get("value") is not None
                ]
            )
            if rates_str:
                context_parts.append(f"Current Treasury Yields: {rates_str}")

        if macro_data:
            macro_str = ", ".join(
                [
                    f"{v.get('name', k)}: {v.get('value', 'N/A')}"
                    for k, v in macro_data.items()
                    if isinstance(v, dict) and v.get("value") is not None
                ]
            )
            if macro_str:
                context_parts.append(f"Macro Indicators: {macro_str}")

        # Include recent news headlines
        try:
            from database.mongo import get_db

            db = get_db()
            recent_news = list(
                db["news_articles"]
                .find({}, {"title": 1, "_id": 0})
                .sort("fetched_at", -1)
                .limit(5)
            )
            if recent_news:
                headlines = [n["title"] for n in recent_news if n.get("title")]
                if headlines:
                    context_parts.append(f"Recent Headlines: {' | '.join(headlines)}")
        except Exception:
            pass

        if context_parts:
            prompt = f"""{SYSTEM_PROMPT}

Write a concise daily market brief (250-350 words) for professional bond investors.

Current Market Data:
{chr(10).join(context_parts)}

Include: Treasury market analysis with specific yield levels, credit spread commentary,
key macro themes with data points, and near-term outlook with actionable insights.
Use professional financial language. Format with markdown headers and bullet points.
Reference specific numbers from the data provided."""

            result, source = self._generate_with_failover(prompt, max_tokens=1500)
            if result and source != "local-fallback":
                cache.set(cache_key, result, ttl=Config.AI_CACHE_TTL)
                return result

        # Fallback
        cache.set(cache_key, FALLBACK_MARKET_BRIEF, ttl=Config.AI_CACHE_TTL)
        return FALLBACK_MARKET_BRIEF

    def analyze_credit_risk(self, issuer: str, bond_data: dict = None) -> dict:
        """Generate credit risk analysis for an issuer."""
        cache_key = f"ai_credit_{issuer}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        context = ""
        if bond_data:
            context = f"\nBond details: Rating={bond_data.get('rating', 'N/A')}, Coupon={bond_data.get('coupon_rate', 'N/A')}%, Sector={bond_data.get('sector', 'N/A')}, Type={bond_data.get('type', 'N/A')}"

        prompt = f"""{SYSTEM_PROMPT}

Provide a credit risk assessment for {issuer}.{context}

Return a JSON object with these fields:
- "summary": 2-3 sentence credit overview with specific metrics
- "strengths": array of 4 key credit strengths
- "risks": array of 4 key credit risks
- "recommendation": one-line recommendation (Buy/Hold/Sell with brief rationale)
- "confidence_score": integer 1-100

Return ONLY the JSON, no markdown formatting."""

        result, source = self._generate_with_failover(prompt, max_tokens=600)
        if result and source != "local-fallback":
            try:
                cleaned = result.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                parsed = json.loads(cleaned)
                parsed["issuer"] = issuer
                parsed["source"] = source
                cache.set(cache_key, parsed, ttl=Config.AI_CACHE_TTL)
                return parsed
            except json.JSONDecodeError:
                # Try to extract JSON from mixed text
                try:
                    start = cleaned.index("{")
                    end = cleaned.rindex("}") + 1
                    parsed = json.loads(cleaned[start:end])
                    parsed["issuer"] = issuer
                    parsed["source"] = source
                    cache.set(cache_key, parsed, ttl=Config.AI_CACHE_TTL)
                    return parsed
                except (ValueError, json.JSONDecodeError):
                    pass

        # Fallback
        result = {
            **FALLBACK_CREDIT_ANALYSIS,
            "issuer": issuer,
            "source": "fallback",
            "confidence_score": 45,
        }
        cache.set(cache_key, result, ttl=Config.AI_CACHE_TTL)
        return result

    def explain_concept(self, concept: str) -> str:
        """Explain a financial concept."""
        prompt = f"""{SYSTEM_PROMPT}

Explain the fixed-income concept "{concept}" for a bond investor.
Keep it concise (150-200 words), professional, and practical.
Include a real-world example with specific numbers.
Use markdown formatting."""

        result, source = self._generate_with_failover(prompt, max_tokens=500)
        if result and source != "local-fallback":
            return result

        explanations = {
            "duration": "**Duration** measures a bond's price sensitivity to interest rate changes. A duration of 5 years means the bond's price will move approximately 5% for every 1% change in rates. Higher duration = more interest rate risk.\n\n**Example:** If you hold a bond with modified duration of 7 years and rates rise 0.50%, expect approximately a 3.5% price decline.",
            "convexity": "**Convexity** captures the non-linear relationship between bond prices and yields. It measures how duration changes as yields change. Positive convexity means bonds gain more from falling rates than they lose from rising rates.\n\n**Example:** Two bonds with identical 5-year duration but different convexity will behave differently in a rate shock — the higher-convexity bond outperforms in both directions.",
            "ytm": "**Yield to Maturity (YTM)** is the total expected return if you hold a bond until maturity. It accounts for coupon payments, time to maturity, and the difference between purchase price and par value.\n\n**Example:** A bond trading at $950 with a 4% coupon and 5 years to maturity has a YTM above 4% because you also earn the $50 discount to par.",
            "spread": "**Credit Spread** is the yield difference between a corporate bond and a risk-free Treasury bond of similar maturity. Wider spreads indicate higher perceived credit risk or market stress.\n\n**Example:** If a 10Y corporate bond yields 5.50% and the 10Y Treasury yields 4.25%, the credit spread is 125 basis points (1.25%).",
        }
        return explanations.get(
            concept.lower(),
            f"**{concept}**: A key concept in fixed-income investing. This concept relates to bond valuation and risk assessment. For detailed AI-powered explanations, configure your Gemini API key in Settings.",
        )

    def generate_news_summary(self, articles: list) -> str:
        """Generate an AI summary of recent news articles."""
        if not articles:
            return "No recent news to summarize."

        headlines = "\n".join(
            [
                f"- {a.get('title', 'N/A')} ({a.get('source', 'Unknown')})"
                for a in articles[:10]
            ]
        )

        prompt = f"""{SYSTEM_PROMPT}

Summarize these financial news headlines into a brief market intelligence update (100-150 words).
Focus on implications for fixed-income investors.

Headlines:
{headlines}

Write in professional analyst style. Highlight the most market-moving items first."""

        result, source = self._generate_with_failover(prompt, max_tokens=400)
        if result:
            return result

        # Fallback: just list headlines
        return "**Market Headlines:**\n" + headlines

    # ══════════════════════════════════════════════════════════════════════════
    # STRUCTURED OUTPUT PARSING
    # ══════════════════════════════════════════════════════════════════════════

    def _parse_structured_response(
        self, raw: str, query: str, source: str, context: dict
    ) -> dict:
        """Parse AI output into structured format, with fallback."""
        if not raw:
            return self._build_fallback_response(query, source, context)

        # Try JSON parse
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            # Find JSON object in text
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                parsed = json.loads(cleaned[start_idx:end_idx])
                # Ensure required fields
                return {
                    "response": parsed.get("response", parsed.get("summary", raw)),
                    "summary": parsed.get("summary", ""),
                    "risk_analysis": parsed.get("risk_analysis", ""),
                    "portfolio_impact": parsed.get("portfolio_impact", ""),
                    "related_holdings": parsed.get("related_holdings", []),
                    "recommended_actions": parsed.get("recommended_actions", []),
                    "sources": parsed.get("sources", []),
                    "confidence_score": parsed.get("confidence_score", 70),
                    "query": query,
                    "source": source,
                }
        except (json.JSONDecodeError, ValueError):
            pass

        # JSON parse failed — wrap raw text as response
        return {
            "response": raw,
            "summary": raw[:300] if len(raw) > 300 else raw,
            "risk_analysis": "",
            "portfolio_impact": "",
            "related_holdings": [],
            "recommended_actions": [],
            "sources": [],
            "confidence_score": 60 if source != "local-fallback" else 35,
            "query": query,
            "source": source,
        }

    def _build_fallback_response(self, query: str, source: str, context: dict) -> dict:
        """Build a data-driven fallback response when all AI fails."""
        holdings = context.get("portfolio_holdings", [])
        treasury = context.get("treasury_data", {})

        summary_parts = [f"Regarding '{query}':"]
        summary_parts.append(
            "The fixed income market continues to present opportunities across the yield curve."
        )

        if treasury:
            curve = treasury.get("curve", {})
            ten_y = curve.get("10Y", {})
            if isinstance(ten_y, dict) and ten_y.get("value"):
                summary_parts.append(f"The 10-year Treasury is at {ten_y['value']}%.")

        if holdings:
            summary_parts.append(
                f"Your portfolio has {len(holdings)} positions across {len(set(h.get('sector', '') for h in holdings))} sectors."
            )

        return {
            "response": " ".join(summary_parts)
            + "\n\n**Key considerations:**\n- Duration risk remains a factor with rate uncertainty\n- Credit quality fundamentals are generally stable\n- Municipal bonds offer attractive tax-equivalent yields\n- Short-duration instruments provide competitive risk-adjusted returns",
            "summary": " ".join(summary_parts),
            "risk_analysis": "Monitor duration exposure and credit spread movements.",
            "portfolio_impact": (
                f"Portfolio has {len(holdings)} positions — review duration sensitivity."
                if holdings
                else "No portfolio data available for impact analysis."
            ),
            "related_holdings": (
                [h.get("issuer", "") for h in holdings[:5]] if holdings else []
            ),
            "recommended_actions": [
                "Review portfolio duration alignment with rate outlook",
                "Monitor credit spreads for early warning signals",
                "Consider rebalancing if sector concentration exceeds targets",
            ],
            "sources": ["FRED", "Portfolio Data"],
            "confidence_score": 35,
            "query": query,
            "source": source,
        }


# Singleton
ai_service = AIService()
