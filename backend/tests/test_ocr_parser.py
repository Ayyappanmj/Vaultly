from decimal import Decimal
from app.services.ocr.parser import parse_receipt_text
from app.services.ocr.provider import FallbackOCRProvider


def test_ocr_parser_synthetic_fixture():
    synthetic_receipt = """
    ACME SUPERMARKET
    123 Main Street, Suite 400
    Tel: (555) 019-2834
    
    Date: 2024-06-15
    Receipt #: ACM-88192
    
    Organic Bananas 1kg      $3.50
    Almond Milk 64oz         $4.99
    Whole Wheat Bread        $2.50
    
    Subtotal:                $10.99
    Tax:                     $0.88
    Total Due:               $11.87
    
    Payment: VISA **** 1234
    Thank you for shopping with us!
    """

    parsed = parse_receipt_text(synthetic_receipt)
    assert parsed.merchant_name == "ACME SUPERMARKET"
    assert parsed.merchant_confidence > 0.5
    assert parsed.receipt_number == "ACM-88192"
    assert parsed.purchase_date is not None
    assert parsed.purchase_date.strftime("%Y-%m-%d") == "2024-06-15"
    assert parsed.total_amount == Decimal("11.87")
    assert parsed.subtotal == Decimal("10.99")
    assert parsed.tax_amount == Decimal("0.88")
    assert parsed.currency == "USD"
    assert parsed.payment_method == "VISA"
    assert len(parsed.line_items) == 3
    assert parsed.line_items[0].description == "Organic Bananas 1kg"
    assert parsed.line_items[0].total_price == Decimal("3.50")
    assert parsed.overall_confidence > 0.8


def test_ocr_fallback_provider_graceful():
    provider = FallbackOCRProvider()
    result = provider.extract_text("nonexistent.jpg")
    assert result == ""
