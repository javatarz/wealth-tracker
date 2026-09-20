# Indian broker tradebook CSV formats

**Verification date:** 20 September 2026 (IST). This brief is built from *actual files and parser
source* rather than documentation prose, because no Indian broker publishes a column-level
specification for its tradebook export.

**Scope:** the **tradebook / order-history** export (one row per executed fill) for equity and, where
noted, F&O. Out of scope: contract notes, P&L/tax reports, ledger/funds statements, holdings
snapshots, and the broker REST APIs (Kite Connect, Upstox v2, Angel SmartAPI).

**Method and evidence quality.** I could not log in to any broker, so every header below is
established from one of:

- a **real export committed to a public repo** (the strongest evidence — an actual file, sanitised),
  or
- the **column-matching code of a shipping product** that parses these exports, or
- **independent importers/parsers** whose expectations agree with each other.

Each section states which. Per-broker confidence is summarised at the end.

---

## 0. Bottom line

**There is no common tradebook format.** Each Indian broker exports a different file, with different
column names, different column order, different casing, a different container (CSV vs XLSX), and
different conventions. [Folioman's own import documentation](https://github.com/codereverser/folioman/blob/main/docs/import-tradebook.md)
(the FOSS personal-finance app by the author of `casparser`) says this explicitly:

> "Brokers do not share one standard export shape. Rather than hard-coding Zerodha (or any single
> broker), Folioman asks you to **map once per file** … Other brokers use different header names —
> that is expected."

I found no SEBI/exchange-mandated standard retail tradebook CSV.

What brokers *do* share is only a **semantic** field set: a date, a security (symbol and/or ISIN), a
quantity, a price, and a buy/sell side, plus an order/trade id. Names and encodings of those fields
differ everywhere. Two consequences that matter more than the column names:

1. **Brokerage/charges are essentially never in the tradebook.** All tradebook formats examined carry
   price and quantity only; brokerage, STT, stamp duty, GST live in a *separate* report (contract
   note, P&L, or charges/ledger). Do not expect a `brokerage` column in a tradebook.
2. **The export is the only source of trade history, but brokers cap the window.** Zerodha's Console
   tradebook is downloadable **365 days at a time** ([Zerodha support](https://support.zerodha.com/category/console/reports/other-queries/articles/where-can-i-see-all-the-trades-i-ve-taken-for-a-particular-period)),
   so multi-year history requires repeated exports, and old sells appear without their matching buys
   (Folioman calls these "orphan sells" and refuses to guess a cost basis).

### Comparison at a glance

| | Zerodha (Console) | Groww | Angel One | Upstox |
|---|---|---|---|---|
| Container | CSV or XLSX (CSV cleaner) | **XLSX** (Stock Order History) | CSV / XLSX (back-office trade book) | XLSX / CSV (reports tradebook) |
| Header row | row 1 (CSV); XLSX has banner rows above | **row 6** (5 preamble rows) | row 1 (adapter scans for a header row) | row 1 (adapter scans for a header row) |
| Symbol column | `symbol` | `Symbol` (and `Stock name`) | `Scrip/Contract` | `Company` (contract/symbol) |
| Side column | `trade_type` (`buy`/`sell`, lower-case) | `Type` (`Buy`/`Sell`) | `Buy/Sell` | `Side` |
| Qty/price | `quantity`, `price` (per unit) | `Quantity`, **`Value` (total, not per unit)** | `Quantity`, **separate `Buy Price` / `Sell Price`** | `Quantity`, `Price` |
| Date/time | `trade_date` (date) + `order_execution_time` (ISO datetime) | single `Execution date and time` | single `Date` (date+time) | `Date` + `Trade Time` |
| ISIN present | yes (equity) | yes (`ISIN`) | no (via `Scrip/Contract` only) | no (`Scrip Code` is not ISIN) |
| Brokerage/charges | **none** | **none** | **none** | **none** |
| Status filter needed | no | **yes** (`Order status` = `Executed`) | no | no |

---

## 1. Zerodha — Console Tradebook (verified against real files)

**Where:** Console → Reports → Tradebook → pick segment + date range → Download → CSV or XLSX
([Zerodha support](https://support.zerodha.com/category/console/reports/other-queries/articles/where-can-i-see-all-the-trades-i-ve-taken-for-a-particular-period)).
Separate "external tradebooks" carry corporate-action, IPO, OFS, buyback, and transfer-in/out rows
that the normal tradebook omits.

**Header (17 columns, equity):**

```
symbol,isin,trade_date,exchange,segment,series,trade_type,auction,quantity,price,trade_id,order_id,order_execution_time
```

**Real sample rows** — verbatim from a sanitised real export committed by the `folioman` project
([fixture](https://github.com/codereverser/folioman/blob/main/app/tests/fixtures/zerodha/tradebook-zerodha-2024.csv);
`trade_id`/`order_id` synthetic, symbols/dates/qty/price unchanged):

```
CMSINFO,INE925R01014,2024-07-23,NSE,EQ,EQ,buy,false,50.000000,530.000000,T2024072301,O2024072301,2024-07-23T12:20:42
DREAMFOLKS,INE0JS101016,2024-08-05,NSE,EQ,EQ,buy,false,5.000000,450.000000,T2024080501,O2024080501,2024-08-05T12:39:34
DREAMFOLKS,INE0JS101016,2024-08-05,NSE,EQ,EQ,buy,false,27.000000,450.000000,T2024080502,O2024080501,2024-08-05T12:39:34
HDFC,INE001A01036,2022-06-27,NSE,EQ,EQ,buy,false,26.000000,2200.000000,T2022062701,O2022062701,2022-06-27T12:33:59
```

**F&O export appends `expiry_date`.** Real sample from a public sample-trades file
([bsteps/zerodha-fno-trade-journal](https://github.com/bsteps/zerodha-fno-trade-journal/blob/master/sample-trades.csv)):

```
symbol,isin,trade_date,exchange,segment,series,trade_type,auction,quantity,price,trade_id,order_id,order_execution_time,expiry_date
NIFTY2560524750PE,,2025-06-02,NSE,FO,,sell,false,150.000000,326.800000,238243,1500000005277076,2025-06-02T09:21:55,2025-06-05
```

**Field semantics verified from those files:**

| Column | Observed |
|---|---|
| `symbol` | trading symbol (`CMSINFO`, `NIFTY2560524750PE` for F&O) |
| `isin` | ISIN for equity; **blank for F&O** |
| `trade_date` | `YYYY-MM-DD` |
| `exchange` | `NSE` / `BSE` |
| `segment` | `EQ` for equity; `FO` for F&O (blank in one equity fixture — treat as optional) |
| `series` | `EQ` for equity; blank for F&O |
| `trade_type` | lower-case `buy` / `sell` |
| `auction` | `true` / `false` (string) |
| `quantity` | fixed 6 decimals (`50.000000`) |
| `price` | fixed 6 decimals, **per unit** (`530.000000`) |
| `trade_id` | per-fill id |
| `order_id` | per-order id — **one order → many fills**, all sharing `order_id` with distinct `trade_id` |
| `order_execution_time` | ISO local datetime `YYYY-MM-DDTHH:MM:SS` (no timezone) |
| `expiry_date` | present only in F&O exports; `YYYY-MM-DD` |

**Corroboration:** a Beancount importer ships a hard-coded assertion of exactly this header string
([`expected = "symbol,isin,trade_date,exchange,segment,series,trade_type,auction,quantity,price,trade_id,order_id,order_execution_time"`](https://github.com/prabusw/beancount-importers-india/blob/master/importers/zerodha/zerodha.py)),
and the `tearsheet` project documents the same columns
([AGENTS.md](https://github.com/tatvadesai/tearsheet)).

**Gotchas**
- **XLSX export contains banner rows above the header** (so a naive `read_excel` header=0 fails);
  CSV is the cleaner input.
- Some exporters/parsers expect `tradingsymbol` / `average_price` / `fill_timestamp` — those are
  **Kite Connect API** (`GET /trades`) field names, *not* the Console CSV. Projects that detect a
  "Zerodha signature" via `tradingsymbol` are matching the API shape, not the tradebook.
- Use `trade_id` (not `order_id`) as the row idempotency key; one order legitimately splits into many
  fills with identical date/symbol/qty/price.

---

## 2. Groww — "Stock Order History" (verified against the real header)

**Where:** Groww app/web → Reports → Transactions → **Stock Order History** → download (XLSX). This
is the file Groww calls its order/trade history; Groww does **not** offer a Kite-Connect-style API
for retail, so CSV/XLSX export is the canonical path.

**The file is an XLSX with a 5-row preamble; the header is row 6.** Two independent importers that
were written against real files agree on the exact header, and both hard-code "skip 5 rows":

From [`rudra-dhamecha/groww-financial-tracker`](https://github.com/rudra-dhamecha/groww-financial-tracker/blob/main/backend/app/services/stock_import.py)
(its own error string states the expected header verbatim):

> "Expected header: Stock name, Symbol, ISIN, Type, Quantity, Value, Exchange, Exchange Order Id,
> Execution date and time, Order status."

From [`sunaiworld/siddegowda-portfolio`](https://github.com/sunaiworld/siddegowda-portfolio/blob/main/data/imports/groww/import_groww.py),
which documents the preamble explicitly:

> Row 4: Order history for stocks from \<date\> to \<date\>
> **Row 6: Stock name | Symbol | ISIN | Type | Quantity | Value | Exchange | Exchange Order Id | Execution date and time | Order status**

And [`tatvadesai/tearsheet`](https://github.com/tatvadesai/tearsheet) documents the identical set:
`Stock name, Symbol, ISIN, Type (BUY/SELL), Quantity, Value, Exchange, Exchange Order Id, Execution date and time, Order status`,
read with "skip 5 header rows, filter status='Executed'".

**Header (row 6):**

```
Stock name,Symbol,ISIN,Type,Quantity,Value,Exchange,Exchange Order Id,Execution date and time,Order status
```

**Sample row** — the **column set and formats are verified**; the *values* below are illustrative
(no raw Groww file was obtainable to quote verbatim):

```
Infosys Ltd,INFY,INE009A01021,Buy,10,15000.00,NSE,130000000012345,01-07-2024 10:15 AM,Executed
```

**Field semantics (from the importers' code):**

| Column | Observed / required handling |
|---|---|
| `Stock name` | company display name (may contain spaces) |
| `Symbol` | tradable symbol |
| `ISIN` | ISIN (present) |
| `Type` | `Buy` / `Sell` |
| `Quantity` | integer shares |
| **`Value`** | **total consideration for the fill, *not* per-unit price** |
| `Exchange` | `NSE` / `BSE` |
| `Exchange Order Id` | broker's exchange order id |
| `Execution date and time` | `DD-MM-YYYY hh:mm AM/PM` (parser layout `02-01-2006 03:04 PM`) |
| `Order status` | **filter to `Executed`** — pending/rejected/cancelled rows are in the same file |

**Two gotchas that will silently corrupt cost basis if missed:**
1. **`Value` ÷ `Quantity` = price.** Groww gives the gross amount, not the unit price. Both the
   `siddegowda` importer (`price = value / quantity`) and the shipping `arthveda` product
   (divides by quantity; its code comment: *"Groww provides the price as total price for the
   trade"*) handle it this way.
2. **The same file contains non-executed orders.** Rows must be filtered on `Order status == Executed`
   before import.
3. Groww issues no trade id; use `Exchange Order Id` as the idempotency key.

**Separate Groww formats (do not confuse):**
- *Groww holdings snapshot CSV*: `Stock Name, Quantity, Average Price, Current Price, Invested Value`
  ([`ranjulbn20/Punji`](https://github.com/ranjulbn20/Punji/blob/main/backend/importers/groww.py)) —
  a position snapshot with no trade dates.
- *Groww MF holdings CSV*: `Fund Name, Units, Average NAV, Current NAV, Invested Amount` (same
  source).
- An `arthveda` **Groww tradebook CSV** variant also exists where the price column is literally
  headed `Price` and the id is `Exchange Order Id` with `Execution date and time` — same value-is-total
  convention. This suggests Groww ships both a name-based and a symbol-based export.

---

## 3. Angel One — back-office Trade Book (medium confidence)

I found **no public raw Angel One tradebook file**; the evidence is parser code. Angel One's own
"Trade Book"/order-history export and its contract-note PDF are different documents — do not treat
them as one format. (The public Angel One fixtures I found, e.g. in
[`RahulSunnyCS/trade-analytics`](https://github.com/RahulSunnyCS/trade-analytics/tree/main/tests/fixtures),
are **contract-note PDF text dumps** headed "CONTRACT NOTE CUM TAX INVOICE", not tradebooks.)

The strongest evidence is the `arthveda` product's file adapter
([`file.go`](https://github.com/Kk-ships/arthveda/blob/main/api/internal/domain/broker_integration/file.go)),
which locates the header row and columns by substring match for Angel One:

- symbol ← header containing **`Scrip/Contract`**
- **`Segment`** (equity is `CAPITAL`)
- side ← **`Buy/Sell`**
- qty ← **`Quantity`**
- **`Buy Price`** and **`Sell Price`** (separate columns — only the relevant side is populated)
- **`Order ID`**
- date+time ← header containing **`Date`** (single combined date+time field)

So the effective column set is:

```
Scrip/Contract,Segment,Buy/Sell,Quantity,Buy Price,Sell Price,Order ID,Date
RELIANCE,CAPITAL,Buy,5,2450.00,,1234567890,15/07/24 09:32
```

*(Column set from the shipping adapter; row values illustrative. Date is a combined date+time string;
the adapter parses it as Go `1/2/06 15:04`, i.e. `M/D/YY HH:MM`, which for an Indian broker is more
likely intended as `D/M/YY` — treat the date layout as unverified.)*

Independent hobby parsers expect a compatible but not identical shape, which is itself evidence of
intra-broker variation across Angel One's reports:

- [`universal_csv_parser.py`](https://github.com/Vinayachandran1709/trade-journal/blob/main/backend/app/services/universal_csv_parser.py)
  signature: `symbol`, `Buy/Sell`, `Net Qty`, `Avg Price`.
- [`niveshpath`](https://github.com/tripathigaurav/niveshpath/blob/main/frontend/src/utils/csvImporter.js):
  `Scripname`/`Script Name`, `Qty`, `Net Rate`/`Rate`, `Trade Date`, `Buy/Sell`.
- [`stocker-2.0`](https://github.com/superdev-windesign/stocker-2.0/blob/main/frontend/src/analytics/tradebook.js)
  detects Angel One via the headers `isinno` / `companyname` / `tradeqty`.

**Practical read:** Angel One has at least two export dialects (a trade book with `Scrip/Contract` +
separate buy/sell prices, and a charges/order report with `Scripname` + `Net Rate`). Match on a
signature set, not one fixed header.

---

## 4. Upstox — reports Tradebook / Realized P&L (medium confidence)

Again no public raw Upstox tradebook file was found. Evidence is the `arthveda` adapter (same
[`file.go`](https://github.com/Kk-ships/arthveda/blob/main/api/internal/domain/broker_integration/file.go))
plus one ETL schema that agrees with it.

**`arthveda` Upstox adapter** (substring anchors → columns):

- symbol ← **`Company`** (the column holding the instrument/contract name)
- **`Scrip Code`**
- **`Segment`** (`EQ`, `FO`, `COM`)
- **`Instrument Type`** (values seen: `European Call`, `European Put` — very Upstox-specific)
- **`Expiry`** (`dd-mm-yyyy`)
- **`Strike Price`**
- side ← **`Side`**
- **`Quantity`**
- **`Price`**
- trade id ← **`Trade Num`**
- **`Trade Time`** and **`Date`** (separate time and date columns)

```
Company,Scrip Code,Segment,Instrument Type,Expiry,Strike Price,Side,Quantity,Price,Trade Num,Trade Time,Date
RELIANCE,INE002A01018,EQ,,, ,Buy,5,2450.00,543210,09:32:15,15-07-2024
```

*(Column set from the shipping adapter; row values illustrative; exact header case/spacing inferred
from substring matching, so it is unverified.)*

This is corroborated by [`PtPrashantTripathi/PortfolioTracker`](https://github.com/PtPrashantTripathi/PortfolioTracker/blob/main/StockETL/ETL_SILVER/TradeHistory.py),
whose Upstox trade-history schema is built from `company`, `scrip_code`, `instrument_type`
(`European Call`/`European Put`), `expiry`, `strike_price`, `trade_number` (converted to int),
`trade_date`, `trade_time`, `quantity`, `side`.

**Upstox also has a distinct "Realized P&L" XLSX** (one row = a completed buy/sell pair), parsed by
[`hisaab`](https://github.com/Devansh-365/hisaab/blob/main/lib/parsers/upstox.ts) with:

```
scrip_name, symbol, isin, qty, buy_date, sell_date, buy_rate, sell_rate, scrip_opt, total_pl
```

It detects this format when headers include `scrip_name, symbol, qty, buy_date, sell_date`, then emits
**two transactions per row** (a BUY leg and a SELL leg). `scrip_opt` distinguishes EQ vs F&O. This is
a P&L report, not a fill-level tradebook — useful for reconciliation but it collapses intraday/multiple
fills.

A third, lower-confidence signature seen in a hobby universal parser is
`Trading Symbol, Transaction Type, Quantity, Order Date`
([`universal_csv_parser.py`](https://github.com/Vinayachandran1709/trade-journal/blob/main/backend/app/services/universal_csv_parser.py)).
Treat as a possible alternate dialect, not a verified header.

---

## 5. Is there a common format? — No, but a common *canonical* schema works

Evidence of divergence is direct: Folioman ships a **column-mapping wizard** precisely because it
cannot hard-code even Zerodha, let alone the others; every multi-broker project I found
(`arthveda`, `hisaab`, `niveshpath`, `stocker-2.0`, `universal_csv_parser`, `lume`) resolves broker
identity from header **signatures** and then applies a per-broker alias map. The header signatures in
`universal_csv_parser.py` (normalised) illustrate how disjoint they are:

```
zerodha      : tradingsymbol, exchange, trade date, trade type, quantity
groww        : trade date, stock symbol, transaction type, quantity, price
angel_one    : symbol, buy sell, net qty, avg price
upstox       : trading symbol, transaction type, quantity, order date
dhan         : security name, type, executed qty, avg traded price
5paisa       : scrip name, buy sell, qty, rate
icici_direct : stock, action, qty, price, trade date
hdfc_sec     : symbol, transaction type, quantity, average price
kotak_sec    : symbol, b s, qty, price, date
motilal_oswal: scrip, buy sell, qty, rate, trade date
```

(Note this particular project's `zerodha` signature uses the Kite **API** names — an example of why
tradebook CSV and broker API shapes must not be conflated.)

**The de-facto standard is a canonical target schema, mapped per broker.** Folioman's backend
contract is a good, minimal model
([developer note](https://github.com/codereverser/folioman/blob/main/docs/developer/tradebook-import.md)):

> **Required:** `security_type, name, date, transaction_type, units, price`
> **Optional:** `symbol, isin, amfi_code, principal, amount, fees, stamp_duty, brokerage, currency,
> source_ref, folio_number, broker`
> `source_ref` holds the broker trade id and is part of the dedup key, so two genuinely-identical
> fills with different trade ids stay distinct and re-imports are idempotent.

---

## 6. What this means for `wealth-tracker`

Maps onto the existing domain model (`docs/adr/0001-ledger-first-positions.md`,
`docs/adr/0015-instrument-identity-model.md`, `CONTEXT.md`):

- **Per-broker parser, one canonical `Transaction`.** Detect broker by header signature, map to the
  canonical fields (`date, type, quantity, price, symbol, isin, source_ref`), then emit `Transaction`
  rows. No broker-specific columns should reach the ledger.
- **`source_ref` = trade id is the idempotency key.** Zerodha `trade_id`, Groww `Exchange Order Id`,
  Upstox `Trade Num`, Angel One `Order ID`. Where absent, fall back to a content fingerprint
  (date|symbol|side|qty|price).
- **Container reality:** Zerodha/Groww ship XLSX with banner rows (Groww 5 rows, header at row 6);
  expect an openpyxl path, not just `csv`.
- **Charges are not in the tradebook.** If cost basis must include brokerage/STT, that is a separate
  ingest (contract note / P&L / ledger), consistent with ADR-0008 (tax out of scope).
- **ISIN is only reliably present for Zerodha and Groww** in these exports; Angel One/Upstox need
  symbol→ISIN resolution (NSE `EQUITY_L.csv`, per the market-data research).
- **Export-window / orphan-sell handling is mandatory.** Any tradebook download is a window; a sell
  without a matching prior buy must be recorded as an incomplete-history position rather than guessed
  (Folioman's `cost_basis_complete=False` / `PartialBlock` is the pattern to copy).

---

## 7. Confidence and missing evidence

| Broker | Confidence in column set | Basis |
|---|---|---|
| Zerodha | **High** | 2 real sanitised files (equity + F&O) + a hard-coded header assertion in a third project |
| Groww | **High** | exact 10-column header stated independently by 2 importers + 1 product doc; 6th-row header and `Value`=total verified in code |
| Angel One | **Medium** | one shipping product's adapter + 3 hobby parsers with partially differing aliases; no raw file |
| Upstox | **Medium** | one shipping product's adapter + one agreeing ETL schema; no raw file |

**Not verified / open:**
1. **No live exports.** I never logged into a broker; the Angel One and Upstox sample rows above are
   illustrative (column sets verified, values invented).
2. **Exact date formats for Angel One and Upstox** (whether `D/M/YY` or `M/D/YY`; date vs time
   separation) are unverified.
3. **Zerodha download window** conflicts across secondary sources: Zerodha's own support article says
   **365 days**; a blog claimed 3 years. The first-party page is authoritative.
4. **Whether Groww offers a true fill-level "tradebook"** (vs the order-history XLSX that mixes
   executed and non-executed orders) is unresolved; the order-history file is what every parser uses.
5. **Angel One intraday time**: one secondary source (Riskora) claims Angel One's Trades-and-Charges
   export has no time-of-day, while `arthveda` parses a combined date+time — these may be two
   different reports.
6. **Upstox `Company` column semantics** (company name vs contract/symbol) is inferred from the
   adapter's use of it as the symbol, not confirmed.

**Cheapest way to close these:** have a holder of each account export one tradebook (equity, a single
day) and record the literal header line + one row. That converts Angel One and Upstox from medium to
high confidence and pins the date formats.

---

## Sources

**Primary artefacts (real files / shipping code):**
- Zerodha real fixture (equity), sanitised from a real Console export — https://github.com/codereverser/folioman/blob/main/app/tests/fixtures/zerodha/tradebook-zerodha-2024.csv ; fixture notes https://github.com/codereverser/folioman/blob/main/app/tests/fixtures/zerodha/README.md
- Zerodha real sample (F&O, adds `expiry_date`) — https://github.com/bsteps/zerodha-fno-trade-journal/blob/master/sample-trades.csv
- Zerodha header hard-coded in a Beancount importer — https://github.com/prabusw/beancount-importers-india/blob/master/importers/zerodha/zerodha.py
- Zerodha column summary — https://github.com/tatvadesai/tearsheet (AGENTS.md)
- Zerodha Console tradebook how-to (365-day limit) — https://support.zerodha.com/category/console/reports/other-queries/articles/where-can-i-see-all-the-trades-i-ve-taken-for-a-particular-period
- Folioman tradebook import docs ("brokers do not share one standard export shape") — https://github.com/codereverser/folioman/blob/main/docs/import-tradebook.md ; developer canonical-schema note https://github.com/codereverser/folioman/blob/main/docs/developer/tradebook-import.md
- Groww exact header + 6th-row preamble — https://github.com/sunaiworld/siddegowda-portfolio/blob/main/data/imports/groww/import_groww.py
- Groww exact header in an error string; `Value`/status handling — https://github.com/rudra-dhamecha/groww-financial-tracker/blob/main/backend/app/services/stock_import.py
- Groww column list + "skip 5 rows, filter status=Executed" — https://github.com/tatvadesai/tearsheet
- Groww importers corroborating `Exchange Order Id` + `Execution date and time` — https://github.com/tks18/personal-finance-etl , https://github.com/thepranaygupta/khaata , https://github.com/ankitbhardwaj66/xirrledger , https://github.com/git-varun/Aureon , https://github.com/saisudheerp/financetracker
- Groww holdings / MF CSV column sets — https://github.com/ranjulbn20/Punji/blob/main/backend/importers/groww.py
- `arthveda` shipping per-broker adapters (Angel One, Groww, Upstox, Zerodha; header matching + date layouts + Groww total-value handling) — https://github.com/Kk-ships/arthveda/blob/main/api/internal/domain/broker_integration/file.go
- Upstox trade-history schema (`company`, `scrip_code`, `instrument_type`, `European Call/Put`, `expiry`, `strike_price`, `trade_number`) — https://github.com/PtPrashantTripathi/PortfolioTracker/blob/main/StockETL/ETL_SILVER/TradeHistory.py
- Upstox Realized-P&L XLSX columns (`scrip_name, symbol, isin, qty, buy_date, sell_date, buy_rate, sell_rate, scrip_opt`) — https://github.com/Devansh-365/hisaab/blob/main/lib/parsers/upstox.ts
- Angel One contract-note fixtures (to distinguish from tradebooks) — https://github.com/RahulSunnyCS/trade-analytics/tree/main/tests/fixtures
- Upstox string aliases — https://github.com/Kk-ships/arthveda (above)

**Secondary / corroborating parsers (alias maps, detection signatures):**
- Multi-broker header signatures — https://github.com/Vinayachandran1709/trade-journal/blob/main/backend/app/services/universal_csv_parser.py
- Multi-broker detection + aliases — https://github.com/superdev-windesign/stocker-2.0/blob/main/frontend/src/analytics/tradebook.js , https://github.com/tripathigaurav/niveshpath/blob/main/frontend/src/utils/csvImporter.js
- Broker parsers (Zerodha/Angel/Groww/Upstox) and broker detector — https://github.com/Devansh-365/hisaab/tree/main/lib/parsers
- LLM/heuristic column-mapping for arbitrary broker exports — https://github.com/vishwastam/lume/blob/main/src/lume/portfolio/ingest.py

**Rejected / low value:**
- US-broker CSV research doc (`Apex-Logics/TradVue/docs/research/broker-csv-formats.md`) — Robinhood/Schwab/IBKR etc.; no Indian brokers.
- SEO/landing pages (`tradeloop.trade`, `tradelyser.com`, `riskora.in`, `journalplus.co`, `fivesviz`, `arthveda.app` marketing) — describe workflow, not columns; used only as pointers to the real repos above.
- Angel One FAQ/RAG dumps (`Unplugged-Sirius/AngelOne-*`, `PrakshayJoshi/Alltius.ai`) — matched keyword "Scrip/Contract" but contain no tradebook columns.
