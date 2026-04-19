"""Central registry of all 22 specialist PE agents.

Each `AgentSpec` is the source of truth for routing, UI rendering, and prompt
loading. The agent module (in agents/<category>/<slug>.py) owns its TOOLS +
build() but imports its SPEC from here to avoid drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentSpec:
    slug: str
    name: str
    category: str        # sourcing | underwriting | diligence | capital | portfolio
    icon: str            # unicode glyph for UI
    one_liner: str       # marketing sub-heading
    description: str     # full sentence for /agents page
    prefix: str          # router prefix (e.g., "triage:")
    example_prompts: tuple[str, ...] = field(default_factory=tuple)


CATEGORIES: list[dict] = [
    {
        "key": "sourcing",
        "name": "Deal Sourcing & Screening",
        "blurb": "Find proprietary deals before they hit the auction.",
        "icon": "◉",
    },
    {
        "key": "underwriting",
        "name": "LBO Underwriting Engine",
        "blurb": "Teaser to IC-ready LBO model in hours.",
        "icon": "◈",
    },
    {
        "key": "diligence",
        "name": "Due Diligence Stack",
        "blurb": "VDR audited, QoE validated, risks surfaced early.",
        "icon": "◆",
    },
    {
        "key": "capital",
        "name": "Capital & LP Relations",
        "blurb": "IC memos, teasers and LP updates your GP will sign.",
        "icon": "◐",
    },
    {
        "key": "asset_mgmt",
        "name": "Portfolio Operations",
        "blurb": "Drive EBITDA growth and value creation post-close.",
        "icon": "◼",
    },
]


AGENTS: tuple[AgentSpec, ...] = (
    # Deal Sourcing & Screening
    AgentSpec(
        slug="market_scanner", name="Market Scanner",
        category="sourcing", icon="⚯", prefix="scan:",
        one_liner="PitchBook + banker feeds + proprietary outreach, ranked by fit.",
        description="Continuously scans sell-side teasers, PitchBook/Grata/SourceScrub feeds, and proprietary founder outreach channels, deduplicating deals and surfacing those that fit your fund's mandate.",
        example_prompts=(
            "scan: lower-middle-market B2B SaaS, $5-15M EBITDA, North America",
            "What healthcare services deals surfaced this week?",
            "Any founder-owned industrial companies in the Midwest under $50M EV?",
        ),
    ),
    AgentSpec(
        slug="deal_triage", name="Deal Triage Agent",
        category="sourcing", icon="✓", prefix="triage:",
        one_liner="Go / no-go in 90 seconds against your fund mandate.",
        description="Screens a deal against your fund's investment criteria — check size, sector, geography, growth profile, leverage capacity — and returns a go/no-go with 3-bullet rationale.",
        example_prompts=(
            "triage: vertical SaaS for auto dealers, $8M EBITDA, 20% growth, $85M ask",
            "Should we pursue the Acme Industrial carve-out? $120M EV, cyclical.",
        ),
    ),
    AgentSpec(
        slug="comp_finder", name="Transaction Comps Finder",
        category="sourcing", icon="≡", prefix="comps:",
        one_liner="M&A + trading comps across 3 sources with outlier filtering.",
        description="Pulls precedent M&A transactions and public trading comps from PitchBook, MergerMarket, and Capital IQ, filters outliers, and returns a tight set for EV/EBITDA and EV/Revenue benchmarking.",
        example_prompts=(
            "comps: vertical SaaS precedent M&A 2022-2024, <$500M EV",
            "Find trading comps for a mid-market HCIT platform",
        ),
    ),
    AgentSpec(
        slug="seller_intent", name="Owner Intent Signal",
        category="sourcing", icon="∿", prefix="intent:",
        one_liner="Ranks companies by likelihood of sale in the next 12 months.",
        description="Combines founder age, fund vintage, sponsor hold period, hiring freezes, and proxy-filing signals to score every target in your pipeline for likelihood of a sale process.",
        example_prompts=(
            "intent: founder-owned logistics companies, $50-150M revenue, southeast US",
            "Which of our tracked sponsor-held assets are past the 5-year hold mark?",
        ),
    ),

    # LBO Underwriting Engine
    AgentSpec(
        slug="rent_roll_parser", name="Cap Table Parser",
        category="underwriting", icon="☰", prefix="cap:",
        one_liner="Any cap table format → clean, fully-diluted ownership with waterfalls.",
        description="Parses cap tables in any format (Excel, PDF, Carta export) into a consistent schema with share classes, options, warrants, liquidation prefs, and fully-diluted ownership.",
        example_prompts=(
            "cap: parse the cap table for Northwind Systems and show fully-diluted ownership",
            "Who has liquidation preference at Northwind Systems?",
        ),
    ),
    AgentSpec(
        slug="t12_normalizer", name="LTM Financials Normalizer",
        category="underwriting", icon="∑", prefix="ltm:",
        one_liner="Messy owner financials → clean, add-back-adjusted LTM EBITDA.",
        description="Normalizes seller-provided financials onto a standard chart of accounts, applies QoE add-backs, separates one-time items, and flags revenue/EBITDA anomalies vs. industry benchmarks.",
        example_prompts=(
            "ltm: normalize the LTM P&L for Northwind Systems with standard add-backs",
            "Compare Northwind EBITDA margin to SaaS peer median",
        ),
    ),
    AgentSpec(
        slug="pro_forma_builder", name="LBO Model Builder",
        category="underwriting", icon="▤", prefix="lbo:",
        one_liner="5-year LBO model with sensitivity grid — editable assumptions.",
        description="Builds a full 5-year LBO model — revenue growth, margin expansion, capex, working capital, debt paydown, exit multiple. Sensitivity grid across the two most impactful variables.",
        example_prompts=(
            "lbo: build a 5-year model for Northwind assuming 12% rev growth, 300bps margin exp",
            "What's the base-case MOIC on Meridian Healthcare at 11x exit?",
        ),
    ),
    AgentSpec(
        slug="debt_stack_modeler", name="Debt Stack Modeler",
        category="underwriting", icon="▥", prefix="debt:",
        one_liner="Unitranche + mezz + revolver — with live leverage + DSCR.",
        description="Models LBO capital structures across senior / unitranche / mezzanine / seller notes / revolver — with total-leverage turns, DSCR, fixed-charge coverage, and refinance sensitivity.",
        example_prompts=(
            "debt: size a 5.5x unitranche on Northwind with a $15M revolver",
            "What's the max leverage at 1.35x FCCR on Meridian Healthcare?",
        ),
    ),
    AgentSpec(
        slug="return_metrics", name="Return Metrics",
        category="underwriting", icon="◈", prefix="ret:",
        one_liner="IRR, MOIC, levered/unlevered, with a value-creation bridge.",
        description="Computes return metrics from projected cash flows — levered/unlevered IRR, MOIC, equity multiple — and breaks results into multiple arbitrage, EBITDA growth, and debt paydown contributions.",
        example_prompts=(
            "ret: compute returns on the Meridian Healthcare model",
            "Show the value-creation bridge for Northwind at 3x MOIC",
        ),
    ),

    # Due Diligence Stack
    AgentSpec(
        slug="doc_room_auditor", name="VDR Auditor",
        category="diligence", icon="☷", prefix="vdr:",
        one_liner="Cross-checks the data room against a full PE DD checklist.",
        description="Audits the seller's VDR against a 140-item PE diligence checklist, flagging missing documents, stale versions, and internal inconsistencies across legal, financial, commercial, and tech DD workstreams.",
        example_prompts=(
            "vdr: audit the data room for Meridian Healthcare",
            "Which DD items are missing in the Northwind VDR?",
        ),
    ),
    AgentSpec(
        slug="lease_abstractor", name="Contract Abstractor",
        category="diligence", icon="▢", prefix="abstract:",
        one_liner="PDFs → contract abstracts with key terms, options, and risks.",
        description="Abstracts PDF contracts (customer MSAs, supplier agreements, employment contracts, IP licenses) into structured records — term, renewal, change-of-control triggers, exclusivity, termination rights — with page-cited references.",
        example_prompts=(
            "abstract: the top-10 customer MSAs for Northwind Systems",
            "Any change-of-control triggers across Meridian's supplier contracts?",
        ),
    ),
    AgentSpec(
        slug="title_zoning", name="Legal & Regulatory Checker",
        category="diligence", icon="◰", prefix="legal:",
        one_liner="Corporate records + litigation + regulatory review, flags material issues.",
        description="Parses corporate minute books, litigation searches, and regulatory filings, flags material breaches, open litigation, licensure gaps, and change-of-control consents required at close.",
        example_prompts=(
            "legal: summarize legal issues for Meridian Healthcare",
            "Are there any HIPAA or state-licensure gaps flagged on the Midwest deal?",
        ),
    ),
    AgentSpec(
        slug="physical_condition", name="Operational Diligence Reviewer",
        category="diligence", icon="⌂", prefix="ops:",
        one_liner="Reads operational DD + QoE, builds a 100-day value-creation plan.",
        description="Reads operational reviews, quality-of-earnings reports, and process maps to extract working capital drag, systems gaps, and unit economics; outputs a 100-day post-close value creation plan.",
        example_prompts=(
            "ops: what operational gaps are flagged for Northwind?",
            "Build a 100-day plan for Meridian Healthcare post-close",
        ),
    ),
    AgentSpec(
        slug="environmental_risk", name="ESG & Compliance Risk Flagger",
        category="diligence", icon="⚠", prefix="esg:",
        one_liner="ESG review — flags environmental, social, governance exposures.",
        description="Reads ESG disclosures, environmental site assessments, worker-safety records, and governance reports to identify ESG exposures, and recommends scope where further review is warranted (Phase II ESA, ethics review, etc).",
        example_prompts=(
            "esg: any environmental liabilities at the Midwest industrial deal?",
            "Summarize ESG risk across my current pipeline",
        ),
    ),

    # Capital & LP Relations
    AgentSpec(
        slug="investor_memo", name="IC Memo Writer",
        category="capital", icon="✎", prefix="memo:",
        one_liner="IC memo your investment committee will actually read.",
        description="Drafts a full investment-committee memo — exec summary, thesis, market, financials, value creation, risks, returns — from the deal's data in your system.",
        example_prompts=(
            "memo: draft the IC memo for Meridian Healthcare",
            "Write a 5-page IC memo for Northwind Systems",
        ),
    ),
    AgentSpec(
        slug="deal_teaser", name="Teaser Designer",
        category="capital", icon="✦", prefix="teaser:",
        one_liner="2-page teaser with thesis, financials, returns snapshot.",
        description="Generates a branded 2-page blind teaser suitable for co-investor or LP distribution — cover, company summary, key financials, returns table, thesis, risks.",
        example_prompts=(
            "teaser: build a co-invest teaser for Meridian Healthcare",
            "Draft a blind LP teaser for the Northwind deal",
        ),
    ),
    AgentSpec(
        slug="lp_update", name="LP Update Generator",
        category="capital", icon="⇄", prefix="lpupd:",
        one_liner="Quarterly LP letter with portfolio performance + outlook.",
        description="Generates a quarterly LP letter pulling fund-level IRR/MOIC/DPI, portfolio-company performance, deals closed/under contract, market outlook, and capital calls.",
        example_prompts=(
            "lpupd: draft Q1 letter for Fund IV LPs",
            "Generate a portfolio update for the Fund III LPs",
        ),
    ),
    AgentSpec(
        slug="fundraising_crm", name="Fundraising CRM Copilot",
        category="capital", icon="◎", prefix="crm:",
        one_liner="LP pipeline ranked by fit, staleness, and commitment size.",
        description="Reads your LP CRM to rank prospects by mandate fit, staleness of last touch, and committed check size — and drafts the next outreach email or meeting prep doc.",
        example_prompts=(
            "crm: who are the top 10 LPs to reach out to for Fund V this week?",
            "Draft a re-engagement email to LPs we haven't touched in 60 days",
        ),
    ),

    # Portfolio Operations
    AgentSpec(
        slug="rent_optimization", name="Pricing Optimization Agent",
        category="asset_mgmt", icon="↗", prefix="price:",
        one_liner="SKU/segment pricing recommendations from elasticity + peer benchmarks.",
        description="Evaluates in-place pricing vs. competitors, elasticity curves, and expiring contract base to recommend price increases at renewal and for new customers.",
        example_prompts=(
            "price: what pricing lift can we capture at Northwind at renewal?",
            "Where is pricing most below market across portcos?",
        ),
    ),
    AgentSpec(
        slug="opex_variance", name="EBITDA Variance Watcher",
        category="asset_mgmt", icon="Δ", prefix="ebitda:",
        one_liner="Monthly EBITDA variance vs. budget — with root-cause commentary.",
        description="Watches monthly actuals vs. budget across all portcos, surfaces variances above your threshold, and suggests root causes from GL-level expense breakouts.",
        example_prompts=(
            "ebitda: what's driving the EBITDA miss at Northwind this quarter?",
            "Show me the top 5 portco-wide EBITDA variances",
        ),
    ),
    AgentSpec(
        slug="capex_prioritizer", name="Value Creation Prioritizer",
        category="asset_mgmt", icon="⚒", prefix="vc:",
        one_liner="Ranks value-creation initiatives by EBITDA impact and ROI.",
        description="Ranks pending value-creation initiatives across portfolio companies by expected EBITDA lift, return on invested capital, and urgency/risk.",
        example_prompts=(
            "vc: rank initiatives across Fund IV by EBITDA impact",
            "Should we prioritize pricing rollout or ERP replacement at Meridian?",
        ),
    ),
    AgentSpec(
        slug="tenant_churn", name="Customer Churn Predictor",
        category="asset_mgmt", icon="∠", prefix="churn:",
        one_liner="Scores each customer's renewal likelihood; drives retention actions.",
        description="Predicts each customer's renewal likelihood from contract economics, usage signals, support tickets, and tenure; prioritizes CS outreach to retain at-risk ARR.",
        example_prompts=(
            "churn: which Northwind customers are at highest renewal risk?",
            "Score renewal likelihood for Meridian's top 20 accounts",
        ),
    ),
)


AGENTS_BY_SLUG: dict[str, AgentSpec] = {a.slug: a for a in AGENTS}
AGENTS_BY_CATEGORY: dict[str, list[AgentSpec]] = {}
for a in AGENTS:
    AGENTS_BY_CATEGORY.setdefault(a.category, []).append(a)


def all_agents() -> tuple[AgentSpec, ...]:
    return AGENTS


def by_slug(slug: str) -> AgentSpec | None:
    return AGENTS_BY_SLUG.get(slug)
