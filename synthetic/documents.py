"""DD document bodies (QoE, legal, ESG, tax, tech DDQ, industry) for RAG indexing."""

from __future__ import annotations

import random
from datetime import date


def qoe_report(company: dict, rng: random.Random) -> str:
    rev = float(company["revenue_ltm"])
    ebitda = float(company["ebitda_ltm"])
    adjustments = rng.randint(4, 9)
    add_back_total = round(rev * rng.uniform(0.005, 0.035), 0)
    adj_ebitda = ebitda + add_back_total
    return f"""# Quality of Earnings Report — {company['name']}

**Company:** {company['name']}
**Sector:** {company['sector']} — {company['sub_sector']}
**Report Date:** {date.today().isoformat()}
**Prepared by:** Keystone Financial Advisory
**Period covered:** LTM

## Executive Summary
Reported LTM EBITDA of ${ebitda/1_000_000:.1f}M normalizes to **${adj_ebitda/1_000_000:.1f}M of Adj. EBITDA** after applying {adjustments} QoE adjustments totaling ${add_back_total/1_000_000:.1f}M. Adjustments are within typical market ranges for a platform of this scale in {company['sector']}.

## Revenue Quality
LTM revenue of ${rev/1_000_000:.0f}M comprises recurring / repeat revenue (~{rng.randint(65, 95)}%) and non-recurring project / one-time revenue (~{rng.randint(5, 35)}%). Top-10 customer concentration is {rng.randint(18, 42)}% of revenue, with the largest single customer at {rng.randint(5, 15)}%. Gross retention over the trailing three years is {rng.randint(85, 96)}%.

## EBITDA Bridge
| Line | Amount (USD) |
|---|---|
| Reported EBITDA | ${ebitda:,.0f} |
| + Owner's excess compensation | ${int(add_back_total * 0.35):,} |
| + Non-recurring legal / transaction | ${int(add_back_total * 0.25):,} |
| + Discontinued product line | ${int(add_back_total * 0.15):,} |
| + Pro-forma ERP contract step-up | ${int(add_back_total * 0.15):,} |
| + Other non-recurring | ${int(add_back_total * 0.10):,} |
| **Adj. EBITDA** | **${adj_ebitda:,.0f}** |

## Working Capital
Net working capital days {rng.randint(35, 110)}, stable over the LTM period. DSO {rng.randint(35, 70)}, DPO {rng.randint(28, 55)}, DIO {rng.randint(0, 90)} (where applicable). No abnormal working capital bumps ahead of sale process.

## Red Flags / Watch Items
- {"Customer concentration at top-3 accounts above 25% warrants diligence on renewal probability." if rng.random() < 0.4 else "No material customer concentration concerns."}
- {"The pro-forma ERP contract step-up assumes 100% conversion of pilot customers — sensitivity analysis recommended." if rng.random() < 0.3 else "Revenue assumptions appear supportable based on actual signed contracts."}
- {"One customer terminated in the last six months for performance reasons — immaterial financial impact but warrants commercial DD follow-up." if rng.random() < 0.25 else "No recent material customer departures observed."}

## Conclusion
Adjustments are well-supported with underlying documentation. No fatal findings. Recommend follow-up commercial diligence on top-10 customer renewal outlook.
"""


def legal_dd(company: dict, rng: random.Random) -> str:
    has_litigation = rng.random() < 0.35
    has_licensure_gap = rng.random() < 0.15
    return f"""# Legal Due Diligence Memorandum — {company['name']}

**Counsel:** Harrison Whitmore LLP
**Date:** {date.today().isoformat()}

## Corporate Records
Minute book reviewed through {date.today().year - 1}. Stock ledger reconciled to cap table. All board and shareholder consents appear to be in proper form.

## Litigation
{"""**Open Litigation:**
1. *Grayson v. """ + company['name'] + f"""* (Delaware Chancery, filed {date.today().year - 1}). Plaintiff alleges wrongful termination; claimed damages ${rng.randint(500, 3500)}k. Defense counsel assesses probability of adverse outcome at {rng.choice(['low', 'low-to-moderate'])}. Reserved on company books.
2. IRS audit of {date.today().year - 3} tax returns pending. Scope limited to R&D credit methodology. Expected resolution by Q2 {date.today().year}.""" if has_litigation else "No material open litigation. Standard employment matters are covered by EPLI policy."}

## Regulatory / Licensure
{f"""**Licensure Gap:** The Company's {rng.choice(['California', 'New York', 'Illinois', 'Massachusetts'])} operations appear to lack a state-specific {rng.choice(['healthcare services', 'broker', 'payment transmitter', 'data privacy'])} license. Management has engaged outside counsel to remediate; estimated 90-day fix. Post-close compliance condition recommended.""" if has_licensure_gap else "All required regulatory licenses are in good standing across operating jurisdictions."}

## Change-of-Control Consents Required at Close
- {rng.choice(['Top 3', 'Top 5', 'Top 7'])} customer contracts require formal notice but not consent (based on current contract review).
- {rng.randint(2, 8)} supplier contracts require written consent; counsel is drafting consent letters.
- Senior credit facility: {"consent required (standard change-of-control covenant)" if rng.random() < 0.7 else "no consent required; pay-off at close"}.

## IP
- Trademark registrations: {rng.randint(4, 18)} active US registrations.
- Patents: {rng.randint(0, 12)} granted, {rng.randint(0, 8)} applications pending.
- All assignments from employees and independent contractors appear to be on file.

## Conclusion
No fatal legal findings. Open items are being tracked on a diligence punch list and are expected to resolve by signing.
"""


def esg_report(company: dict, rng: random.Random) -> str:
    sector = company["sector"]
    return f"""# ESG Assessment — {company['name']}

**Assessment Date:** {date.today().isoformat()}
**Consultant:** Brightway ESG Advisors

## Environmental
{"""Manufacturing operations generate scope-1 emissions from natural-gas heating and scope-2 emissions from purchased electricity. Estimated carbon intensity is """ + str(rng.randint(30, 180)) + """ kgCO2e per $1k of revenue, within the 25th-75th percentile for the sub-sector. The Company has not yet adopted an SBTi-aligned emissions reduction target; doing so is a typical post-close initiative.""" if sector == "industrials" else "No material direct emissions exposure. Scope 2 emissions are attributable to office and cloud-infrastructure usage. The Company reports SaaS-inferred carbon footprint via its primary cloud provider."}

## Social
Headcount of {company.get('employees', 'n/a')} across all jurisdictions. Female representation: {rng.randint(28, 52)}% overall, {rng.randint(12, 38)}% in senior leadership. Turnover: {rng.randint(9, 22)}% annualized. No OSHA recordable incidents above industry benchmark in trailing 3 years.

## Governance
Board of {rng.randint(3, 7)} directors; current sponsor/investor representation {rng.randint(1, 3)} seats. No anti-corruption or FCPA exposures identified. Policies in place: Code of Conduct, Anti-Bribery, Whistleblower, Data Privacy.

## Watch Items
- {"Climate disclosure compliance (CSRD / SEC climate rule) will require additional reporting infrastructure by {}. Estimated cost $150-250k.".format(date.today().year + 1) if rng.random() < 0.6 else "No material upcoming regulatory reporting deadlines."}
- Diversity metrics trending positively but still below sector-leading benchmarks.

## Recommendations
1. Establish SBTi-aligned reduction target within 12 months of close.
2. Implement CDP and EcoVadis disclosure ahead of next exit.
3. Add a formal DEI metric to the value creation plan.
"""


def tax_dd(company: dict, rng: random.Random) -> str:
    return f"""# Tax Due Diligence — {company['name']}

**Firm:** Withum Tax Advisory
**Date:** {date.today().isoformat()}

## Historical Filings
Federal and state income tax returns reviewed for the trailing {rng.randint(3, 5)} years. No open federal audits. {"State audit pending in California regarding apportionment methodology; estimated exposure below $250k." if rng.random() < 0.25 else "No open state audits."}

## Sales & Use Tax
Company collects and remits sales tax in {rng.randint(12, 43)} states. {"Nexus study indicates a historical under-collection exposure of approximately ${:.1f}M, with material remediation through the VDA program recommended prior to close.".format(rng.uniform(0.2, 1.8)) if rng.random() < 0.35 else "Nexus study indicates no material historical exposure."}

## R&D Credits
Company has claimed R&D tax credits of approximately ${rng.randint(400, 3200)}k over the trailing 3 years. Methodology supported by contemporaneous documentation.

## Transaction Structuring
Sellers will effect a 338(h)(10) election; buyer receives a stepped-up tax basis resulting in estimated ${rng.randint(6, 38)}M NPV of tax shield over 15 years.

## International
{"Cross-border operations in {} require additional transfer-pricing documentation; no material findings.".format(rng.choice(['Canada', 'UK', 'Germany', 'Ireland'])) if company['country'] != 'USA' else "No material international tax exposures."}
"""


def tech_ddq(company: dict, rng: random.Random) -> str:
    return f"""# Technology & Security DDQ — {company['name']}

**Reviewer:** Signal 42 Tech Advisory
**Date:** {date.today().isoformat()}

## Architecture
Primary application is a {rng.choice(['Python/Django', 'Node.js/TypeScript', '.NET Core', 'Java/Spring'])} monolith with {rng.choice(['a shared PostgreSQL', 'AWS RDS MySQL', 'CockroachDB', 'DynamoDB'])} datastore. Infrastructure runs on AWS ({rng.choice(['us-east-1', 'us-west-2'])}) via {rng.choice(['ECS', 'EKS', 'EC2 + auto-scaling'])}. CI/CD via {rng.choice(['GitHub Actions', 'CircleCI', 'Buildkite'])}.

## Engineering Org
{rng.randint(12, 85)} engineers across product, platform, and SRE. Engineering leadership has tenure averaging {rng.randint(2, 7)} years; no senior departures in trailing 12 months.

## Security & Compliance
- SOC 2 Type II: {"certified, renewed annually" if rng.random() < 0.7 else "gap remediation in progress; audit scheduled for Q3"}
- ISO 27001: {"certified" if rng.random() < 0.3 else "not pursued; no customer-driver requirement"}
- Penetration testing: annual via third party; most recent {date.today().year - rng.randint(0, 1)} findings — no high-severity open items.
- HIPAA / GDPR: {"applicable; controls in place" if company['sector'] == 'healthcare' else "not applicable"}

## Technical Debt & Scalability
Observed technical debt is {rng.choice(['moderate', 'average for company stage', 'below average'])}. Principal concerns: {rng.choice(['legacy reporting module', 'monolith decomposition', 'cache invalidation patterns', 'data-warehouse maturity'])}. Recommended 100-day engineering investment: ${rng.randint(300, 1400)}k.

## Scalability
Current architecture supports ~{rng.randint(5, 50)}x current load without material rearchitecture.
"""


def industry_report(sector: str, sub_sector: str, rng: random.Random) -> str:
    return f"""# Industry Report — {sector.title()} / {sub_sector} — Q1 {date.today().year}

## Executive Summary
The {sub_sector} segment within {sector} continued its {rng.choice(['steady growth', 'gradual consolidation', 'premiumization', 'digitization'])} in the most recent quarter. {"Deal volume is modestly below peak 2021 levels but has stabilized." if sector != 'software' else "Deal volume remains robust despite multiple compression."}

## Key Metrics (median, LTM)
- **EV/EBITDA:** {round(rng.uniform(8.5, 15.5), 1)}x
- **EV/Revenue:** {round(rng.uniform(1.1, 5.5), 2)}x
- **Organic growth:** {round(rng.uniform(3.5, 18.5), 1)}%
- **EBITDA margin:** {round(rng.uniform(11, 32), 1)}%

## Deal Activity
Trailing 12-month PE buyout activity: {rng.randint(35, 180)} announced transactions. Strategic M&A: {rng.randint(50, 220)} deals. Median deal size: ${rng.randint(85, 650)}M EV.

## Key Themes
- {rng.choice(["Roll-ups in fragmented sub-segments continue to command premium multiples.", "Exit environment still challenging for legacy growth portfolios; hold periods extending.", "Strategic acquirers are reaccelerating M&A following multiple years of organic focus.", "Mid-market sponsors are leaning into add-ons to anchor platform creation at lower multiples."])}
- Regulatory: {rng.choice(["No material regulatory overhang.", "FTC scrutiny on roll-ups has slowed mega-deal approvals; sub-$1B deals proceeding normally.", "Expected changes to {} policy will affect revenue mix by 2026.".format(sector)])}

## Outlook
Medium-term (3-year) view: {rng.choice(['positive', 'cautiously positive', 'neutral'])}. {rng.choice(["Expect multiples to normalize to ~10-year averages as rate environment stabilizes.", "Underlying fundamentals remain strong; multiple compression has been a macro phenomenon.", "Dispersion between top-quartile and median operators will widen; platform selection matters more."])}
"""


def cim_summary(company: dict, rng: random.Random) -> str:
    return f"""# Confidential Information Memorandum (Summary) — {company['name']}

**Banker:** Sedgwick Capital Advisors
**Process Launched:** {date.today().isoformat()}

## The Opportunity
{company['name']} ("Company") is a leading provider of {company['sub_sector'].lower()} solutions headquartered in {company['hq_city']}. The Company operates in the high-growth {company['sector']} sector with a differentiated positioning, {company['employees']} employees, and an LTM revenue of ${float(company['revenue_ltm'])/1_000_000:.0f}M growing {company['growth_rate']:.0f}% YoY.

## Transaction Details
- **Process:** Targeted auction; {rng.randint(6, 18)} potential sponsors contacted
- **Proposed Structure:** {company.get('deal_type', 'platform').replace('_', ' ')}
- **Indicative EV Range:** ${float(company.get('enterprise_value') or 0)/1_000_000:.0f}M (implied {company.get('ask_multiple') or '—'}x LTM EBITDA)
- **Timeline:** IOIs by end of month; management meetings to follow; LOIs 4 weeks post-meeting

## Investment Highlights
1. **Market leadership** in a fragmented segment with visible M&A tuck-in opportunities.
2. **Predictable revenue** — {rng.randint(72, 95)}% recurring, {rng.randint(88, 97)}% gross retention.
3. **Attractive margin profile** at {company['ebitda_margin']:.0f}% EBITDA and clear path to ≥{min(40, int(company['ebitda_margin']) + 5)}% via already-identified initiatives.
4. **Experienced management team** willing to rollover a meaningful stake.
5. **Rule of 40** profile of {company['growth_rate'] + company['ebitda_margin']:.0f}+.

## Financial Summary (LTM)
| Metric | Value |
|---|---|
| Revenue | ${float(company['revenue_ltm'])/1_000_000:.0f}M |
| EBITDA | ${float(company['ebitda_ltm'])/1_000_000:.0f}M |
| EBITDA margin | {company['ebitda_margin']:.0f}% |
| Growth | {company['growth_rate']:.0f}% YoY |
"""


def generate_all_for_property(company: dict, rng: random.Random) -> list[dict]:
    """Return a list of DD docs {title, doc_type, text} for RAG ingest."""
    docs = [
        {"title": f"CIM — {company['name']}", "doc_type": "cim", "text": cim_summary(company, rng)},
        {"title": f"QoE Report — {company['name']}", "doc_type": "qoe", "text": qoe_report(company, rng)},
        {"title": f"Legal DD Memo — {company['name']}", "doc_type": "legal", "text": legal_dd(company, rng)},
        {"title": f"ESG Assessment — {company['name']}", "doc_type": "esg", "text": esg_report(company, rng)},
        {"title": f"Tax DD — {company['name']}", "doc_type": "tax", "text": tax_dd(company, rng)},
        {"title": f"Tech DDQ — {company['name']}", "doc_type": "tech_ddq", "text": tech_ddq(company, rng)},
    ]
    return docs


def generate_market_reports(companies: list[dict], rng: random.Random) -> list[dict]:
    pairs = sorted({(c["sector"], c["sub_sector"]) for c in companies})
    return [
        {
            "title": f"{sector.title()} / {sub} Industry Report — Q1 {date.today().year}",
            "doc_type": "industry",
            "text": industry_report(sector, sub, rng),
        }
        for sector, sub in pairs
    ]
