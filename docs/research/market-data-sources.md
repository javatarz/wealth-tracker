# Market data sources for a self-hosted Indian household wealth tracker

**Verification date:** 19 September 2026 (IST). Every "verified" claim below is backed by an HTTP
request made on that date; the endpoints, file headers and sample rows quoted are what the live
services actually returned. Where I could only rely on a search-result snippet or a secondary
source, that is stated explicitly.

**Scope:** daily MF NAV history keyed by a stable scheme identifier; a scheme master (names/ISINs);
daily prices for Indian equities, gold and crypto; and historical benchmark index series (NIFTY 50
TRI at minimum).

**Out of scope for this brief:** anything requiring portfolio upload. No source reviewed here
requires uploading holdings — the only one that requires an *account* for richer data (BSE StAR MF
scheme master) is a member/broker login, not a portfolio upload.

---

## 0. Bottom line: recommended provider per data kind

| Data kind | Recommended primary | Why | Recommended fallback |
|---|---|---|---|
| MF daily NAV (current) | **AMFI `NAVAll.txt`** (official) | First-party, one file, scheme code + ISIN + name + plan/option + NAV + date | `mfapi.in` per-scheme JSON (mirror) |
| MF NAV history (backfill) | **AMFI `DownloadNAVHistoryReport_Po.aspx`** (official, ≤90 days/request) | First-party, includes ISIN columns, dates `DD-MMM-YYYY` | Community bulk dump (`api.tigzig.com/mf/v1/download`, Parquet/CSV/SQLite) |
| Scheme master (name/ISIN ↔ id) | **AMFI `NAVAll.txt`** (it *is* the master for id+ISIN+plan/option) | No separate official machine-readable master exists for free | `api.mfapi.in/mf` list (adds JSON, includes ISINs) |
| Equity EOD | **NSE UDiFF bhavcopy** + **NSE `EQUITY_L.csv` master** (official) | Official, no key, ISIN included in master | BSE UDiFF bhavcopy (official, blocks non-browser clients — see §4.2); Yahoo chart API (unofficial) |
| Gold | **IBJA daily AM/PM rates** (official industry benchmark) for physical gold; **AMFI NAV** for Gold ETFs / Gold FoFs / SGB-like MF wrappers | IBJA is the India benchmark used for SGB redemption; MF wrappers come free with the NAV feed | MCX bhavcopy (official commodity exchange, blocked non-browser), manual entry |
| Crypto | **CoinGecko** (keyless/Demo) for INR valuation | Free, no key, INR quotes, works from a server | Binance public klines (no key) for deep history; paid CoinGecko tier for full history |
| Benchmark (NIFTY 50 TRI) | **NSE Indices (`niftyindices.com`) TRI/NTR export** (official) | The only first-party source of dividend-inclusive series | NSE daily index CSV `ind_close_all_DDMMYYYY.csv` (official, **price** index only, no dividends) |

**One-line identifier answer (detail in §7):** the recommended NAV source exposes ISINs *in the same
row* as its scheme identifier, so ISIN can be joined directly — but the **join key must be the AMFI
scheme code**, not the ISIN, because ISIN coverage is incomplete and scheme-code rows are
plan/option-granular.

---

## 1. Mutual fund NAV: AMFI (official, first-party)

### 1.1 Current NAV — `NAVAll.txt`

- **URL:** https://portal.amfiindia.com/spages/NAVAll.txt (linked from
  https://www.amfiindia.com/net-asset-value/nav-download as "Complete NAV Report")
- **Access:** plain HTTP GET, no key, no account, no cookies. Verified 19 Sep 2026: `text/plain`,
  1,520,781 characters (~1.5 MB) fetched successfully.
- **Format (verified live):** semicolon-delimited, UK-style dates, with an **8-column header row**
  followed by section headers and AMC names on their own lines:

  ```
  Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Plan;Option;Net Asset Value;Date

  Open Ended Schemes(Children’s Fund - Childrens' Fund)

  Axis Mutual Fund

  135762;INF846K01WO1;-;Axis Children's Fund;Direct Plan;Growth Option;29.8856;18-Sep-2026
  ```

  So each data row carries: integer **scheme code**, two optional **ISINs**, scheme name, plan,
  option, NAV, and NAV date.
- **Update cadence:** published each business day after the SEBI-imposed 21:00 IST NAV cut-off. My
  19 Sep 2026 fetch contained rows dated 18-Sep-2026 and a few dated 19-Sep-2026 — i.e. the file was
  mid-publish, which is worth knowing operationally (a fetch can straddle a publication boundary).
- **Coverage:** open-ended schemes across all AMCs, all plans (Direct/Regular) and options
  (Growth/IDCW/Bonus), plus section types observed live: ETFs (debt / equity / gold / silver /
  overseas / hybrid / other), Fund of Funds, gilt, income, interval. Matured and segregated
  portfolios are still present with their **last-ever NAV date frozen** (e.g. ICICI Prudential
  Interval Fund rows dated 2017, "UTI - Bond Fund (Segregated - 17022020)" dated 2022, "ICICI
  Prudential Gilt Fund Investment Plan PF Option" dated 25-May-2018). Consumers must therefore
  treat "row present" ≠ "scheme live".
- **Unverified detail:** I could not find a `Close Ended Schemes(...)` section header in the
  19-Sep-2026 snapshot (a whole-file search for the pattern returned 0 matches while
  `Open Ended Schemes(` returned 103). AMFI's *old-format* download set has a separate "Close Ended
  NAV Report" (`Original_NAVClose.txt`) and "Interval Fund NAV Report" (`Original_NAVInterval.txt`),
  so closed-ended coverage in the current file is an open question — see §9. If the tracker must
  hold close-ended schemes (FMPs, closed-ended debt funds), verify this before relying on
  `NAVAll.txt` alone.
- **Licence/terms:** AMFI Terms of Use (https://www.amfiindia.com/terms-of-use) grant a
  "non-exclusive, personal, non-transferable, non-sublicensable, limited and revocable right to
  access, use and display this Site … for your **personal and non-commercial use only**", and
  prohibit you from "publicly perform[ing], publicly display[ing], transmit[ting], publish[ing] …
  modify[ing], or creat[ing] derivative works based on anything available through the Site",
  adding: "You shall not store electronically any significant portion of any part of the Site."
  A locally cached, single-household, non-redistributed tracker sits at the benign end of that
  language; a multi-user or publicly hosted version does not. AMFI's own footer disclaimer also
  states the information is supplied by its members and "AMFI does not take any responsibility for
  its accuracy, completeness and timeliness" (https://portal.amfiindia.com/).
- **Rate limits:** none documented. Practically: one ~1.5 MB GET per refresh, which fits the
  "refresh on explicit user action" design.
- **Disappearance / shape-change risk (medium-high, and currently live):** the download page
  currently states *"The NAV download in old format will be available only till 30th September
  2026"*, and the page now offers two generations of endpoints side by side — `NAVAll.txt` (new) and
  `Original_NAVAll.txt` / `Original_NAVOpen.txt` / `Original_NAVClose.txt` / `Original_NAVInterval.txt`
  (old, retiring). A search-cache snapshot of `NAVAll.txt` attributed to 11-Sep-2026 showed a
  6-column layout with plan/option folded into the scheme name; the 19-Sep-2026 live file has the
  8-column layout with separate `Plan` and `Option`. **Interpretation (researcher inference):**
  AMFI is mid-migration between file layouts, so parsers must key off the header row and tolerate
  new columns rather than assume fixed positions. Domain name unchanged and stable for years, so
  disappearance risk is low; layout-change risk is real and current.

### 1.2 NAV history — date-range report

- **URL:** `https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?frmdt=DD-MMM-YYYY&todt=DD-MMM-YYYY`
  (the form on https://www.amfiindia.com/net-asset-value/nav-download posts here)
- **Access:** plain GET, no key. Verified 19 Sep 2026.
- **Format (verified):** semicolon-delimited with header
  `Scheme Code;NAV Name;Plan;Option;ISIN Div Payout/ISIN Growth;ISIN Div Reinvestment;Net Asset Value;Date`
  — note this is a **different column order** from `NAVAll.txt` (ISINs after Plan/Option), one row
  per scheme per business day.
- **History depth — measured, not assumed:**
  - `frmdt=01-Apr-2006&todt=03-Apr-2006` → **255,849 characters of real NAV rows** (verified).
  - `frmdt=31-Mar-2006`, `15-Mar-2006`, `02-Jan-2006`, `01-Feb-2006`, `01-Apr-2005`,
    `03-Jan-2005`, `03-Jan-2001`, `01-Jan-1999` → all returned an HTML page (the ~7.9 KB search form)
    instead of data (verified, repeatable).
  - **Conclusion: AMFI's portal history begins ~1 April 2006.** This is a hard upstream floor, not a
    scheme-launch date. Any scheme older than April 2006 simply has no portal NAV before that date.
- **ISINs in old rows:** the April-2006 rows I fetched have **empty ISIN fields**
  (`102652;ABN AMRO Monthly Income Plan-Regular Plan-Growth Option;;;;;11.7436;03-Apr-2006`), and
  scheme names are the pre-2010 concatenated style. So historical backfill gives you NAVs keyed by
  scheme code but **no ISIN for old rows** — ISINs must come from the current master.
- **Rate limit / batching:** AMFI's page states "One can download historical NAV for a maximum
  period of 90 days at a time". A 2006-to-today backfill is therefore ~85+ requests; combine with
  the "refresh on explicit user action" design so this happens once, offline, then increment daily.

### 1.3 Official vs community mirrors

| Source | First-party? | Notes |
|---|---|---|
| `portal.amfiindia.com` `NAVAll.txt` + `DownloadNAVHistoryReport_Po.aspx` | **Official** (AMFI is the SEBI-mandated industry body that collects NAVs from AMCs) | No key, no SLA, no docs, ToU = personal non-commercial |
| `api.mfapi.in` | Community | Same scheme codes and ISINs, adds JSON + per-scheme history |
| `api.tigzig.com/mf/v1` | Community | Bulk Parquet/CSV/TSV/SQLite, "April 2006 onward" |
| NSE MF Desk "Scheme Master Report", BSE StAR MF "SCHEME CODE MASTER" | **Official** but member-gated | See §3 |

---

## 2. Mutual fund NAV mirrors (community-operated)

### 2.1 mfapi.in

- **URL / docs:** https://www.mfapi.in/ , https://www.mfapi.in/docs/ , base `https://api.mfapi.in`
- **Access:** anonymous GET, JSON, **no API key**. Verified 19 Sep 2026.
- **Endpoints verified live:**
  - `GET /mf/{scheme_code}` → `{"meta":{...,"scheme_code":125497,"scheme_name":"SBI SMALL CAP FUND - Direct Plan - Growth","isin_growth":"INF200K01T51","isin_div_reinvestment":null},"data":[{"date":"18-09-2026","nav":"214.73250"}, …],"status":"SUCCESS"}`
  - `GET /mf?limit=2&offset=0` → `[{"schemeCode":100027,"schemeName":"…","isinGrowth":null,"isinDivReinvestment":null}, …]`
    — i.e. the **scheme list itself carries ISINs**, which is exactly the master needed. (The
    unfiltered list is ~5 MB; page it or cache it.)
  - `/mf/{code}/latest`, `/mf/search?q=…` also documented at https://www.mfapi.in/docs/
- **History depth — measured:** `GET /mf/100119` (HDFC Balanced Advantage Fund – Regular – Growth,
  a fund launched in 1994) returned a series whose **oldest row is 03-04-2006** and whose newest is
  18-09-2026. That matches AMFI's floor exactly, so mfapi is a mirror of AMFI rather than a deeper
  archive. mfapi's own site markets "5+ Years" of history.
- **Update cadence:** six times daily per https://www.mfapi.in/ (10:05, 14:05, 18:05, 21:05, 03:09,
  05:05 IST).
- **Rate limits:** contradictory — the docs say "The API implements rate limiting to ensure fair
  usage. Please cache responses…" while the marketing page says "**no rate limiting**". **Recorded
  as a contradiction; not resolved.** Practical read: budget your calls, don't hammer it.
- **Licence / terms:** no Terms-of-Use or licence page was reachable from the docs page; the site
  describes itself as free and open. There is **no stated data licence, no SLA, no operator
  disclosure** available publicly. Source: https://www.mfapi.in/docs/
- **Disappearance risk:** highest of the MF options. It is a single community-run service
  (IP traceable to a DigitalOcean Bengaluru host per third-party stats page https://hypestat.com/info/mfapi.in),
  free, keyless, and with no funding model visible. It is excellent as a *fallback*, unsafe as a
  *sole* dependency for a data layer you plan to keep for years.

### 2.2 tigzig MF NAV API / bulk dump (community)

- **URL:** https://www.tigzig.com/apis/mf-nav , base `https://api.tigzig.com/mf/v1`, reference at
  `https://api.tigzig.com/mf/v1/redoc`
- **Claims from its own documentation page (fetched 19 Sep 2026, not independently audited):**
  "37M+ daily NAV records", "38,000+ schemes … including matured (open-ended, closed-ended,
  interval)", "**History back to April 2006**", "No authentication. No key, no sign-up.
  **300 requests/min per IP**", bulk download of the whole dataset in Parquet/CSV/TSV/SQLite
  (`GET /mf/v1/download`), and **lookup "by AMFI code OR ISIN — auto-detected"**.
- **Why it matters:** (a) it independently corroborates the April-2006 history floor and the
  scheme-code↔ISIN join; (b) a one-shot bulk download is the cheapest possible way to backfill a
  local cache for a self-hosted app, after which the app only needs AMFI's 1.5 MB daily file.
- **Risk:** single-operator community project behind a personal-finance site; no public SLA or
  licence terms found; treat as a convenience mirror, keep AMFI as the source of record.

---

## 3. Scheme master (name + ISIN → identifier)

There is **no free, documented, official "scheme master" file** populated with AMC, category,
benchmark and ISIN for all schemes. What exists:

1. **AMFI `NAVAll.txt` doubles as the practical master** — it carries scheme code, both ISINs,
   scheme name, plan, option, and (via section and AMC header lines) category group and AMC name.
   Verified live. This is sufficient to answer "given a scheme name or ISIN, what is the stable id?"
2. **`api.mfapi.in/mf`** — same mapping in JSON, including null ISINs (verified live).
3. **BSE StAR MF — SCHEME CODE MASTER (official, member-gated).** BSE StAR-MF file structures
   document "SCHEME CODE MASTER (Demat)" / "(Physical)" / "SCHEME CODE MASTER DETAILS" with an
   `ISIN varchar 12` field, distributed "under the Daily Download option on the application menu":
   https://bsestarmf.in/WEBFileStructure.pdf (PDF, referenced from https://www.bsestarmf.in/).
   **This requires BSE StAR MF membership/member login** — it is not a public download, so it is
   disqualified for a consumer self-hosted app even though it is first-party.
4. **NSE MF Desk — "Scheme Master Report"** (consolidated/SIP/STP/SWP variants) at
   https://nseinvestuat.nseindia.com/nsemfdesk/schememaster.htm — also member-ID gated
   (search-result snippet; page not fetched from this environment). Same disqualification.
5. **Richer metadata** (launch date, SEBI sub-category, benchmark, risk label, TXIC code) is only
   available from community aggregators (e.g. tigzig's scheme search returns AMC, group, category,
   plan, option, first/last NAV dates, TXIC code) or commercial vendors. Use it as enrichment, not
   as identity.

**Recommendation:** treat AMFI scheme code as the identity for MF instruments and keep name/ISIN as
attributes. Do not build identity on scheme *name* — see §7 for the collision evidence.

---

## 4. Indian equities (NSE / BSE)

### 4.1 NSE (first-party)

- **Equity master with ISIN — verified live:** `https://archives.nseindia.com/content/equities/EQUITY_L.csv`
  (182,067 chars, fetched 19 Sep 2026). Header:
  `SYMBOL,NAME OF COMPANY, SERIES, DATE OF LISTING, PAID UP VALUE, MARKET LOT, ISIN NUMBER, FACE VALUE`,
  e.g. `RELIANCE,…`/`3MINDIA,3M India Limited,EQ,13-AUG-2004,10,1,INE470A01017,10`. This is the
  authoritative NSE symbol ↔ ISIN mapping, free, no key.
- **Daily index closes — verified live:** `https://archives.nseindia.com/content/indices/ind_close_all_DDMMYYYY.csv`
  (17,449 chars for `18092026`). Columns:
  `Index Name,Index Date,Open Index Value,High Index Value,Low Index Value,Closing Index Value,Points Change,Change(%),Volume,Turnover (Rs. Cr.),P/E,P/B,Div Yield`;
  contains `Nifty 50,18-09-2026,…,23346.4,…`, plus ~140 indices and 15 columns of metadata. Note it
  also carries derivative indices (`Nifty50 TR 1x Inverse`, `Nifty50 TR 2x Leverage`,
  `Nifty50 Futures TR Index`) — **the plain `Nifty 50` row is a price index, not a TRI**, so this
  file cannot satisfy the benchmark requirement on its own.
- **Equity EOD ("bhavcopy"):** NSE moved to the SEBI-mandated **UDiFF** format; the old
  `sec_bhavdata_full` / legacy bhavcopy CSVs were discontinued from 08-Jul-2024 per NSE circular
  NSE/MSD/62424 dated 12-Jun-2024 (circular mirror: https://www.ricago.com/assets/front/base/file/file_management/2065.pdf;
  format description: https://www.nseindia.com/static/resources/forms-formats-members). The current
  file is a ZIP, community-documented as
  `https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip`
  (https://github.com/jugaad-py/jugaad-data/issues/79).
  **Unverified here:** I could not download the bhavcopy ZIP in this environment (see §8
  reachability log), so the exact column list (including whether ISIN is a column) is **not
  verified by me** — NSE's own format page and the UDiFF guidance document are the places to confirm,
  and the equity master above already supplies symbol↔ISIN if the bhavcopy lacks it.
- **NSE live APIs:** `https://www.nseindia.com/api/allIndices` and friends require cookie priming and
  browser-like headers; my keyless fetch was refused (see §8). They are also undocumented/unstable.
  Do not build on them.
- **Official paid alternative:** NSE sells historical EOD data by subscription
  (https://www.nseindia.com/static/market-data/eod-historical-data-subscription) — relevant only if
  you need a contractual licence, not for a personal tracker.
- **Licence:** NSE's publicly downloadable files carry no explicit redistribution licence. For a
  single-household local cache this is a low-risk grey area; redistribution or resale is not
  permitted without an NSE market-data agreement.

### 4.2 BSE (first-party) — reachable but hostile

- **URL patterns:** current equity bhavcopy (UDiFF, plain uncompressed CSV) —
  `https://www.bseindia.com/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_YYYYMMDD_F_0000.CSV`;
  legacy ZIP — `https://www.bseindia.com/download/BhavCopy/Equity/EQDDMMYY_CSV.ZIP`; legacy help
  page documents filename convention `eqddmmyy.csv` and a ~16:45 IST upload time
  (https://beta.bseindia.com/markets/equity/EQReports/BhavCopyhelp.aspx).
  UDiFF standardisation dates for BSE: notices 20240322-52 and 20240429-1
  (https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20240322-52,
  https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20240429-1);
  format summary at https://beta.bseindia.com/static/members/udiff.aspx.
- **Verified behaviour 19 Sep 2026:** every BSE URL I tried returned **HTTP 403 Forbidden** to a
  non-browser client — `https://www.bseindia.com/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_20260918_F_0000.CSV`,
  `https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx`,
  `https://beta.bseindia.com/static/members/udiff.aspx`,
  `https://beta.bseindia.com/markets/equity/EQReports/BhavCopyhelp.aspx`. **Direct evidence that BSE
  requires browser-like headers and/or a session cookie.** Any BSE integration must be treated as
  fragile-by-design.
- **Master list:** BSE exposes "List of Scrips" with ISIN via its website; I could not fetch it
  (403). Community/broker mirrors exist (e.g. `https://public.fyers.in/sym_details/BSE_CM.csv` — a
  broker-hosted symbol master containing BSE scrip code, symbol and ISIN) but they are third-party.
- **Depth:** BSE's public bhavcopy archive depth (earliest available date) is **unverified** — I
  could not reach the pages that document it.

### 4.3 Unofficial equity price APIs (fallback only)

- **Yahoo Finance chart endpoint — verified working keyless on 19 Sep 2026:**
  `https://query1.finance.yahoo.com/v8/finance/chart/RELIANCE.NS?range=1mo&interval=1d` returned
  `currency: INR`, `exchangeName: NSI`, `fullExchangeName: NSE`, `firstTradeDate`, a daily timestamp
  array, and `validRanges` up to `max`. Convenient for a handful of holdings with long history.
- **Risks:** undocumented, unversioned, no contract, and Yahoo's terms do not license
  redistribution or systematic scraping. This is a "may break without notice" dependency — acceptable
  as an optional fallback provider behind the same interface, never as the source of record.
- **Caution for ISIN-based portfolios:** Yahoo is keyed by exchange ticker (`RELIANCE.NS`), *not* by
  ISIN, so you need the NSE master (§4.1) to resolve ISIN → symbol first.

---

## 5. Gold

### 5.1 IBJA (official industry benchmark, first-party for bullion rates)

- **URL:** https://ibjarates.com/ (Indian Bullion and Jewellers Association). Verified 19 Sep 2026.
- **What it publishes:** daily **AM and PM** rates per purity — 999, 995, 916, 750, 585, plus Silver
  999 and Platinum 999 — quoted **per gram** for gold and per kg for silver, "without 3% GST and
  Making Charges". The visible page shows the current day's AM/PM block plus a "Previous Dates Rate"
  table with the last handful of days (15–18 Sep 2026 when I fetched); longer history is published
  as **daily PDF reports** under `https://www.ibja.co/Upload/IBJA_Bullion Daily Report - DD-MM-YYYY.pdf`
  (example PDF for 12-Aug-2026 returned by search: https://www.ibja.co/Upload/IBJA_Bullion%20Daily%20Report%20-%2012-08-2026.pdf).
- **Methodology (why it is the right benchmark):** IBJA polls "tradable prices" twice daily from 29
  physical-market participants (bullion dealers, refiners, importers, scrap dealers, exporters,
  jewellers) — see https://www.ibjarates.com/pdf/spot-polling-mechanism/spot-polling-mechanism.pdf.
  Sovereign Gold Bond redemption values are derived from IBJA 999 closing prices, which is why this
  is the number an Indian household's gold should be valued against.
- **API / key / cost:** the site shows an "**API Esteemed Users**" logo wall (RBI, HDFC, IndusInd,
  UCO Bank, GIFT City entities, fintechs), i.e. IBJA's API is a **licensed commercial product**
  aimed at institutions. No free, documented, keyless IBJA API was found. Third-party resellers
  exist (e.g. https://www.indiagoldratesapi.com/Documentation.aspx — API key required, commercial)
  and community scrapers exist (e.g. https://github.com/0xSaurabhx/IBJA-API) — both add a
  dependency on someone else's ToS compliance.
- **Practical recommendation:** scrape the AM/PM table once per business day (one small GET, no key)
  and/or record IBJA's daily PDF; store the 999/916 per-gram values with the date and the AM/PM flag.
  Provide a manual-override so the tracker still works if the page shape changes. If gold is held as
  **Gold ETF / Gold FoF**, skip IBJA entirely — AMFI's NAV feed already covers those (verified: gold
  ETF and gold FoF sections and schemes such as `115127;INF209KB18D3;…;Aditya Birla Sun Life Gold ETF`
  appear in `NAVAll.txt`).

### 5.2 MCX (official commodity exchange) — blocked

- **URL:** https://www.mcxindia.com/market-data/bhavcopy (also `/BhavCopy`). The page's underlying
  payload is JSON with per-contract `Symbol/ExpiryDate/Open/High/Low/Close/Volume/OpenInterest`
  (per search-result snippet of the endpoint's JSON body).
- **Verified 19 Sep 2026:** fetch returned **HTTP 403 Forbidden** to a non-browser client.
- **Fit:** MCX gives *futures contract* prices (with expiries, roll effects), not a household
  bullion rate. Useful as a market signal, poor as a valuation input. Not recommended as the gold
  valuation source.
- **Note:** MCX market data is licensed; redistribution terms are not public.

### 5.3 Other gold forms

- **SGB (Sovereign Gold Bond):** valued off IBJA (§5.1); redemption values are published by RBI on a
  semi-annual schedule. New SGB tranches are no longer being issued, but outstanding bonds exist in
  household portfolios. **Unverified in this pass:** I did not locate the RBI page URL for the
  redemption-value table within this research budget.
- **Digital gold (MMTC-PAMP / SafeGold / jeweller apps):** no published, official, free API found;
  vendor rates also embed making charges/GST. Recommend manual entry.

---

## 6. Crypto

### 6.1 CoinGecko — recommended for INR valuation

- **URL:** keyless `https://api.coingecko.com/api/v3`, docs https://docs.coingecko.com/docs/keyless-public-api
- **Verified live 19 Sep 2026:** `https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=inr&days=365&interval=daily`
  returned **no key required**, with a price series in INR whose final point is dated 19-Sep-2026 and
  whose length is ~366 daily points (≈1 year).
- **History depth — the important limit:** CoinGecko documents that "**Access to historical data via
  the Public API (Demo plan) is restricted to the past 365 days only. To access the complete range of
  historical data, please subscribe**" (https://coingecko-api-v3.readme.io/v3.0.1/reference/coins-id-history),
  and plan tables show `days` accepted values of `7, 14, 30, 90, 180, 365` for Demo/Keyless vs
  `…, max` for Analyst-and-above (https://docs.coingecko.com/demo/reference/public-treasury-entity-chart).
  **So: free CoinGecko cannot backfill crypto history beyond one year** — a real constraint for a
  tracker that needs cost basis and long-run performance.
- **Rate limits (contradictory sources — recorded, not resolved):** keyless "~10–30 calls/min
  (dynamic, varies by server load)" (https://docs.coingecko.com/docs/keyless-public-api); a support
  article says public API 5–15/min and "a stable rate limit of 30 calls per minute" for a Demo
  account (https://support.coingecko.com/hc/en-us/articles/4538771776153);
  the pricing page shows Demo = 100 calls/min with a 10,000 calls/month cap
  (https://www.coingecko.com/en/api/pricing). Assume the most conservative number.
- **Licence:** CoinGecko API Terms (https://www.coingecko.com/en/api_terms). The free plans are
  licensed for the described scope; the keyless API is documented as "useful for quick prototyping,
  open-source projects, and educational use" and the Demo plan **requires attribution**. A
  personal, self-hosted, non-redistributed tracker is inside that envelope; check the terms again if
  you ever expose it to other users.
- **Key/account:** none for keyless; a free Demo account (email signup, API key header
  `x_cg_demo_api_key`) gives a more stable limit. No portfolio data is sent — only coin ids.

### 6.2 Binance (deep-history alternative)

- **Why it is relevant:** Binance's public market-data endpoints (`/api/v3/klines`) are keyless and
  serve full history per instrument pair since listing (BTCUSDT from 2017). **Unverified here:** I did
  not call the klines endpoint in this pass.
- **India access:** Binance was blocked in India in Jan-2024 and **re-registered with FIU-IND in
  Aug-2024**, paying a ₹18.8 crore penalty, and is described as legal/operational in India in 2026
  (secondary sources: https://economictimes.indiatimes.com/tech/technology/binance-registers-with-fiu-ind-pays-rs-18-8-crore-fine-to-restart-ops-in-india/articleshow/112542870.cms,
  https://legalshouts.com/is-binance-legal-in-india/). It does not support INR deposits.
  **Confidence: medium** — treat India-accessibility as a re-check-at-implementation item, and note
  it is irrelevant for a personal tracker that only reads prices.
- **Recommendation:** CoinGecko for INR valuation and metadata; Binance (or a paid CoinGecko tier)
  only if/when you need >365 days of crypto history. Behind the interface, that is one provider
  method with two implementations.
- **Tax context (not a data question, but the tracker will need it):** Indian VDAs are taxed at 30%
  with 1% TDS on transfers — keep this out of the market-data layer.

---

## 7. Identifiers: what each source exposes (the downstream `Instrument` decision)

This is the section the identity design is blocked on. Verified from live responses unless noted.

| Source | Identifiers exposed | Stable? |
|---|---|---|
| AMFI `NAVAll.txt` | **AMFI scheme code** (integer, e.g. `119551`), **ISIN Div Payout/ISIN Growth**, **ISIN Div Reinvestment** (`-` when absent), scheme name, plan, option | Scheme code: stable, never reused, present for every row. ISIN: nullable |
| AMFI history report | scheme code, scheme name, plan, option, both ISIN columns (**empty for 2006-era rows**), NAV, date | as above |
| mfapi.in | `schemeCode` (= AMFI code), `schemeName`, `isinGrowth`, `isinDivReinvestment`; meta adds `fund_house`, `scheme_type`, `scheme_category` | mirror of AMFI |
| tigzig MF API | AMFI code **or ISIN** accepted as input; scheme metadata includes AMC, group, category, plan, option, first/last NAV date, "TXIC code" (self-reported) | mirror of AMFI |
| NSE `EQUITY_L.csv` | **SYMBOL**, `ISIN NUMBER`, name, series, listing date, face value | symbol stable, ISIN stable |
| NSE bhavcopy (UDiFF ZIP) | symbol/ISIN per NSE's UDiFF spec — **column presence not verified by me** | — |
| BSE bhavcopy / List of Scrips | **BSE scrip code** (numeric), scrip id (symbol), ISIN, group (per BSE help/notice pages; direct fetch blocked 403) | scrip code stable |
| NSE index CSV | index name string only (e.g. `Nifty 50`) — **no ISIN for indices** | name is the key |
| NSE Indices TRI export | index name + date + TRI + NTR; no ISIN | name is the key |
| IBJA | metal + purity + AM/PM + date; no ISIN | synthetic key |
| CoinGecko | coin `id` (e.g. `bitcoin`), symbol, platform contract address | id stable, symbol not unique |
| Yahoo | exchange ticker (`RELIANCE.NS`) — no ISIN | ticker can change |

### 7.1 The precise answer to the blocked question

**Does the recommended NAV source expose an identifier that can be joined to an ISIN?**

**Yes — and more than that, it exposes the ISIN itself in the same row.** `NAVAll.txt` has a column
literally headed `ISIN Div Payout/ ISIN Growth` and another `ISIN Div Reinvestment`; `mfapi.in`
returns the same two values as `isin_growth` / `isin_div_reinvestment` next to `scheme_code`. So no
external join is needed to get from a NAV series to an ISIN.

**But the join key must be the AMFI scheme code, not the ISIN**, for three verified reasons:

1. **ISINs are nullable.** Live examples from the 19-Sep-2026 file: `154625;-;-;quant Silver ETF`,
   `154504;-;-;HDFC Nifty Metal ETF`, and AMFI's own 2006-era history rows have all ISIN columns
   blank (`102652;…;;;;;11.7436;03-Apr-2006`). Any scheme whose ISIN is missing cannot be keyed by
   ISIN.
2. **Scheme name + plan + option is NOT unique.** In the same file, `Axis Children's Fund;Direct
   Plan;Growth Option` appears under **both** `135762` (ISIN `INF846K01WO1`) and `135764`
   (ISIN `INF846K01WR4`). Name-based dedup would silently merge two distinct schemes with distinct
   NAV series.
3. **A scheme-code row is plan/option-granular, and one row carries up to two ISINs.** AMFI column 2
   is the growth ISIN *or* the IDCW-payout ISIN depending on the row's option (researcher
   interpretation of the column label `ISIN Div Payout/ ISIN Growth`), and column 3 is the
   reinvestment ISIN. So the natural primary key is `(scheme_code)`, with `isin_growth` /
   `isin_payout` / `isin_reinvestment` as **attributes**, not the key.

**Consequence for `Instrument` identity (recommendation):**

- Surrogate internal id (`uuid`), plus a set of typed external identifiers:
  `amfi_scheme_code` (MF), `isin` (equities, ETFs, SGB, MF options), `nse_symbol` / `bse_scrip_code`
  (equities), `nse_index_name` (benchmarks), `coingecko_id` (+ chain/contract for tokens),
  `ibja_key` (metal+purity).
- For MF instruments, upsert on `amfi_scheme_code`; store ISINs as nullable, changeable attributes.
- Use ISIN as the *cross-source* join (broker contract notes, CDSL/NSDL, exchange lists, SGB), and
  accept that it will be absent for some MF schemes and all indices.
- **Not verified:** whether the same ISIN ever appears under two different AMFI scheme codes (i.e.
  whether ISIN is 1:1 with scheme code). Do not assume it is; treat `amfi_scheme_code → ISIN` as
  many-to-one-safe but re-check before enforcing a unique index on ISIN.

---

## 8. Reachability log (what I actually got, 19 Sep 2026)

Useful because it tells you which of these sources a self-hosted app can realistically talk to from
an ordinary server/desktop without browser emulation.

| Request | Result |
|---|---|
| `GET portal.amfiindia.com/spages/NAVAll.txt` | **200**, 1,520,781 chars, 8-column header |
| `GET portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?frmdt=01-Apr-2006&todt=03-Apr-2006` | **200**, 255,849 chars of rows |
| Same endpoint for Jan/Feb/Mar-2006, 2005, 2001, 1999 | **HTML form page (~7.9 KB) — no data** |
| `GET api.mfapi.in/mf/125497`, `/mf/100119`, `/mf?limit=2` | **200**, JSON with ISINs; series back to 03-04-2006 |
| `GET api.tigzig.com` docs page (via site) | **200**, claims bulk Parquet/CSV/SQLite dump |
| `GET archives.nseindia.com/content/equities/EQUITY_L.csv` | **200**, 182,067 chars |
| `GET archives.nseindia.com/content/indices/ind_close_all_18092026.csv` | **200**, 17,449 chars |
| `GET nsearchives.nseindia.com/products/content/sec_bhavdata_full_18092026.csv` | **failed (aborted)** |
| `GET nsearchives.nseindia.com/content/indices/ind_nifty50list.csv` | **failed (aborted)** |
| `GET www.nseindia.com/api/allIndices` | **failed (aborted)** |
| `GET archives.nseindia.com/content/press/Data_details_CM.pdf` | **failed** |
| `GET www.bseindia.com/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_20260918_F_0000.CSV` | **HTTP 403** |
| `GET www.bseindia.com/markets/MarketInfo/BhavCopy.aspx` | **HTTP 403** |
| `GET beta.bseindia.com/...` (UDiFF, BhavCopyhelp) | **HTTP 403** |
| `GET www.mcxindia.com/market-data/bhavcopy` | **HTTP 403** |
| `GET query1.finance.yahoo.com/v8/finance/chart/RELIANCE.NS?range=1mo&interval=1d` | **200**, JSON with INR prices |
| `GET api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=inr&days=365&interval=daily` | **200**, keyless, ~366 daily INR points |
| `GET www.niftyindices.com/reports` and `/reports/historical-data` | **failed (aborted)** |
| `GET ibjarates.com` | **200**, AM/PM table + last few days |
| `GET www.amfiindia.com/terms-of-use` | **200**, full text |

**Interpretation (researcher inference):** NSE's newer `nsearchives` host, all `nseindia.com` pages
and the whole `niftyindices.com` domain were unreachable from this environment, while the older
`archives.nseindia.com` host served two files without cookies. This is consistent with the widely
reported NSE/NSE-Indices anti-bot layer (Akamai) rather than with the files not existing. Practical
consequence: a self-hosted app should expect to tune headers/UA (or run its fetcher on the user's own
machine, where a real browser session exists) for NSE/BSE/NSE-Indices endpoints, and should degrade
gracefully when they refuse.

---

## 9. Benchmark index series (NIFTY 50 TRI)

- **Official existence (documentary):** NSE publishes "Total Returns Index Values" under its
  historical market reports (https://www.nseindia.com/resources/historical-reports-capital-market-daily-monthly-archives),
  and NSE Indices hosts a historical-data page with columns
  `IndexName | Date | Total Returns Index | Net Total Return Index`
  (https://www.niftyindices.com/reports, https://niftyindices.com/reports/historical-data).
  NSE Indices also explains the price-vs-TRI distinction at
  https://niftyindices.com/resources/index-concepts/total-return-index. **None of these pages could
  be fetched from this environment** (§8), so the above is from search-result snippets of the official
  pages, not from a fetch I performed.
- **Machine access (community-documented, not verified by me):** a POST back-end on
  `https://www.niftyindices.com/Backpage.aspx/getTotalReturnIndexString` accepts a
  `{"cinfo":"{'name':'NIFTY 50','startDate':'01-Jan-1999','endDate':'…','indexName':'NIFTY 50'}"}`
  body with `Content-Type: application/json`, `X-Requested-With: XMLHttpRequest`, a Referer and a
  **browser-like User-Agent**, returning `{"d":"[{…'TotalReturnsIndex':'35793.78','NTR_Value':'31169.3'…}]"}`.
  Documented (with the UA trap — non-browser UAs stall rather than 403) at
  https://github.com/satwikbasu/indian-market-data-endpoints/blob/main/endpoints/niftyindices-tri-api.md.
  My tooling cannot issue POST requests, so **this remains unverified here**.
- **History depth — NOT verifiable in this pass.** The community spec's example requests start at
  `01-Jan-1999` and describe the series as "from inception to today", but I could not confirm the
  actual earliest returned date. Community sources disagree on the TRI's base date: one says the
  price index is based at 3 Nov 1995 / launched 22 Apr 1996 and that **the NIFTY 50 TRI "has its own
  base date of 30 June 1999"** (https://www.holisticinvestment.in/nifty-50-prediction-2030-2035-2040-2045/,
  low-authority community source, **contradicted** by the endpoint example that reports values from
  Jan-1999). **Treat TRI history depth and base date as open; verify with one POST request at
  implementation time.** Do not state a TRI history depth in the spec until measured.
- **Verified fallback that does work (keyless):** `ind_close_all_DDMMYYYY.csv` on
  `archives.nseindia.com` (§4.1) provides daily closes and P/E/P/B/Div Yield for `Nifty 50` and
  siblings — but **no dividends**, so it is a *price* series. Combining it with the published Nifty 50
  Dividend Points row (`Nifty50 Dividend Points,18-09-2026,…,-,-,-,196.79,…`) is **not** a
  substitute for a true TRI, and I would not build a benchmark on that reconstruction.
- **Recommendation:** treat NSE Indices' TRI/NTR export as the single benchmark provider, fetch it
  via an explicit user-triggered refresh (a full "max" history per index is one request), cache the
  series locally, and store the retrieval timestamp. If the endpoint's behaviour changes, fall back to
  the official (paid, contractual) NSE data subscription rather than to a scraped third party.

---

## 10. Risk comparison: official vs community

| | Official / first-party | Community mirrors |
|---|---|---|
| Examples | AMFI, NSE, BSE, NSE Indices, MCX, IBJA | mfapi.in, tigzig, jugaad-data/nsepy, indiagoldratesapi.com, broker symbol masters (FYERS), Yahoo |
| Data quality | Source of record; AMFI NAVs come straight from the AMCs | Derived; normally identical, occasionally stale or normalised differently |
| Availability | Years-long track record, but **no SLA and no documented format contract**; AMFI changes layout, NSE/BSE change file formats (UDiFF 2024) and block scrapers | Can vanish overnight; no notice; no versioned API |
| Cost/keys | Free, keyless | Free, keyless (mfapi/tigzig); some commercial (indiagoldratesapi) |
| Licence clarity | Muddled: AMFI ToU is personal/non-commercial; exchange files have no explicit redistribution licence | Usually silent — no terms page at all |
| Failure mode | Format change, bot-blocking, hosts moving (`nsearchives` vs `archives`) | Operator stops paying the bill |

**Design implication:** keep the market-data provider behind an interface (as intended), but make the
*implementation* policy "official first, mirror second", with a per-source provenance tag and a
`fetched_at` stamp stored next to every cached series so a later format change or stale mirror is
detectable rather than silent.

---

## 11. Missing evidence / unresolved questions

1. **NIFTY 50 TRI history depth and base date** — could not issue a POST to the documented endpoint
   (tooling limitation) and `niftyindices.com` was unreachable. Community sources contradict each
   other (Jan-1999 values vs a 30-Jun-1999 base date). **Must be measured before writing any
   "history depth" claim for benchmarks into the spec.**
2. **Whether `NavAll.txt` includes closed-ended schemes** in the current format — no
   `Close Ended Schemes(` header matched in the 19-Sep-2026 snapshot, but AMFI's old-format set has a
   dedicated Close Ended report. Re-check (and check the "Complete NAV Report" download page for a
   separate closed-ended link) before assuming coverage.
3. **NSE UDiFF bhavcopy column list** (is ISIN a column?) — the ZIP was not downloadable from this
   environment; NSE's own UDiFF format page is the place to confirm.
4. **History depth of NSE/BSE bhavcopy archives** (earliest downloadable date) — undocumented in what
   I could reach; community sources mention a dated directory structure starting 1999, but I could
   not verify the claim against a first-party page (the NSE historical-data-dissemination PDF would
   not download).
5. **mfapi.in rate-limit numbers and any licence** — its own docs contradict its marketing page
   ("rate limiting" vs "no rate limiting") and expose no terms/licence.
6. **Whether one ISIN ever maps to two AMFI scheme codes** — untested; relevant to enforcing a
   uniqueness constraint on ISIN.
7. **RBI's SGB redemption-value page URL** — not located in this pass.
8. **Binance klines endpoint** — assumed-working from documentation knowledge; not called here. Its
   India-access status rests on secondary sources (Economic Times and similar).
9. **Number of schemes in `NavAll.txt`** — I did not count rows; community figures range from
   "10,000+ active" (mfapi) to "38,000+ including matured" (tigzig). Treat both as unverified.

---

## 12. Recommended next steps (research)

1. One-off verification script (run from the target machine, not a sandbox) that: (a) POSTs the
   NSE-Indices TRI endpoint for `NIFTY 50` with `startDate` far back and records the earliest row
   returned; (b) downloads one NSE UDiFF bhavcopy ZIP and prints its header; (c) downloads
   `NAVAll.txt` and asserts the presence/absence of a closed-ended section and the current column
   count.
2. Confirm mfapi.in's practical tolerance (e.g. 50 sequential scheme fetches) and record the observed
   429/throttle behaviour, since the docs are self-contradictory.
3. Decide the local cache shape: one daily unit per kind (MF NAV snapshot, equity EOD, index TRI,
   gold rate, crypto price) with `source`, `fetched_at`, `payload_hash`; that makes mirror-vs-official
   divergence measurable.

---

## Sources

**Kept (primary / directly relevant):**

- AMFI NAV download page — https://www.amfiindia.com/net-asset-value/nav-download — official entry
  point; states the 90-day history limit and the 30-Sep-2026 old-format retirement.
- AMFI `NAVAll.txt` — https://portal.amfiindia.com/spages/NAVAll.txt — the recommended MF source;
  fetched and parsed.
- AMFI history report — https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx — used to
  establish the 1-Apr-2006 history floor by probing.
- AMFI Terms of Use — https://www.amfiindia.com/terms-of-use — the licence position for MF data.
- AMFI portal footer disclaimer — https://portal.amfiindia.com/ — accuracy disclaimer.
- mfapi.in docs — https://www.mfapi.in/docs/ and https://www.mfapi.in/ — mirror docs; verified
  responses via https://api.mfapi.in.
- tigzig MF NAV API — https://www.tigzig.com/apis/mf-nav — community bulk-dump option and an
  independent corroboration of the April-2006 floor and the code-OR-ISIN lookup.
- NSE equity master — https://archives.nseindia.com/content/equities/EQUITY_L.csv — symbol↔ISIN.
- NSE daily index CSV — https://archives.nseindia.com/content/indices/ind_close_all_DDMMYYYY.csv —
  verified; price indices only.
- NSE UDiFF circular copy — https://www.ricago.com/assets/front/base/file/file_management/2065.pdf —
  the 08-Jul-2024 discontinuation of legacy bhavcopy formats; format summary at
  https://www.nseindia.com/static/resources/forms-formats-members (snippet only).
- NSE EOD/historical paid subscription — https://www.nseindia.com/static/market-data/eod-historical-data-subscription
  — the licensable alternative.
- BSE UDiFF notices — https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20240322-52
  and https://beta.bseindia.com/static/members/udiff.aspx — BSE format standardisation.
- BSE bhavcopy help — https://beta.bseindia.com/markets/equity/EQReports/BhavCopyhelp.aspx —
  naming convention and upload time (snippet; the page itself returned 403).
- BSE StAR MF file structures — https://bsestarmf.in/WEBFileStructure.pdf — proof that the official MF
  scheme-code master with ISIN exists but is member-gated.
- IBJA rates — https://ibjarates.com/ and polling mechanism
  https://www.ibjarates.com/pdf/spot-polling-mechanism/spot-polling-mechanism.pdf — official bullion
  benchmark.
- MCX bhavcopy — https://www.mcxindia.com/market-data/bhavcopy — official commodity EOD (403 to
  plain clients).
- CoinGecko keyless docs / limits — https://docs.coingecko.com/docs/keyless-public-api ,
  https://docs.coingecko.com/docs/errors-and-rate-limits , https://www.coingecko.com/en/api/pricing ,
  https://www.coingecko.com/en/api_terms , and the 365-day restriction statement at
  https://coingecko-api-v3.readme.io/v3.0.1/reference/coins-id-history.
- NSE Indices TRI endpoint spec (community) —
  https://github.com/satwikbasu/indian-market-data-endpoints/blob/main/endpoints/niftyindices-tri-api.md —
  the only concrete machine-access description found; unverified here.
- NSE Indices historical data / TRI concept — https://www.niftyindices.com/reports ,
  https://niftyindices.com/resources/index-concepts/total-return-index — official existence of the
  TRI/NTR export (snippets only; site unreachable from this environment).
- Yahoo chart endpoint — https://query1.finance.yahoo.com/v8/finance/chart/RELIANCE.NS — verified
  working unofficial fallback.

**Rejected / deprioritised:**

- SEO aggregator pages describing `NAVAll.txt` (e.g. `v2.webnotes.in`, `financex.in`,
  `rightadvise.com`, `bullwiser.com`) — no primary evidence, sometimes factually loose (one claims
  even ₹1 "per-month" charges for NAV data); used only where they pointed to a real endpoint.
- `nseindia.in/all-reports` — host is not the exchange's canonical domain; likely a mirror; not cited
  as evidence.
- PyPI/GitHub client libraries (`navpipe`, `mf-tool`, `jugaad-data`, `nsepy`, `nse-archives`,
  `AMFI-API`, `amfipy`) — useful as implementation references but they add no sourcing authority and
  several are stale; not treated as evidence.
- Paid vendor "data source" marketing pages (`mfapis.in`, `indiagoldratesapi.com`) — commercial
  resellers, kept only as existence evidence for paid routes.
- `investing.com` TRI page — third-party aggregator, unclear provenance for index series.
