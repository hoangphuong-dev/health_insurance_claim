from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DepartmentWizard(models.TransientModel):
    """Wizard tạo khoa BHYT mới"""
    _name = 'hic.department.wizard'
    _description = 'Create BHYT Department Wizard'
    
    bhyt_code = fields.Char(
        'Mã khoa BHYT', 
        required=True, 
        size=10,
        help="Mã khoa theo quy định BHYT"
    )
    bhyt_name = fields.Char(
        'Tên khoa BHYT', 
        required=True,
        help="Tên đầy đủ của khoa phòng"
    )
    his_department_ids = fields.Many2many(
        'hr.department',
        string='Khoa HIS tương ứng',
        domain="[('department_source', '=', 'his')]",
        help='Chọn một hoặc nhiều khoa HIS để ánh xạ với khoa BHYT này'
    )
    description = fields.Text('Ghi chú')
    
    @api.constrains('bhyt_code')
    def _check_bhyt_code(self):
        """Validate mã BHYT với message clear"""
        for record in self:
            if record.bhyt_code:
                existing = self.env['hr.department'].search([
                    ('bhyt_code', '=', record.bhyt_code),
                    ('department_source', '=', 'bhyt')
                ])
                if existing:
                    raise ValidationError(
                        _("Mã khoa BHYT '%(code)s' đã tồn tại!\nVui lòng sử dụng mã khác.", 
                          code=record.bhyt_code)
                    )
    
    def action_create_department(self):
        """Tạo khoa BHYT mới với enhanced notification"""
        self.ensure_one()
        
        # Tạo khoa BHYT
        department_vals = {
            'name': self.bhyt_name,
            'bhyt_code': self.bhyt_code,
            'bhyt_name': self.bhyt_name,
            'department_source': 'bhyt',
            'patient_department': True,
            'his_department_ids': [(6, 0, self.his_department_ids.ids)],
        }
        
        new_department = self.env['hr.department'].create(department_vals)
        
        # Enhanced notification
        message = _("Đã tạo khoa BHYT [%(code)s] %(name)s", 
                   code=self.bhyt_code, name=self.bhyt_name)
        if self.his_department_ids:
            his_names = ', '.join(self.his_department_ids.mapped('name'))
            message += _("\nĐã ánh xạ với %(count)s khoa HIS: %(names)s", 
                        count=len(self.his_department_ids), names=his_names)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Tạo thành công'),
                'message': message,
                'type': 'success',
                'sticky': False,
            },
            'context': {'department_created': new_department.id}
        }