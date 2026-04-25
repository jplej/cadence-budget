from decimal import Decimal
from datetime import date
from typing import Optional

from ninja import Schema


class PartnerIn(Schema):
    name: str
    is_internal: bool = False


class PartnerPatchIn(Schema):
    name: Optional[str] = None
    is_internal: Optional[bool] = None


class PartnerOut(Schema):
    id: int
    name: str
    is_internal: bool


class CategoryIn(Schema):
    name: str


class CategoryPatchIn(Schema):
    name: Optional[str] = None


class CategoryOut(Schema):
    id: int
    name: str


class ProjectIn(Schema):
    name: str
    year: int


class ProjectPatchIn(Schema):
    name: Optional[str] = None
    year: Optional[int] = None


class ProjectOut(Schema):
    id: int
    name: str
    year: int


class ProjectTagIn(Schema):
    tag: str  # user writes "type/spectacle"


class ProjectTagOut(Schema):
    id: int
    tag: str  # returned as "type/spectacle"


class ProjectParticipationIn(Schema):
    partner_id: int
    share_percent: Decimal


class ProjectParticipationPatchIn(Schema):
    share_percent: Optional[Decimal] = None


class ProjectParticipationOut(Schema):
    id: int
    partner_id: int
    share_percent: Decimal


class BudgetLineIn(Schema):
    category_id: int
    forecast_amount: Optional[Decimal] = None
    forecast_date: Optional[date] = None
    realized_amount: Optional[Decimal] = None
    realized_date: Optional[date] = None
    comment: str = ""


class BudgetLinePatchIn(Schema):
    category_id: Optional[int] = None
    forecast_amount: Optional[Decimal] = None
    forecast_date: Optional[date] = None
    realized_amount: Optional[Decimal] = None
    realized_date: Optional[date] = None
    comment: Optional[str] = None


class BudgetLineOut(Schema):
    id: int
    project_id: int
    category_id: int
    forecast_amount: Optional[Decimal]
    forecast_date: Optional[date]
    realized_amount: Optional[Decimal]
    realized_date: Optional[date]
    comment: str


class LineParticipationIn(Schema):
    partner_id: int
    share_percent: Decimal


class LineParticipationPatchIn(Schema):
    share_percent: Optional[Decimal] = None


class LineParticipationOut(Schema):
    id: int
    partner_id: int
    share_percent: Decimal


class WaterfallTrancheIn(Schema):
    priority: int
    rule_type: str  # "RECOUPMENT" | "RESIDUAL"
    description: str = ""


class WaterfallTranchePatchIn(Schema):
    priority: Optional[int] = None
    rule_type: Optional[str] = None
    description: Optional[str] = None


class WaterfallTrancheOut(Schema):
    id: int
    project_id: int
    priority: int
    rule_type: str
    description: str


class TrancheClaimIn(Schema):
    partner_id: int
    share_percent: Decimal
    recoup_target: Optional[str] = None  # "FIXED" | "EXPENSE_SUM" | None
    recoup_amount: Optional[Decimal] = None


class TrancheClaimPatchIn(Schema):
    share_percent: Optional[Decimal] = None
    recoup_target: Optional[str] = None
    recoup_amount: Optional[Decimal] = None


class TrancheClaimOut(Schema):
    id: int
    partner_id: int
    share_percent: Decimal
    recoup_target: Optional[str]
    recoup_amount: Optional[Decimal]
