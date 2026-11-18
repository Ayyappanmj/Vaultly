from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class ReportExportRequest(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    format: str = "csv"  # csv or pdf


class ReportExportResponse(BaseModel):
    report_url: str
    record_count: int
    total_spent: Decimal
    currency: str = "USD"
