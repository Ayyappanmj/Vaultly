import csv
import io
from datetime import datetime
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_receipts_csv(receipts: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Receipt ID",
            "Purchase Date",
            "Merchant",
            "Total Amount",
            "Currency",
            "Category",
            "Payment Method",
            "Receipt Number",
            "Notes",
        ]
    )
    for r in receipts:
        writer.writerow(
            [
                str(r.get("id", "")),
                r.get("purchase_date", "").strftime("%Y-%m-%d")
                if isinstance(r.get("purchase_date"), datetime)
                else str(r.get("purchase_date", "")),
                r.get("merchant_name", ""),
                str(r.get("total_amount", "")),
                r.get("currency", "USD"),
                r.get("category_name", ""),
                r.get("payment_method", ""),
                r.get("receipt_number", ""),
                r.get("notes", ""),
            ]
        )
    return output.getvalue()


def parse_receipts_csv(csv_content: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(csv_content))
    parsed_receipts = []
    for row in reader:
        try:
            date_val = datetime.strptime(
                row.get("Purchase Date", "").strip(), "%Y-%m-%d"
            )
            amount_val = Decimal(row.get("Total Amount", "0").strip())
            parsed_receipts.append(
                {
                    "merchant_name": row.get("Merchant", "").strip(),
                    "purchase_date": date_val,
                    "total_amount": amount_val,
                    "currency": row.get("Currency", "USD").strip(),
                    "category_name": row.get("Category", "").strip(),
                    "payment_method": row.get("Payment Method", "").strip(),
                    "receipt_number": row.get("Receipt Number", "").strip(),
                    "notes": row.get("Notes", "").strip(),
                }
            )
        except Exception:
            continue
    return parsed_receipts


def generate_expense_pdf(
    user_name: str, receipts: list[dict], total_spent: Decimal, currency: str = "USD"
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=10,
    )
    elements.append(Paragraph("Vaultly — Expense Report", title_style))

    # Meta
    meta_style = ParagraphStyle(
        name="MetaStyle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=15,
    )
    date_str = datetime.now().strftime("%B %d, %Y")
    elements.append(
        Paragraph(
            f"Prepared for: <b>{user_name}</b> | Generated: {date_str} | Total: <b>{currency} {total_spent:,.2f}</b>",
            meta_style,
        )
    )
    elements.append(Spacer(1, 10))

    # Table
    table_data = [["Date", "Merchant", "Category", "Payment", f"Amount ({currency})"]]
    for r in receipts:
        d = r.get("purchase_date")
        d_str = d.strftime("%Y-%m-%d") if isinstance(d, datetime) else str(d)[:10]
        table_data.append(
            [
                d_str,
                str(r.get("merchant_name", ""))[:25],
                str(r.get("category_name", "General"))[:20],
                str(r.get("payment_method", "-"))[:15],
                f"{Decimal(str(r.get('total_amount', '0'))):,.2f}",
            ]
        )

    table = Table(table_data, colWidths=[80, 160, 110, 90, 100])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f8fafc")],
                ),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)
    return buffer.getvalue()
