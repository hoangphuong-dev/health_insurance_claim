from odoo import models, fields, api
from datetime import datetime

class SyncMixin(models.AbstractModel):
    """Mixin cho danh mục đồng bộ từ HIS"""
    _name = 'hic.sync.mixin'
    _description = 'HIC Sync Mixin'
    
    his_ref = fields.Char('HIS Reference', help='ID/Code trong HIS system')
    
    @api.model
    def action_sync_from_his(self):
        """Template method - Override trong từng model"""
        raise NotImplementedError("Phải implement method action_sync_from_his")