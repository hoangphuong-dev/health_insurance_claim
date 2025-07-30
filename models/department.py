from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HRDepartment(models.Model):
    """Extend hr.department để thêm BHYT và HIS fields"""

    _inherit = "hr.department"

    # Phân loại nguồn
    department_source = fields.Selection(
        [
            ("bhyt", "BHYT Department"),
            ("his", "HIS Department"),
        ],
        string="Department Type",
        default="his",
        tracking=True,
        index=True,
    )

    # BHYT specific fields
    bhyt_code = fields.Char("BHYT Code", index=True, tracking=True, size=10)
    bhyt_name = fields.Char("BHYT Name", tracking=True, translate=True)

    # HIS specific fields
    his_code = fields.Char("HIS Code", index=True, readonly=True, size=10)

    # Mapping relationship - Many2many cho phép 1 BHYT map nhiều HIS
    his_department_ids = fields.Many2many(
        "hr.department",
        "bhyt_his_department_mapping",
        "bhyt_department_id",
        "his_department_id",
        string="Corresponding HIS Departments",
        domain="[('department_source', '=', 'his')]",
    )

    _sql_constraints = [
        ("bhyt_code_uniq", "unique(bhyt_code)", "BHYT department code must be unique!"),
        ("his_code_uniq", "unique(his_code)", "HIS department code must be unique!"),
    ]

    @api.model
    def create(self, vals):
        """Override create method để xử lý khi tạo khoa BHYT mới"""
        if vals.get("department_source") == "bhyt":
            # Validate mã BHYT không trùng
            if vals.get("bhyt_code"):
                existing = self.search(
                    [
                        ("bhyt_code", "=", vals["bhyt_code"]),
                        ("department_source", "=", "bhyt"),
                    ]
                )
                if existing:
                    raise ValidationError(
                        _("BHYT department code '%s' already exists!")
                        % vals["bhyt_code"]
                    )

            # Set default values cho khoa BHYT
            vals.update(
                {
                    "patient_department": True,
                    "bhyt_name": vals.get("name") or vals.get("bhyt_name"),
                }
            )

        return super().create(vals)

    @api.model
    def default_get(self, fields_list):
        """Set default values khi tạo mới"""
        defaults = super().default_get(fields_list)

        # Kiểm tra context để xác định tạo khoa BHYT
        if self.env.context.get("create_bhyt_department"):
            defaults.update(
                {
                    "department_source": "bhyt",
                    "patient_department": True,
                }
            )

        return defaults

    def name_get(self):
        """Custom display name với icon"""
        result = []
        for record in self:
            if record.department_source == "bhyt" and record.bhyt_code:
                name = f"🏥 [{record.bhyt_code}] {record.bhyt_name or record.name}"
            elif record.department_source == "his" and record.his_code:
                name = f"💻 [HIS-{record.his_code}] {record.name}"
            else:
                name = record.name
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        """Enhanced search"""
        if name:
            domain = domain or []
            domain = [
                "|",
                "|",
                "|",
                ("bhyt_code", operator, name),
                ("bhyt_name", operator, name),
                ("his_code", operator, name),
                ("name", operator, name),
            ] + domain
        return self._search(domain, limit=limit, order=order)

    @api.onchange("bhyt_name")
    def _onchange_bhyt_name(self):
        """Auto-fill name from bhyt_name"""
        if self.bhyt_name and self.department_source == "bhyt":
            self.name = self.bhyt_name
