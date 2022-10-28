from datetime import date
import this
from odoo import api, fields, models, _
from openerp.tools.translate import _
from openerp.exceptions import UserError

class Sales_Data(models.Model):


    _inherit='sale.order'
    building=fields.Many2one(comodel_name='property.building', string='Building')
    project=fields.Many2one(comodel_name='project.project', string='Project')
    floor=fields.Many2one(comodel_name='property.floor', string='Floor')
    unit=fields.Many2one(comodel_name='product.product', string='Unit')

    @api.onchange('unit')
    def onchange_unit(self):
        rec =self.env['product.product'].search([('id','=',self.unit.id)])
        if rec:
             self.building = rec.building
             self.floor=rec.floor_id
             self.project=rec.project



class inv_Data(models.Model):


    _inherit='account.move'
    building=fields.Many2one(comodel_name='property.building', string='Building')
    project=fields.Many2one(comodel_name='project.project', string='Project')
    floor=fields.Many2one(comodel_name='property.floor', string='Floor')
    unit=fields.Many2one(comodel_name='product.product', string='Unit')

class transfer_Data(models.Model):


    _inherit='stock.picking'
    building=fields.Many2one(comodel_name='property.building', string='Building')
    project=fields.Many2one(comodel_name='project.project', string='Project')
    floor=fields.Many2one(comodel_name='property.floor', string='Floor')
    unit=fields.Many2one(comodel_name='product.product', string='Unit')

class prodvar_Data(models.Model):


    _inherit='product.product'
    project=fields.Many2one(comodel_name='project.project', string='Project')
    