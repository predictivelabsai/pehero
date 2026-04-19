"""Generate material contract bodies (customer MSAs) for RAG indexing.

Kept under the legacy filename `leases.py`. Output is a markdown-formatted
contract body used by the documents generator.
"""

from __future__ import annotations

import random
from datetime import date, timedelta


TERMINATION_STANDARD = """
**Termination.** Either party may terminate this Agreement for convenience upon ninety (90) days' prior written notice to the other party, provided that Customer shall remain obligated for fees accrued through the effective termination date. Either party may terminate immediately for material breach not cured within thirty (30) days of written notice.
"""

CHANGE_OF_CONTROL = """
**Change of Control.** In the event of a Change of Control of Customer (defined as a sale of substantially all assets, merger, or transfer of more than fifty percent (50%) of voting securities), Provider shall have the right, exercisable within sixty (60) days of the Change of Control, to either (a) consent to the continuation of this Agreement, or (b) terminate this Agreement upon ninety (90) days' written notice. {coc_extra}
"""

EXCLUSIVITY_CLAUSE = """
**Exclusivity.** During the Term, Customer shall engage Provider as its exclusive supplier of the Services in the Territory, and shall not engage any third party to provide services substantially similar to the Services.
"""

MSA_PAYMENT = """
**Fees and Payment.** Customer shall pay the fees set forth in the applicable Order Form. All fees are invoiced monthly in advance and are due within thirty (30) days of invoice date. Late payments accrue interest at the lesser of 1.5% per month or the maximum rate permitted by law.
"""

MSA_IP = """
**Intellectual Property.** Provider retains all right, title, and interest in and to the Services, including all intellectual property rights therein. Customer receives a non-exclusive, non-transferable license during the Term to access and use the Services solely for its internal business operations. Nothing in this Agreement grants Customer any ownership interest in the Services.
"""

MSA_LIABILITY = """
**Limitation of Liability.** EXCEPT FOR BREACHES OF CONFIDENTIALITY OR INDEMNIFICATION OBLIGATIONS, NEITHER PARTY SHALL BE LIABLE FOR INDIRECT, CONSEQUENTIAL, OR PUNITIVE DAMAGES. EACH PARTY'S AGGREGATE LIABILITY IS CAPPED AT THE AGGREGATE FEES PAID OR PAYABLE BY CUSTOMER IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM.
"""

AUTO_RENEW = """
**Term and Renewal.** The initial term of this Agreement is {years} year(s) (the "Initial Term") commencing on the Effective Date. Thereafter, this Agreement shall automatically renew for successive one (1) year terms unless either party provides written notice of non-renewal at least sixty (60) days prior to the end of the then-current term.
"""

DATA_SECURITY = """
**Data Security.** Provider shall implement and maintain commercially reasonable administrative, physical, and technical safeguards consistent with SOC 2 Type II controls to protect Customer Data. Provider shall notify Customer of any security incident affecting Customer Data within seventy-two (72) hours of discovery.
"""


def generate_lease_body(*, prop: dict, unit: dict, rng: random.Random) -> str:
    """Render a customer Master Services Agreement.

    Note: `prop` is a portfolio company dict; `unit` is a cap-table holder dict,
    re-purposed loosely here to stub a counterparty name if present.
    """
    company = prop  # alias
    counterparty = unit.get("holder") if unit else None
    if not counterparty:
        counterparty = rng.choice([
            "Acme Industrial Co.", "Vector Logistics Inc.", "Harborlight Holdings",
            "Cascade Retail Corp.", "Northwind Distributors", "Meridian Hospitals",
            "Alpine Foods Inc.", "Orbit Communications LLC",
        ])

    effective = date.today() - timedelta(days=rng.randint(180, 900))
    term_years = rng.choice([1, 2, 3, 3, 5])
    end = effective + timedelta(days=term_years * 365)
    annual_value = rng.randint(120_000, 4_800_000)

    auto_renew = rng.random() < 0.7
    exclusivity = rng.random() < 0.15
    coc_required = rng.random() < 0.35
    coc_extra = ("Customer shall deliver prior written notice to Provider of any pending "
                 "Change of Control not less than thirty (30) days prior to closing."
                 if coc_required else "")

    body = f"""# MASTER SERVICES AGREEMENT

**Provider:** {company['name']}
**Customer:** {counterparty}
**Effective Date:** {effective.isoformat()}
**Initial Term End Date:** {end.isoformat()}
**Annual Contract Value (ACV):** ${annual_value:,}

---

## 1. Definitions
Terms capitalized in this Agreement shall have the meanings set forth in this Agreement or in the applicable Order Form.

## 2. Services
Provider shall make available to Customer the software-as-a-service platform, professional services, or other offerings described in the applicable Order Form (the "Services"). Provider shall use commercially reasonable efforts to meet the service level commitments set forth in Exhibit A.

{AUTO_RENEW.format(years=term_years)}

{MSA_PAYMENT}

{MSA_IP}

{DATA_SECURITY}

{MSA_LIABILITY}

{TERMINATION_STANDARD}

{CHANGE_OF_CONTROL.format(coc_extra=coc_extra)}

{"" if not exclusivity else EXCLUSIVITY_CLAUSE}

## 13. Miscellaneous
This Agreement constitutes the entire agreement between the parties concerning its subject matter and supersedes all prior discussions. It shall be governed by the laws of the State of Delaware without regard to conflict of laws principles. Any dispute arising hereunder shall be resolved exclusively in the state or federal courts located in Delaware.

---

IN WITNESS WHEREOF, the parties have executed this Master Services Agreement as of the Effective Date above.

**Provider:** _________________________  Date: _____________
**Customer:** _________________________  Date: _____________

---

### Exhibit A — Service Level Commitments
- **Availability:** 99.9% monthly uptime
- **Response time (P1):** 1 business hour
- **Response time (P2):** 4 business hours
- **Scheduled maintenance window:** Sunday 02:00–06:00 UTC
- **Data residency:** US (US-East, US-West) or EU (Frankfurt) at Customer's election

### Exhibit B — Order Form #1
- **Product:** Platform — Enterprise Tier
- **Annual Fee:** ${annual_value:,}
- **Payment Terms:** Net 30, billed monthly in advance
- **Term:** {term_years} year(s), auto-renew: {"yes" if auto_renew else "no"}
"""
    return body
