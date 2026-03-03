"""SQLite database initialization and connection management."""
import sqlite3
from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS edi_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    isa_sender_id TEXT,
    isa_receiver_id TEXT,
    isa_date TEXT,
    isa_control_number TEXT,
    gs_functional_id TEXT,
    gs_sender_code TEXT,
    gs_receiver_code TEXT,
    gs_date TEXT,
    gs_control_number TEXT,
    bpr_transaction_type TEXT,
    bpr_amount REAL,
    bpr_credit_debit TEXT,
    bpr_payment_method TEXT,
    bpr_payment_date TEXT,
    trn_reference TEXT,
    trn_originator TEXT,
    payer_name TEXT,
    payer_id TEXT,
    payee_name TEXT,
    payee_id TEXT,
    payee_npi TEXT,
    contact_name TEXT,
    contact_phone TEXT,
    contact_email TEXT,
    source_type TEXT DEFAULT 'edi',
    pdf_parsing_notes TEXT
);

CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    clp_claim_id TEXT,
    clp_status_code TEXT,
    clp_total_charge REAL,
    clp_total_payment REAL,
    clp_plan_code TEXT,
    clp_filing_indicator TEXT,
    clp_drg_code TEXT,
    clp_drg_weight REAL,
    clp_facility_type TEXT,
    patient_name TEXT,
    patient_id TEXT,
    patient_first_name TEXT,
    patient_last_name TEXT,
    rendering_provider_name TEXT,
    rendering_provider_id TEXT,
    crossover_payer_name TEXT,
    crossover_payer_id TEXT,
    claim_date_start TEXT,
    claim_date_end TEXT,
    claim_received_date TEXT,
    total_adjustments REAL DEFAULT 0,
    FOREIGN KEY (file_id) REFERENCES edi_files(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS claim_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    group_code TEXT,
    reason_code TEXT,
    amount REAL,
    quantity REAL,
    FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS service_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    procedure_code TEXT,
    procedure_modifiers TEXT,
    revenue_code TEXT,
    charge_amount REAL,
    payment_amount REAL,
    units REAL,
    date_start TEXT,
    date_end TEXT,
    control_number TEXT,
    rendering_provider_id TEXT,
    FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS service_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_line_id INTEGER NOT NULL,
    group_code TEXT,
    reason_code TEXT,
    amount REAL,
    quantity REAL,
    FOREIGN KEY (service_line_id) REFERENCES service_lines(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS provider_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    provider_id TEXT,
    fiscal_period_end TEXT,
    reason_code TEXT,
    amount REAL,
    FOREIGN KEY (file_id) REFERENCES edi_files(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS claim_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    flag_type TEXT NOT NULL DEFAULT 'review',
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_name TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    permissions TEXT DEFAULT 'read',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS claim_837_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER,
    expected_payment REAL,
    dx_codes TEXT,
    procedure_codes TEXT,
    FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_claims_file_id ON claims(file_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(clp_status_code);
CREATE INDEX IF NOT EXISTS idx_claim_adj_claim_id ON claim_adjustments(claim_id);
CREATE INDEX IF NOT EXISTS idx_svc_claim_id ON service_lines(claim_id);
CREATE INDEX IF NOT EXISTS idx_svc_adj_svc_id ON service_adjustments(service_line_id);
CREATE INDEX IF NOT EXISTS idx_prov_adj_file_id ON provider_adjustments(file_id);
CREATE INDEX IF NOT EXISTS idx_claims_date_start ON claims(claim_date_start);
CREATE INDEX IF NOT EXISTS idx_claims_patient ON claims(patient_name);
CREATE INDEX IF NOT EXISTS idx_claims_claim_id ON claims(clp_claim_id);
CREATE INDEX IF NOT EXISTS idx_svc_procedure ON service_lines(procedure_code);
CREATE INDEX IF NOT EXISTS idx_flags_claim_id ON claim_flags(claim_id);
"""


def _migrate(conn: sqlite3.Connection):
    """Add columns that may be missing from older databases."""
    # Check existing columns on edi_files
    cursor = conn.execute("PRAGMA table_info(edi_files)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    migrations = [
        ("edi_files", "source_type", "TEXT DEFAULT 'edi'"),
        ("edi_files", "pdf_parsing_notes", "TEXT"),
    ]

    for table, col, col_def in migrations:
        if col not in existing_cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")


def init_db():
    """Initialize the database with the schema."""
    conn = sqlite3.connect(settings.DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    _migrate(conn)
    # Insert default settings if not present
    conn.execute("""
        INSERT OR IGNORE INTO app_settings (key, value) VALUES ('underpayment_threshold', '70')
    """)
    conn.commit()
    conn.close()


def get_db() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
