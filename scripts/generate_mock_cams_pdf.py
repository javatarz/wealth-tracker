"""Generate a fake CAMS CAS PDF for development and testing.

Creates a PDF that casparser can parse, with synthetic mutual fund
transaction data. No personal or real financial data is included.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from fpdf import FPDF

# ---------------------------------------------------------------------------
# Synthetic data
# ---------------------------------------------------------------------------

SCHEMES_META = [
    (
        "HGFG",
        "HDFC Top 200 Fund - Direct Plan - Growth",
        "INF123VGHI56",
        "123456",
        "HDFC Mutual Fund",
    ),
    (
        "ICPG",
        "ICICI Prudential Value Discovery Fund - Direct - Growth",
        "INF109KIBB78",
        "234567",
        "ICICI Prudential Mutual Fund",
    ),
    (
        "SBEC",
        "SBI Equity Hybrid Fund - Direct Plan - Growth",
        "INF200KJCC90",
        "345678",
        "SBI Mutual Fund",
    ),
    (
        "KKMF",
        "Kotak Flexicap Fund - Direct - Growth",
        "INF174KJDD12",
        "456789",
        "Kotak Mahindra Mutual Fund",
    ),
]


@dataclass
class Transaction:
    date: date
    description: str
    amount: Decimal
    units: Decimal
    nav: Decimal
    balance: Decimal


@dataclass
class SchemeData:
    code: str
    name: str
    isin: str
    amfi: str
    amc: str = ""
    transactions: list[Transaction] = field(default_factory=list)

    @property
    def close_units(self) -> Decimal:
        return self.transactions[-1].balance if self.transactions else Decimal(0)

    @property
    def last_nav(self) -> Decimal:
        return self.transactions[-1].nav if self.transactions else Decimal(0)

    @property
    def last_value(self) -> Decimal:
        return (self.close_units * self.last_nav).quantize(Decimal("0.01"))


@dataclass
class FolioData:
    folio_no: str
    pan: str
    holder_name: str
    schemes: list[SchemeData] = field(default_factory=list)


def _generate_transactions(
    scheme_code: str,
    start_date: date,
    end_date: date,
    seed: int,
) -> list[Transaction]:
    rng = random.Random(seed)
    transactions: list[Transaction] = []
    balance = Decimal(0)
    nav_start = Decimal(str(round(rng.uniform(10, 100), 4)))

    txn_date = start_date + timedelta(days=rng.randint(1, 15))
    amount = Decimal(str(round(rng.uniform(10000, 100000), 2)))
    nav = nav_start
    units = (amount / nav).quantize(Decimal("0.001"))
    balance += units
    transactions.append(Transaction(txn_date, "Purchase", -amount, units, nav, balance))

    current_date = txn_date
    while current_date < end_date - timedelta(days=15):
        current_date += timedelta(days=rng.randint(30, 90))
        if current_date >= end_date - timedelta(days=15):
            break
        txn_type = rng.choices(
            ["Purchase", "Purchase", "Redemption", "Dividend"],
            weights=[4, 3, 2, 1],
        )[0]
        nav = nav_start + Decimal(str(round(rng.uniform(-5, 15), 4)))
        if nav < Decimal(1):
            nav = nav_start
        if txn_type == "Purchase":
            amount = Decimal(str(round(rng.uniform(5000, 50000), 2)))
            units = (amount / nav).quantize(Decimal("0.001"))
            balance += units
            transactions.append(
                Transaction(current_date, txn_type, -amount, units, nav, balance)
            )
        elif txn_type == "Redemption":
            if balance < Decimal(100):
                continue
            units_to_sell = (
                Decimal(str(round(rng.uniform(100, min(500, int(balance))), 3))) / nav
            ).quantize(Decimal("0.001"))
            if units_to_sell >= balance:
                units_to_sell = balance - Decimal("0.001")
            amount = (units_to_sell * nav).quantize(Decimal("0.01"))
            balance -= units_to_sell
            transactions.append(
                Transaction(
                    current_date, txn_type, amount, -units_to_sell, nav, balance
                )
            )
        else:
            rate = rng.choice([Decimal("0.50"), Decimal("1.00"), Decimal("2.00")])
            div_amount = (rate * balance / nav).quantize(Decimal("0.01"))
            transactions.append(
                Transaction(current_date, "IDCW", div_amount, Decimal(0), nav, balance)
            )

    nav_final = nav_start + Decimal(str(round(rng.uniform(0, 20), 4)))
    if transactions:
        transactions.append(
            Transaction(
                end_date,
                "(Adjustment)",
                Decimal(0),
                Decimal(0),
                nav_final,
                transactions[-1].balance,
            )
        )

    return transactions


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

L = 56  # left margin
# For right-aligned columns, the VALUE must end at the same x as the
# right edge of the header text. We precompute header x_hi values.
HEADER_LABELS = {
    "Date": "Date",
    "Transaction": "Transaction",
    "Amount": "Amount",
    "Units": "Units",
    "Price": "Price",
    "Unit Balance": "Unit Balance",
}
CELL_H = 10


class CAMSPDF(FPDF):
    def __init__(self) -> None:
        super().__init__(orientation="P", unit="pt", format="A4")
        self.set_auto_page_break(auto=False)
        self.set_margin(0)
        self._header_widths: dict[str, float] = {}

    def _cache_header_widths(self) -> None:
        self.set_font("Helvetica", "B", 8)
        for col, label in HEADER_LABELS.items():
            self._header_widths[col] = self.get_string_width(label)

    def _col_x(self, col: str) -> float:
        return {
            "Date": 56,
            "Transaction": 130,
            "Amount": 300,
            "Units": 370,
            "Price": 430,
            "Unit Balance": 490,
        }[col]

    def _col_right(self, col: str) -> float:
        return self._col_x(col) + self._header_widths.get(col, 30)

    def _place_hdr(self, col: str, y: float) -> None:
        self.text(self._col_x(col), y + 2, HEADER_LABELS[col])

    def _place_val(self, col: str, y: float, text: str, size: int = 8) -> None:
        if col in ("Date", "Transaction"):
            self.text(self._col_x(col), y + 2, text)
        else:
            w = self.get_string_width(text)
            self.text(self._col_right(col) - w, y + 2, text)

    def _spacing(self, pt: float) -> None:
        self.ln(pt)

    def _line(
        self,
        text: str,
        style: str = "",
        size: int = 9,
        x: float = L,
        bold: bool = False,
    ) -> None:
        fs = "B" if bold else style
        self.set_font("Helvetica", fs, size)
        self.set_xy(x, self.get_y())
        self.multi_cell(0, CELL_H, text, new_x="LMARGIN", new_y="NEXT")

    def _txn_row(self, txn: Transaction) -> None:
        date_str = txn.date.strftime("%d-%b-%Y")
        desc = txn.description
        amount_str = f"{txn.amount:,.2f}"
        units_str = f"{txn.units:,.3f}"
        nav_str = f"{txn.nav:,.4f}"
        bal_str = f"{txn.balance:,.3f}"
        row_y = self.get_y()
        self.set_font("Helvetica", "", 8)
        self._place_val("Date", row_y, date_str)
        self._place_val("Transaction", row_y, desc)
        self._place_val("Amount", row_y, amount_str)
        self._place_val("Units", row_y, units_str)
        self._place_val("Price", row_y, nav_str)
        self._place_val("Unit Balance", row_y, bal_str)
        self.set_y(row_y + CELL_H)

    def _txn_header(self) -> None:
        row_y = self.get_y()
        self.set_font("Helvetica", "B", 8)
        self._place_hdr("Date", row_y)
        self._place_hdr("Transaction", row_y)
        self._place_hdr("Amount", row_y)
        self._place_hdr("Units", row_y)
        self._place_hdr("Price", row_y)
        self._place_hdr("Unit Balance", row_y)
        self.set_y(row_y + CELL_H)

    def generate(
        self,
        output_path: str,
        period_start: date,
        period_end: date,
        folios: list[FolioData],
    ) -> None:
        self.add_page()
        self._cache_header_widths()

        # Watermark (at very bottom of page)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(200, 200, 200)
        self.set_xy(10, 790)
        self.cell(0, 10, "CAMSCASWS Version:V3.4 Live-1017")
        self.set_text_color(0, 0, 0)
        self.set_y(20)

        # Title
        self._line("Consolidated Account Statement", "B", 14)
        self._spacing(5)

        # Period
        period_str = (
            f"{period_start.strftime('%d-%b-%Y')} To {period_end.strftime('%d-%b-%Y')}"
        )
        self._line(period_str, "", 10)
        self._spacing(8)

        # Investor info block
        self._line("Email Id: john.doe@example.com", "", 8)
        self._line("JOHN DOE", "", 8)
        self._line("123, MAIN STREET", "", 8)
        self._line("MUMBAI 400001", "", 8)
        self._line("Mobile: +919999999999", "", 8)
        self._spacing(10)

        for folio in folios:
            for scheme in folio.schemes:
                # Page break check
                if self.get_y() > 700:
                    self.add_page()
                    self.set_y(20)

                # AMC header
                self._line(scheme.amc, "B", 11)
                self._spacing(2)

                # Folio
                self._line(f"Folio No: {folio.folio_no}  PAN: {folio.pan}", "", 9)
                # Holder name
                self._line(folio.holder_name, "", 9)
                # Scheme code-name
                self._line(f"{scheme.code}-{scheme.name}", "", 9)
                # Registrar
                self._line("Registrar : CAMS", "", 8)
                # ISIN
                self._line(f"ISIN : {scheme.isin}", "", 8)
                # AMFI
                self._line(f"AMFI : {scheme.amfi}", "", 8)
                # Nominee
                self._line("Nominee 1 : PRIMARY NOMINEE", "", 8)
                self._spacing(2)

                # Opening Unit Balance
                self._line("Opening Unit Balance : 0.000", "", 9)
                self._spacing(2)

                # Transaction table header
                self._txn_header()

                # Transactions
                for txn in scheme.transactions:
                    if self.get_y() > 740:
                        self.add_page()
                        self.set_y(20)
                        self._txn_header()
                    self._txn_row(txn)

                self._spacing(2)

                # Footer
                self._line(f"Closing Unit Balance : {scheme.close_units:.3f}", "", 9)
                self._line(
                    f"NAV on {period_end.strftime('%d-%b-%Y')} : INR {scheme.last_nav:.4f}",
                    "",
                    9,
                )
                self._line(
                    f"Valuation on {period_end.strftime('%d-%b-%Y')} : INR {scheme.last_value:.2f}",
                    "",
                    9,
                )
                self._line("Total Cost Value : INR 0.00", "", 9)
                self._spacing(8)

        self.output(output_path)


def make_mock_data() -> list[FolioData]:
    period_start = date(2024, 4, 1)
    period_end = date(2025, 3, 31)
    return [
        FolioData(
            folio_no="1234567890",
            pan="ABCDE1234F",
            holder_name="JOHN DOE",
            schemes=[
                SchemeData(
                    code=SCHEMES_META[0][0],
                    name=SCHEMES_META[0][1],
                    isin=SCHEMES_META[0][2],
                    amfi=SCHEMES_META[0][3],
                    amc=SCHEMES_META[0][4],
                    transactions=_generate_transactions(
                        "HGFG", period_start, period_end, 42
                    ),
                ),
                SchemeData(
                    code=SCHEMES_META[1][0],
                    name=SCHEMES_META[1][1],
                    isin=SCHEMES_META[1][2],
                    amfi=SCHEMES_META[1][3],
                    amc=SCHEMES_META[1][4],
                    transactions=_generate_transactions(
                        "ICPG", period_start, period_end, 99
                    ),
                ),
            ],
        ),
        FolioData(
            folio_no="9876543210",
            pan="XYZPD1234K",
            holder_name="JOHN DOE",
            schemes=[
                SchemeData(
                    code=SCHEMES_META[2][0],
                    name=SCHEMES_META[2][1],
                    isin=SCHEMES_META[2][2],
                    amfi=SCHEMES_META[2][3],
                    amc=SCHEMES_META[2][4],
                    transactions=_generate_transactions(
                        "SBEC", period_start, period_end, 77
                    ),
                ),
            ],
        ),
    ]


if __name__ == "__main__":
    import sys

    output = sys.argv[1] if len(sys.argv) > 1 else "mock_cams_cas.pdf"
    pdf = CAMSPDF()
    pdf.generate(output, date(2024, 4, 1), date(2025, 3, 31), make_mock_data())
    print(f"Generated {output}")
