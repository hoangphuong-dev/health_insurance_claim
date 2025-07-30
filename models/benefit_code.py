from odoo import fields, models


class HicBenefitCode(models.Model):
    _name = "hic.benefit.code"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Health Insurance Benefit Code"
    _order = "benefit_code"
    _rec_name = "benefit_code"

    benefit_code = fields.Integer(
        required=True,
        copy=False,
        tracking=True,
    )
    benefit_rate = fields.Integer(
        string="Benefit Rate (%)",
        required=True,
        tracking=True,
        help="Percentage of coverage for this benefit code",
    )
    is_payment_condition_applied = fields.Boolean(
        default=False,
        tracking=True,
    )
    is_transport_cost_covered = fields.Boolean(
        string="Transportation Cost Covered", default=False, tracking=True
    )
    is_non_bhyt_cost_paid = fields.Boolean(
        string="Out of Scope BHYT Costs Covered", default=False, tracking=True
    )
    active = fields.Boolean(default=True, tracking=True)

    _sql_constraints = [
        ("benefit_code_uniq", "unique(benefit_code)", "Benefit code must be unique!"),
        (
            "benefit_code_check",
            "check(benefit_code >= 1)",
            "Benefit code must be greater than 0!",
        ),
        (
            "benefit_rate_check",
            "check(benefit_rate >= 1 and benefit_rate <= 100)",
            "Benefit rate must be between 1 and 100!",
        ),
    ]

    def name_get(self):
        """Display name with benefit code and rate"""
        result = []
        for record in self:
            name = f"{record.benefit_code} - {record.benefit_rate}%"
            result.append((record.id, name))
        return result
