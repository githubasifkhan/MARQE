import datetime
from re import U

from odoo import models, fields,api
from odoo.exceptions import UserError
import base64
import requests
import datetime

# class OLStartDate(models.Model):
#     _inherit = 'contract.order'

#     def change_start_date(self,context):
#         active_ids = self.env.context.get('active_ids')
#         return {
#             'name': _('Change Order Start Date'),
#             'view_mode': 'form',
#             'res_model': 'contract.order.change.start.date',
#             'view_id': False,
#             'type': 'ir.actions.act_window',
#             'context': {
#                 'contract_id': self.id,
#             },
#             'target': 'new'
#         }
    
