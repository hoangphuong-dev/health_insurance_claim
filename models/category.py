import re

import regex

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CommonCategory(models.Model):
    _name = "hic.category"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Common Category"
    _order = "category_type, code asc"
    _rec_name = "name"

    # Basic information
    code = fields.Char(
        required=True,
        index=True,
        tracking=True,
        help="Unique identifier code for the category",
    )
    name = fields.Char(
        required=True,
        tracking=True,
        translate=True,
        help="Display name of the category",
    )
    description = fields.Text(
        translate=True,
        help="Detailed description of the category",
    )
    benefit_code = fields.Many2one(
        "hic.benefit.code",
        tracking=True,
    )

    # Category type
    category_type = fields.Selection(
        [
            ("technical_level", _("Technical Level")),
            ("professional_title", _("Professional Title")),
            ("medical_service_code", _("Medical Service Code")),
            ("bhyt_object_code", _("BHYT Object Code")),
            ("kcb_object_code", _("KCB Object Code")),
            ("discharge_type_code", _("Discharge Type Code")),
            ("accident_code", _("Accident Code")),
        ],
        required=True,
        help="Category classification type",
    )
    active = fields.Boolean(default=True)

    @api.constrains("code", "category_type")
    def _check_code_format(self):
        """Validate code format based on category type"""
        for record in self:
            if record.code and record.category_type:
                # Chỉ validate số cho professional_title và medical_service_code
                if record.category_type in [
                    "professional_title",
                    "medical_service_code",
                ]:
                    if not record.code.isdigit():
                        raise ValidationError(
                            _("Code must contain only numbers for this category type!")
                        )
                    # Kiểm tra độ dài phải đúng 2 chữ số
                    if len(record.code) > 2:
                        raise ValidationError(
                            _("The code length is only up to 2 digits!")
                        )

    @api.onchange("code", "category_type")
    def _onchange_code(self):
        """Remove non-numeric characters from code on input for specific types"""
        if self.code and self.category_type:
            # Chỉ validate số cho professional_title và medical_service_code
            if self.category_type in ["professional_title", "medical_service_code"]:
                # Chỉ giữ lại các ký tự số
                numeric_only = re.sub(r"\D", "", self.code)

                # Giới hạn chỉ 2 chữ số đầu tiên
                if len(numeric_only) > 2:
                    numeric_only = numeric_only[:2]

                if numeric_only != self.code:
                    self.code = numeric_only
                    if len(self.code) > 2:
                        message = _("Keep only the first 2 digits")
                    else:
                        message = _("Keep only the digits")

                    return {
                        "warning": {
                            "title": _("Invalid Characters Removed"),
                            "message": message,
                        }
                    }

    def name_get(self):
        """Custom display name with code"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result

    @api.constrains("code", "category_type")
    def _check_category_code(self):
        """Check category code validation based on type"""
        for record in self:
            if not (record.code and record.category_type):
                continue

            # Validate code format based on category type
            self._validate_code_format(record)

            # Check for duplicates
            self._check_code_duplicate(record)

    def _validate_code_format(self, record):
        """Validate code format based on category type"""
        if record.category_type == "bhyt_object_code":
            self._check_bhyt_object_code(record)
        elif record.category_type == "kcb_object_code":
            self._check_kcb_object_code(record)
        elif record.category_type in ("discharge_type_code", "accident_code"):
            self._check_numeric_code(record)

    def _check_length(self, code, max_length, error_message):
        """Check if code length is within limit"""
        if len(code) > max_length:
            raise ValidationError(_(error_message))

    def _check_text_pattern(self, code, pattern, error_message):
        """Check if code matches the specified pattern"""
        if not regex.match(pattern, code, regex.I):
            raise ValidationError(_(error_message))

    def _check_numeric_only(self, code, category_name):
        """Check if code contains only digits"""
        if not code.isdigit():
            raise ValidationError(_("%(name)s must be a number!", name=category_name))

    def _check_numeric_range(self, code, min_val, max_val, category_name):
        """Check if numeric code is within specified range"""
        code_int = int(code)
        if not (min_val <= code_int <= max_val):
            raise ValidationError(
                _(
                    "%(name)s must be between %(min)s and %(max)s!",
                    name=category_name,
                    min=min_val,
                    max=max_val,
                )
            )

    def _get_category_name(self, record):
        """Get translated category type name"""
        return _(
            dict(record._fields["category_type"].selection).get(record.category_type)
        )

    def _check_bhyt_object_code(self, record):
        """Validate BHYT object code format"""
        error_msg = (
            "BHYT object code must not exceed 2 characters and "
            "must not contain numbers or special characters!"
        )
        self._check_length(record.code, 2, error_msg)
        # Only letters and spaces allowed
        self._check_text_pattern(record.code, r"^[\p{L}\s]*$", error_msg)

    def _check_kcb_object_code(self, record):
        """Validate KCB object code format"""
        error_msg = (
            "KCB object code must not exceed 4 characters and "
            "must contain only numbers and special characters "
            "(no letters and number '0')!"
        )
        self._check_length(record.code, 4, error_msg)
        # Only numbers and special characters allowed (no letters)
        self._check_text_pattern(record.code, r"^[\d\s\-_\.\(\)\[\]]*$", error_msg)
        if record.code.strip() == "0":
            raise ValidationError(_(error_msg))

    def _check_numeric_code(self, record):
        """Validate numeric codes (discharge_type_code, accident_code)"""
        category_name = self._get_category_name(record)
        self._check_numeric_only(record.code, category_name)
        self._check_numeric_range(record.code, 1, 99, category_name)

    def _check_code_duplicate(self, record):
        """Check for duplicate codes"""
        existing = self.search(
            [
                ("category_type", "=", record.category_type),
                ("code", "=", record.code),
                ("id", "!=", record.id),
            ],
            limit=1,
        )

        if existing:
            category_name = self._get_category_name(record)
            raise ValidationError(
                _(
                    "%(name)s with the code %(code)s already exists. "
                    "Please check again.",
                    name=category_name,
                    code=record.code,
                )
            )

    @api.model
    def create(self, vals):
        """Override create to customize log message based on category type"""
        record = super().create(vals)
        # Custom log message based on category type
        if record.category_type:
            category_name = self._get_category_name(record)
            # Store all existing messages before creating custom one
            existing_messages = record.message_ids
            # Remove all previous messages (including default tracking messages)
            if existing_messages:
                existing_messages.unlink()
            # Create custom message
            record.message_post(
                body=_("%(name)s has been created.", name=category_name),
                message_type="notification",
            )
        return record
