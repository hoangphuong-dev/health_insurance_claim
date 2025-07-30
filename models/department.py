from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HRDepartment(models.Model):
    """Extend hr.department để thêm BHYT và HIS fields"""
    _inherit = 'hr.department'
    
    # Phân loại nguồn
    department_source = fields.Selection([
        ('bhyt', 'Khoa BHYT'),
        ('his', 'Khoa HIS'),
    ], string='Loại khoa', default='his', tracking=True, index=True)
    
    # BHYT specific fields  
    bhyt_code = fields.Char('Mã khoa BHYT', index=True, tracking=True, size=10)
    bhyt_name = fields.Char('Tên khoa BHYT', tracking=True)
    
    # HIS specific fields
    his_code = fields.Char('Mã HIS', index=True, readonly=True, size=10)
    
    # Mapping relationship - Many2many cho phép 1 BHYT map nhiều HIS
    his_department_ids = fields.Many2many(
        'hr.department',
        'bhyt_his_department_mapping',
        'bhyt_department_id',
        'his_department_id', 
        string='Khoa HIS được ánh xạ',
        domain="[('department_source', '=', 'his')]"
    )
    bhyt_department_ids = fields.Many2many(
        'hr.department',
        'bhyt_his_department_mapping',
        'his_department_id',
        'bhyt_department_id',
        string='Khoa BHYT tương ứng',
        domain="[('department_source', '=', 'bhyt')]"
    )
    
    mapped_count = fields.Integer(
        'Số lượng ánh xạ',
        compute='_compute_mapped_count',
        store=True
    )
    
    _sql_constraints = [
        ('bhyt_code_uniq', 'unique(bhyt_code)', 
         'Mã khoa BHYT phải duy nhất!'),
        ('his_code_uniq', 'unique(his_code)', 
         'Mã khoa HIS phải duy nhất!'),
    ]
    
    @api.depends('his_department_ids', 'bhyt_department_ids', 'department_source')
    def _compute_mapped_count(self):
        for record in self:
            if record.department_source == 'bhyt':
                record.mapped_count = len(record.his_department_ids)
            elif record.department_source == 'his':
                record.mapped_count = len(record.bhyt_department_ids)
            else:
                record.mapped_count = 0
    
    def name_get(self):
        """Custom display name với icon"""
        result = []
        for record in self:
            if record.department_source == 'bhyt' and record.bhyt_code:
                name = f"🏥 [{record.bhyt_code}] {record.bhyt_name or record.name}"
            elif record.department_source == 'his' and record.his_code:
                name = f"💻 [HIS-{record.his_code}] {record.name}"
            else:
                name = record.name
            result.append((record.id, name))
        return result
    
    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        """Enhanced search"""
        if name:
            domain = domain or []
            domain = [
                '|', '|', '|',
                ('bhyt_code', operator, name),
                ('bhyt_name', operator, name), 
                ('his_code', operator, name),
                ('name', operator, name)
            ] + domain
        return self._search(domain, limit=limit, order=order)
    
    @api.onchange('bhyt_name')
    def _onchange_bhyt_name(self):
        """Auto-fill name from bhyt_name"""
        if self.bhyt_name and self.department_source == 'bhyt':
            self.name = self.bhyt_name
    
    @api.model
    def action_sync_from_his(self):
        """Đồng bộ khoa từ HIS với notification toast"""
        # Demo data - thực tế call API HIS
        his_departments = [
            {'his_code': 'K01', 'name': 'Khoa Nội tổng hợp'},
            {'his_code': 'K02', 'name': 'Khoa Ngoại tổng hợp'},
            {'his_code': 'K03', 'name': 'Khoa Sản'},
            {'his_code': 'K04', 'name': 'Khoa Nhi'},
            {'his_code': 'K05', 'name': 'Khoa Cấp cứu'},
            {'his_code': 'K06', 'name': 'Khoa Chẩn đoán hình ảnh'},
            {'his_code': 'K07', 'name': 'Khoa Xét nghiệm'},
        ]
        
        created_count = 0
        updated_count = 0
        
        for dept_data in his_departments:
            existing = self.search([
                ('his_code', '=', dept_data['his_code']),
                ('department_source', '=', 'his')
            ], limit=1)
            
            dept_data.update({
                'department_source': 'his',
                'patient_department': True,
            })
            
            if not existing:
                self.create(dept_data)
                created_count += 1
            else:
                existing.write({'name': dept_data['name']})
                updated_count += 1
        
        # Toast notification cho Odoo 18
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Đồng bộ thành công'),
                'message': _('Đã đồng bộ %(total)s khoa từ HIS (%(created)s mới, %(updated)s cập nhật)', 
                           total=len(his_departments), created=created_count, updated=updated_count),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_view_mappings(self):
        """Xem mapping với context menu"""
        self.ensure_one()
        
        if self.department_source == 'bhyt':
            domain = [('id', 'in', self.his_department_ids.ids)]
            title = _('Khoa HIS được ánh xạ cho [%(code)s] %(name)s', 
                     code=self.bhyt_code, name=self.bhyt_name)
        elif self.department_source == 'his':
            domain = [('id', 'in', self.bhyt_department_ids.ids)]
            title = _('Khoa BHYT tương ứng với [HIS-%(code)s] %(name)s', 
                     code=self.his_code, name=self.name)
        else:
            return
            
        return {
            'type': 'ir.actions.act_window',
            'name': title,
            'res_model': 'hr.department',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'create': False, 
                'edit': False,
                'search_default_active': 1
            },
        }