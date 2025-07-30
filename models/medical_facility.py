from odoo import api, fields, models


class MedicalFacility(models.Model):
    _name = "hic.medical.facility"
    _description = "Medical Facility"
    _order = "code asc"
    _rec_name = "name"

    # Basic information
    code = fields.Char(required=True, help="Medical facility identification code")
    name = fields.Char(required=True, help="Full name of the medical facility")

    # Constraints
    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "Medical facility code must be unique!"),
    ]

    def name_get(self):
        """Custom display name"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Custom search by code or name"""
        args = args or []
        if name:
            args = ["|", ("code", operator, name), ("name", operator, name)] + args
        return self.search(args, limit=limit).name_get()
