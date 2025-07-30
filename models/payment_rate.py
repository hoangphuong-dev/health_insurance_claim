from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PaymentRate(models.Model):
    _name = "hic.payment.rate"
    _description = "Payment Rate"
    _order = "code asc"
    _rec_name = "code"

    # Basic information
    code = fields.Char(required=True, help="payment rate identification code")

    # Relations with other tables
    medical_facility_id = fields.Many2one(
        "hic.medical.facility",
        string="Hospital",
        required=True,
        help="Select hospital from medical facility directory",
    )

    technical_level_id = fields.Many2one(
        "hic.category",
        string="Technical Level",
        required=True,
        domain=[("category_type", "=", "technical_level")],
        help="Select technical level",
    )

    # Payment rates
    outpatient_rate = fields.Float(
        string="Outpatient Rate (%)",
        digits=(5, 2),
        help="Percentage for outpatient services (0-100%)",
    )

    inpatient_rate = fields.Float(
        string="Inpatient Rate (%)",
        digits=(5, 2),
        help="Percentage for inpatient services (0-100%)",
    )

    # Validity period
    date_from = fields.Date(
        string="From Date",
        required=True,
        default=fields.Date.context_today,
        help="Start date of validity",
    )

    date_to = fields.Date(
        string="To Date", help="End date of validity (leave empty for unlimited)"
    )

    # Constraints
    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "Payment rate code must be unique!"),
        (
            "outpatient_rate_check",
            "CHECK(outpatient_rate >= 0 AND outpatient_rate <= 100)",
            "Outpatient rate must be between 0% and 100%!",
        ),
        (
            "inpatient_rate_check",
            "CHECK(inpatient_rate >= 0 AND inpatient_rate <= 100)",
            "Inpatient rate must be between 0% and 100%!",
        ),
    ]

    @api.constrains("date_from", "date_to")
    def _check_date_validity(self):
        """Check date validity"""
        for record in self:
            if record.date_to and record.date_from > record.date_to:
                raise ValidationError(_("End date must be after start date!"))

    @api.constrains("medical_facility_id", "technical_level_id", "date_from", "date_to")
    def _check_overlapping_periods(self):
        """Check for no overlapping periods for same hospital and technical level"""
        for record in self:
            domain = [
                ("id", "!=", record.id),
                ("medical_facility_id", "=", record.medical_facility_id.id),
                ("technical_level_id", "=", record.technical_level_id.id),
            ]

            # Check overlap
            if record.date_to:
                domain.extend(
                    [
                        "|",
                        "&",
                        ("date_from", "<=", record.date_from),
                        ("date_to", ">=", record.date_from),
                        "&",
                        ("date_from", "<=", record.date_to),
                        ("date_to", ">=", record.date_to),
                    ]
                )
            else:
                domain.extend(
                    [
                        "|",
                        ("date_to", "=", False),
                        ("date_to", ">=", record.date_from),
                    ]
                )

            overlapping = self.search(domain)
            if overlapping:
                hospital_name = record.medical_facility_id.name
                tech_level_name = record.technical_level_id.name
                raise ValidationError(
                    _(
                        'Payment rate already exists for hospital "%(hospital)s" '
                        'and technical level "%(tech_level)s" in this time period!'
                    )
                    % {
                        "hospital": hospital_name,
                        "tech_level": tech_level_name,
                    }
                )

    def name_get(self):
        """Custom display name"""
        result = []
        for record in self:
            hospital_name = record.medical_facility_id.name
            tech_level_name = record.technical_level_id.name
            name = f"[{record.code}] {hospital_name} - {tech_level_name}"
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Custom search by code, hospital name or technical level"""
        args = args or []
        if name:
            args = [
                "|",
                "|",
                "|",
                ("code", operator, name),
                ("medical_facility_id.name", operator, name),
                ("medical_facility_id.code", operator, name),
                ("technical_level_id.name", operator, name),
            ] + args
        return self.search(args, limit=limit).name_get()
