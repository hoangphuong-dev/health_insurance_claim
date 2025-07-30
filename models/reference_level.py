from datetime import date, datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ReferenceLevel(models.Model):
    _name = "hic.reference.level"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Reference Level"
    _order = "end_date desc"
    _rec_name = "reference_code"

    reference_code = fields.Char(
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )
    level_number = fields.Integer(
        string="Reference Level",
        required=True,
        help=(
            "Coefficient for the appraisal system to automatically determine "
            "and apply the 100% co-payment exemption benefit to eligible patients."
        ),
        tracking=True,
    )
    start_date = fields.Date(
        required=True,
        help="Start date for applying the reference level",
        tracking=True,
    )
    end_date = fields.Date(
        required=True,
        help="End date for applying the reference level",
        tracking=True,
    )
    check_edit = fields.Boolean()

    @api.constrains("level_number")
    def _check_level_number(self):
        for record in self:
            if record.level_number <= 0:
                raise ValidationError(_("Level number must be greater than 0!"))

    @api.constrains("start_date", "end_date")
    def _check_overlapping_dates(self):
        """Check that no overlapping time periods are allowed"""
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date >= record.end_date:
                    raise ValidationError(_("Start date must be less than end date!"))
                overlapping_records = self.search(
                    [
                        ("id", "!=", record.id),
                        "|",
                        "|",
                        "|",
                        # 1: New start < existing start AND new end >= existing start
                        "&",
                        ("start_date", ">=", record.start_date),
                        ("start_date", "<=", record.end_date),
                        # 2: New start <= existing end AND new end >= existing end
                        "&",
                        ("end_date", ">=", record.start_date),
                        ("end_date", "<=", record.end_date),
                        # 3: New period completely contains existing period
                        "&",
                        ("start_date", "<=", record.start_date),
                        ("end_date", ">=", record.end_date),
                        # 4: New period is completely within existing period
                        "&",
                        ("start_date", ">=", record.start_date),
                        ("end_date", "<=", record.end_date),
                    ],
                    limit=1,
                )

                if overlapping_records:
                    raise ValidationError(
                        _(
                            "The reference level time is overlapping with the "
                            "reference level %s. Please check again."
                        )
                        % overlapping_records.reference_code
                    )

    @api.model
    def create(self, vals):
        """Override create to generate reference code"""
        if vals.get("reference_code", _("New")) == _("New"):
            vals["reference_code"] = self.env["ir.sequence"].next_by_code(
                "hic.reference.level"
            ) or _("New")
        if (
            vals.get("start_date")
            and date.today() >= datetime.strptime(vals["start_date"], "%Y-%m-%d").date()
        ):
            vals["check_edit"] = True
        return super().create(vals)

    def write(self, vals):
        vals["check_edit"] = (
            True
            if vals.get("start_date")
            and date.today() >= datetime.strptime(vals["start_date"], "%Y-%m-%d").date()
            else False
        )
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.check_edit:
                raise ValidationError(
                    _(
                        "The reference level has been used for assessment and "
                        "the start date is in the past. Cannot be deleted."
                    )
                )
        return super().unlink()
