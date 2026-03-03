"""Pydantic response models."""
from pydantic import BaseModel


class FileInfo(BaseModel):
    id: int
    filename: str
    uploaded_at: str
    payer_name: str | None = None
    payee_name: str | None = None
    bpr_amount: float | None = None
    bpr_payment_date: str | None = None
    claim_count: int = 0


class FileListResponse(BaseModel):
    files: list[FileInfo]


class AdjustmentInfo(BaseModel):
    id: int
    group_code: str
    group_description: str = ""
    reason_code: str
    reason_description: str = ""
    amount: float
    quantity: float


class ServiceLineInfo(BaseModel):
    id: int
    procedure_code: str | None = None
    procedure_modifiers: str | None = None
    revenue_code: str | None = None
    charge_amount: float
    payment_amount: float
    units: float
    date_start: str | None = None
    date_end: str | None = None
    control_number: str | None = None
    adjustments: list[AdjustmentInfo] = []


class ClaimSummary(BaseModel):
    id: int
    file_id: int
    filename: str = ""
    clp_claim_id: str
    clp_status_code: str
    status_description: str = ""
    clp_total_charge: float
    clp_total_payment: float
    patient_name: str | None = None
    rendering_provider_name: str | None = None
    claim_date_start: str | None = None
    service_line_count: int = 0


class ClaimDetail(BaseModel):
    id: int
    file_id: int
    filename: str = ""
    clp_claim_id: str
    clp_status_code: str
    status_description: str = ""
    clp_total_charge: float
    clp_total_payment: float
    clp_plan_code: str | None = None
    clp_filing_indicator: str | None = None
    clp_drg_code: str | None = None
    clp_drg_weight: float | None = None
    clp_facility_type: str | None = None
    patient_name: str | None = None
    patient_id: str | None = None
    patient_first_name: str | None = None
    patient_last_name: str | None = None
    rendering_provider_name: str | None = None
    rendering_provider_id: str | None = None
    crossover_payer_name: str | None = None
    crossover_payer_id: str | None = None
    claim_date_start: str | None = None
    claim_date_end: str | None = None
    claim_received_date: str | None = None
    total_adjustments: float = 0
    adjustments: list[AdjustmentInfo] = []
    service_lines: list[ServiceLineInfo] = []


class ClaimsListResponse(BaseModel):
    claims: list[ClaimSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class DashboardStats(BaseModel):
    total_payments: float = 0
    total_charges: float = 0
    total_adjustments: float = 0
    total_claims: int = 0
    claims_by_status: list[dict] = []
    top_denial_reasons: list[dict] = []
    top_adjustments: list[dict] = []
    file_count: int = 0


class CodeInfo(BaseModel):
    code: str
    description: str


class CodeSearchResponse(BaseModel):
    codes: list[CodeInfo]
    total: int


class MessageResponse(BaseModel):
    message: str
    id: int | None = None
