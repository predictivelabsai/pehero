# Baltic business registry + tax authority integration

PEHero supports lookup against the three Baltic business registries and their
tax authorities. Modules live under `tools/registry/` — one per country —
behind a uniform `tools/baltic.py` surface (`baltic_lookup`,
`baltic_filings`, `baltic_tax_status`) that any agent can call.

If a country's API key is not set, the relevant tool returns a `stub=True`
response. The rest of the app keeps working — sourcing agents just won't get
that data.

## What needs to be done per country

### Estonia (EE) — easiest

**Äriregister (business registry, RIK):**
- Portal: https://ariregister.rik.ee/eng
- API docs: https://ariregister.rik.ee/eng/api
- Some company-card endpoints are **public, no auth** (basic data, directors,
  annual-report indices). These can be used right now — just point the stub
  at them.
- Full Teabesüsteem access (change history, annex documents, shareholder
  registry, etc.) requires a contract with RIK:
  1. Submit application via https://ariregister.rik.ee/eng/teenused
  2. Pay per-query or subscribe (€ rates published on RIK site)
  3. Receive a username + password pair → fold into an API key header or
     HTTP basic auth in `tools/registry/ee.py::_ari_get`
- Set `EE_ARI_API_KEY` in `.env`.

**EMTA (tax authority):**
- Portal: https://emta.ee/en/business-client/registers-and-inquiries
- Public lookups:
  - Tax debt by reg code (`maksuvelg`) — unauthenticated JSON endpoint
  - VAT payer status
- Authenticated lookups (employment registry, TSD declarations, etc.) require
  eID (ID card / Mobile-ID / Smart-ID) with a delegated access agreement.
- Set `EE_EMTA_API_KEY` in `.env` once obtained.

### Lithuania (LT)

**Registrų centras (JAR/JADIS):**
- Portal: https://www.registrucentras.lt/en/
- Open data:
  https://www.registrucentras.lt/atviri_duomenys/eng/index.php
  (bulk downloads + limited REST)
- Paid REST API ("JAREP"):
  - Submit application to RC — business use requires a contract
  - Per-query or annual subscription, prices on RC site
  - Auth header: `X-RC-API-KEY: <token>`
- Set `LT_CR_API_KEY` in `.env`.

**VMI (State Tax Inspectorate) — i.MAS:**
- Portal: https://www.vmi.lt
- APIs are largely certificate-based (qualified e-signature). For a pure
  integration, you'll need:
  1. A qualified certificate (via Registrų centras / Skaitmeninio sertifikavimo
     centras)
  2. API enrollment via i.MAS
  3. OAuth2 client credentials flow
- Set `LT_VMI_API_KEY` to the bearer token returned after the OAuth2 exchange.

### Latvia (LV)

**Uzņēmumu reģistrs (UR):**
- Open data (bulk + limited REST): https://www.ur.gov.lv/lv/atverti-dati/
- Full feed (including change notifications, shareholder registry) requires a
  signed agreement with UR. Contact: klientu.serviss@ur.gov.lv
- After approval, an API key is issued. Use `X-UR-API-KEY: <token>`.
- Set `LV_UR_API_KEY` in `.env`.

**VID (State Revenue Service) — EDS:**
- Portal: https://eds.vid.gov.lv
- Public lookups:
  - Tax-debt register (by reg code)
  - VAT-payer status
- Authenticated APIs require eParaksts (Latvia's qualified e-signature). The
  integration pattern is the same as EMTA and VMI — sign on behalf of the fund
  entity, exchange for a bearer token.
- Set `LV_VID_API_KEY` to the bearer token.

## File map

- `tools/registry/__init__.py` — re-exports the three country modules
- `tools/registry/ee.py` — Estonia
- `tools/registry/lt.py` — Lithuania
- `tools/registry/lv.py` — Latvia
- `tools/baltic.py` — uniform StructuredTools for agents
- `utils/config.py` — env-var wiring (`LT_CR_API_KEY`, `LT_VMI_API_KEY`,
  `LV_UR_API_KEY`, `LV_VID_API_KEY`, `EE_ARI_API_KEY`, `EE_EMTA_API_KEY`)

## Wiring into agents

To enable for a specific agent, add to its TOOLS list, e.g.:

```python
from tools.baltic import baltic_lookup, baltic_filings, baltic_tax_status
TOOLS = [..., baltic_lookup, baltic_filings, baltic_tax_status]
```

Good candidates: `market_scanner`, `seller_intent`, `deal_triage`, and the
DD agents (`doc_room_auditor`, `title_zoning`) when Baltic deals are in scope.

## Quick manual test

```bash
# Works even with stub
.venv/bin/python -c "from tools.baltic import baltic_lookup; \
  print(baltic_lookup.invoke({'country':'EE','name_or_code':'Bolt Technology OÜ'}))"
```

With a real `EE_ARI_API_KEY` set, the same call returns structured company data
from Äriregister.
