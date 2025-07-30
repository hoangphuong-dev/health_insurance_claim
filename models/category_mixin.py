# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CategoryMixin(models.AbstractModel):
    """Base mixin cho mọi danh mục BHYT"""
    _name = 'hic.category.mixin'
    _description = 'HIC Category Mixin'
    
    code = fields.Char('Code', required=True, index=True, tracking=True)
    name = fields.Char('Name', required=True, index=True, tracking=True)
    description = fields.Text('Description')
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã phải duy nhất!'),
    ]
    
    def name_get(self):
        """Hiển thị [Mã] Tên"""
        return [(rec.id, f"[{rec.code}] {rec.name}") for rec in self]
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Tìm kiếm theo cả mã và tên"""
        if name:
            args = ['|', ('code', operator, name), ('name', operator, name)] + (args or [])
        return super().name_search(name='', args=args, operator=operator, limit=limit)