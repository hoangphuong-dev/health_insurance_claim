from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MedicalStaff(models.Model):
    _inherit = "hr.employee"
    _description = "Medical Staff"
    _order = "name asc"

    # Mã code từ his
    his_code = fields.Char(string="HIS Code", required=True)

    # Mã bảo hiểm xã hội
    bhyt_code = fields.Char(
        size=10,
        help="Enter the Social Insurance number of the medical staff",
    )

    # Mã chứng chỉ hành nghề
    bhyt_certificate_code = fields.Char(
        help="Enter the code number on the Practice Certificate of the staff",
    )

    bhyt_certificate_date = fields.Date(
        help="Select the issue date of the Practice Certificate.",
    )

    bhyt_certificate_place = fields.Char(
        help="Enter the name of the authority",
    )

    # Chức danh
    bhyt_title_id = fields.Many2one(
        "hic.category",
        domain=[("category_type", "=", "professional_title")],
        help="Enter the professional title of the staff",
    )

    # Mã loại Khám chữa bệnh
    bhyt_service_id = fields.Many2one(
        "hic.category",
        domain=[("category_type", "=", "medical_service_code")],
        help="Select the Medical Service Code from the available list",
    )

    @api.constrains("bhyt_code")
    def _check_bhyt_code(self):
        """Validate social insurance code format"""
        for record in self:
            if record.bhyt_code:
                if len(record.bhyt_code) != 10:
                    raise ValidationError(
                        _("BHYT Code must be exactly 10 characters long.")
                    )
                if not record.bhyt_code.isdigit():
                    raise ValidationError(_("BHYT Code must contain only numbers."))

    @api.constrains("bhyt_certificate_date")
    def _check_certificate_date(self):
        """Validate certificate issue date"""
        for record in self:
            if record.bhyt_certificate_date:
                if record.bhyt_certificate_date > date.today():
                    raise ValidationError(
                        _("Certificate issue date cannot be in the future.")
                    )

    _sql_constraints = [
        (
            "social_insurance_code_unique",
            "UNIQUE(bhyt_code)",
            "BHYT Code must be unique!",
        ),
        (
            "certificate_code_unique",
            "UNIQUE(bhyt_certificate_code)",
            "Practice Certificate Code must be unique!",
        ),
        (
            "his_code_unique",
            "UNIQUE(his_code)",
            "HIS Code must be unique!",
        ),
    ]
