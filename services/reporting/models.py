"""
Reporting Service Database Models
Report tracking and templates
"""
from sqlalchemy import Column, String, Integer, Enum as SQLEnum, Text, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.database import Base, TimestampMixin


class ReportType(str, enum.Enum):
    """Report type enumeration"""
    SALES_SUMMARY = "sales_summary"
    INVENTORY_STATUS = "inventory_status"
    TVA_MONTHLY = "tva_monthly"
    TRIAL_BALANCE = "trial_balance"
    DASHBOARD = "dashboard"
    STOCK_MOVEMENTS = "stock_movements"
    CUSTOMER_SALES = "customer_sales"
    CUSTOM = "custom"


class ReportFormat(str, enum.Enum):
    """Report output format"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class ReportStatus(str, enum.Enum):
    """Report generation status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(Base, TimestampMixin):
    """
    Generated reports tracking
    Stores metadata about generated reports and their locations
    """
    __tablename__ = 'reports'

    __table_args__ = (
        Index('idx_report_type', 'report_type'),
        Index('idx_report_status', 'status'),
        Index('idx_report_date', 'report_date'),
        Index('idx_user_report', 'user_id', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_type = Column(SQLEnum(ReportType), nullable=False, index=True)
    report_format = Column(SQLEnum(ReportFormat), nullable=False, index=True)
    status = Column(SQLEnum(ReportStatus), nullable=False, default=ReportStatus.PENDING)

    # Report metadata
    title = Column(String(255), nullable=False)
    description = Column(String(500))
    report_date = Column(String(10))  # YYYY-MM-DD format (date the report covers)

    # Filters used to generate the report
    filters = Column(Text)  # JSON string of filters applied

    # File storage
    file_path = Column(String(500))  # Path in MinIO/S3
    file_size = Column(Integer)  # File size in bytes
    file_name = Column(String(255))  # Original filename

    # Generation details
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    generation_time_ms = Column(Integer)  # Time taken to generate in milliseconds
    error_message = Column(Text)  # Error message if failed

    # Template used (optional)
    template_id = Column(UUID(as_uuid=True), index=True)

    # Expiration (optional)
    expires_at = Column(String(19))  # YYYY-MM-DD HH:MM:SS format


class ReportTemplate(Base, TimestampMixin):
    """
    Report templates for reusable report configurations
    """
    __tablename__ = 'report_templates'

    __table_args__ = (
        Index('idx_template_type', 'report_type'),
        Index('idx_template_active', 'is_active'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))

    report_type = Column(SQLEnum(ReportType), nullable=False, index=True)
    report_format = Column(SQLEnum(ReportFormat), nullable=False)

    # Template configuration
    template_config = Column(Text)  # JSON string with template settings
    default_filters = Column(Text)  # JSON string with default filters

    # HTML template for PDF generation (if format is PDF)
    html_template = Column(Text)

    # Column configuration for Excel (if format is Excel)
    excel_config = Column(Text)  # JSON string with column definitions, styles, etc.

    # Access control
    is_active = Column(Integer, default=1)
    is_public = Column(Integer, default=0)  # Whether all users can access
    created_by_user_id = Column(UUID(as_uuid=True))
