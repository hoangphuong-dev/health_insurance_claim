from odoo import fields, models

HIC_HOSPITAL_BED = "hic.hospital.bed"


class HospitalBed(models.Model):
    """Hospital Bed Category / Danh mục Giường bệnh"""

    _name = HIC_HOSPITAL_BED
    _description = "Hospital Bed"
    _rec_name = "name"

    code = fields.Char(
        string="Bed Code",
        required=True,
        index=True,
        tracking=True,
        help="Unique code for the hospital bed",
    )
    name = fields.Char(
        string="Bed Name",
        required=True,
        tracking=True,
        help="Display name of the hospital bed",
    )

    # Type field để phân biệt BHYT/HIS
    bed_type = fields.Selection(
        [("bhyt", "BHYT Bed"), ("his", "HIS Bed")],
        string="Type",
        required=True,
        default="bhyt",
        tracking=True,
        help="Classification of bed type",
    )

    # Specific fields
    department_id = fields.Many2one(
        "hr.department",
        string="Department",
        domain=[("patient_department", "=", True)],
        help="Department where this bed is located",
    )

    price = fields.Float(tracking=True, help="Price per day for using this bed")

    # Mapping fields
    bhyt_bed_id = fields.Many2one(
        HIC_HOSPITAL_BED,
        string="Corresponding BHYT Bed",
        domain=[("bed_type", "=", "bhyt")],
        tracking=True,
        help="BHYT bed that this HIS bed maps to",
    )

    his_bed_ids = fields.One2many(
        HIC_HOSPITAL_BED,
        "bhyt_bed_id",
        string="Mapped HIS Beds",
        domain=[("bed_type", "=", "his")],
        help="HIS beds that are mapped to this BHYT bed",
    )

    _sql_constraints = [
        (
            "code_type_uniq",
            "unique(code, bed_type)",
            "Bed code must be unique within the same type (BHYT/HIS)!",
        ),
    ]
