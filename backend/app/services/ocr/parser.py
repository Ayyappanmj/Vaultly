import re
from datetime import datetime, timezone
from decimal import Decimal
from app.schemas.ocr import ParsedLineItem, ParsedReceiptData

CURRENCY_SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "USD": "USD",
    "EUR": "EUR",
    "GBP": "GBP",
    "CAD": "CAD",
    "AUD": "AUD",
}

DATE_PATTERNS = [
    # YYYY-MM-DD or YYYY/MM/DD
    (r"\b(20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b", "%Y-%m-%d"),
    # MM/DD/YYYY or MM-DD-YYYY
    (r"\b(0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])[-/](20\d{2})\b", "%m/%d/%Y"),
    # DD/MM/YYYY
    (r"\b(0[1-9]|[12]\d|3[01])[-/](0[1-9]|1[0-2])[-/](20\d{2})\b", "%d/%m/%Y"),
    # Month DD, YYYY (e.g. Jan 15, 2024 or January 15, 2024)
    (
        r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2}),?\s+(20\d{2})\b",
        "named_month",
    ),
]

PAYMENT_METHODS = [
    "VISA",
    "MASTERCARD",
    "AMEX",
    "AMERICAN EXPRESS",
    "DISCOVER",
    "DEBIT",
    "CASH",
    "APPLE PAY",
    "GOOGLE PAY",
]


def normalize_text(text: str) -> list[str]:
    """Cleans up raw OCR lines."""
    lines = [line.strip() for line in text.splitlines()]
    return [line for line in lines if line]


def parse_receipt_text(raw_text: str) -> ParsedReceiptData:
    lines = normalize_text(raw_text)
    if not lines:
        return ParsedReceiptData()

    parsed = ParsedReceiptData()

    # 1. Currency detection
    detected_currency = "USD"
    for symbol, code in CURRENCY_SYMBOLS.items():
        if symbol in raw_text:
            detected_currency = code
            break
    parsed.currency = detected_currency

    # 2. Merchant name: First 1-3 lines usually contain the merchant name
    merchant_candidates = []
    for line in lines[:5]:
        # Filter out lines that look like dates, times, or headers like 'WELCOME'
        clean_line = re.sub(r"[*=_-]+", "", line).strip()
        if not clean_line or len(clean_line) < 3:
            continue
        if re.search(
            r"\b(receipt|welcome|tax invoice|store|tel|phone|cashier|date|time)\b",
            clean_line,
            re.I,
        ):
            continue
        merchant_candidates.append(clean_line)

    if merchant_candidates:
        parsed.merchant_name = merchant_candidates[0]
        parsed.merchant_confidence = 0.85 if len(parsed.merchant_name) > 3 else 0.50

    # 3. Date detection
    for pattern, fmt in DATE_PATTERNS:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            try:
                if fmt == "named_month":
                    month_str, day_str, year_str = match.groups()
                    dt = datetime.strptime(
                        f"{month_str[:3]} {day_str} {year_str}", "%b %d %Y"
                    )
                elif fmt == "%m/%d/%Y":
                    m, d, y = match.groups()
                    dt = datetime(int(y), int(m), int(d))
                elif fmt == "%d/%m/%Y":
                    d, m, y = match.groups()
                    dt = datetime(int(y), int(m), int(d))
                else:
                    y, m, d = match.groups()
                    dt = datetime(int(y), int(m), int(d))
                parsed.purchase_date = dt.replace(tzinfo=timezone.utc)
                parsed.date_confidence = 0.90
                break
            except Exception:
                continue

    # 4. Receipt number / Invoice number
    receipt_no_match = re.search(
        r"\b(?:receipt|invoice|trans(?:action)?|order|bill)\s*(?:#|no\.?|id)?\s*[:\s]?\s*([A-Za-z0-9_-]{4,20})\b",
        raw_text,
        re.I,
    )
    if receipt_no_match:
        parsed.receipt_number = receipt_no_match.group(1).strip()
        parsed.receipt_number_confidence = 0.80

    # 5. Payment method
    for method in PAYMENT_METHODS:
        if re.search(rf"\b{method}\b", raw_text, re.IGNORECASE):
            parsed.payment_method = method.upper()
            break

    # 6. Amounts: Total, Subtotal, Tax
    total_match = re.search(
        r"\b(?:grand\s+total|total\s+due|total|amount\s+due)\s*[:\s]*[\$€£¥]?\s*(\d+[.,]\d{2})\b",
        raw_text,
        re.I,
    )
    if total_match:
        val_str = total_match.group(1).replace(",", ".")
        try:
            parsed.total_amount = Decimal(val_str)
            parsed.total_confidence = 0.95
        except Exception:
            pass

    subtotal_match = re.search(
        r"\b(?:subtotal|sub-total|sub\s+total)\s*[:\s]*[\$€£¥]?\s*(\d+[.,]\d{2})\b",
        raw_text,
        re.I,
    )
    if subtotal_match:
        val_str = subtotal_match.group(1).replace(",", ".")
        try:
            parsed.subtotal = Decimal(val_str)
        except Exception:
            pass

    tax_match = re.search(
        r"\b(?:tax|vat|gst|sales\s+tax)\s*[:\s]*[\$€£¥]?\s*(\d+[.,]\d{2})\b",
        raw_text,
        re.I,
    )
    if tax_match:
        val_str = tax_match.group(1).replace(",", ".")
        try:
            parsed.tax_amount = Decimal(val_str)
        except Exception:
            pass

    # 7. Line items parsing
    line_item_pattern = re.compile(
        r"^(.+?)\s+(?:(\d+)\s+x\s+)?[\$€£¥]?\s*(\d+[.,]\d{2})$", re.IGNORECASE
    )
    items: list[ParsedLineItem] = []
    for line in lines:
        # Ignore lines that are total/subtotal/tax/payment
        if re.search(
            r"\b(total|subtotal|tax|vat|gst|cash|change|balance|visa|mastercard|amex|date|time|thank)\b",
            line,
            re.I,
        ):
            continue
        match = line_item_pattern.match(line)
        if match:
            desc, qty_str, price_str = match.groups()
            clean_desc = desc.strip(" *-#")
            if len(clean_desc) >= 2 and not clean_desc.isdigit():
                try:
                    price = Decimal(price_str.replace(",", "."))
                    qty = Decimal(qty_str) if qty_str else Decimal("1.0")
                    items.append(
                        ParsedLineItem(
                            description=clean_desc,
                            quantity=qty,
                            unit_price=price if not qty_str else (price / qty),
                            total_price=price,
                            confidence=0.80,
                        )
                    )
                except Exception:
                    continue

    parsed.line_items = items

    # If total amount wasn't found via keyword but line items exist, sum line items
    if parsed.total_amount is None and items:
        computed_total = sum(item.total_price for item in items)
        if parsed.tax_amount:
            computed_total += parsed.tax_amount
        parsed.total_amount = computed_total
        parsed.total_confidence = 0.70

    # 8. Overall confidence score
    confidence_factors = [
        parsed.merchant_confidence,
        parsed.date_confidence,
        parsed.total_confidence,
    ]
    valid_factors = [f for f in confidence_factors if f > 0]
    parsed.overall_confidence = (
        round(sum(valid_factors) / len(valid_factors), 2) if valid_factors else 0.0
    )

    return parsed
