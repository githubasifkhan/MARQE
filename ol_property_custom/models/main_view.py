import datetime
from email.policy import default
from pyexpat import model
from re import U
from tokenize import String

from odoo import models, fields,api
from odoo.exceptions import UserError
import base64
import requests
import datetime

class ProjectProjectInherit(models.Model):
    _inherit='project.project'
    short_name = fields.Char(string='Short Name')
    code = fields.Char(string='Code',default="New")
    # parent_project = fields.Many2one(comodel_name='project.project', string='Parent Project')
    parent_project = fields.Many2one(
            comodel_name='project.project',
            relation='contents_found_rel',
            column1='lot_id',
            column2='content_id',
            string='Parent Project')
    def create_building(self):
        data={
        'name':self.name,
        'project_id':self.id,
        }
        self.env['property.building'].create(data)
    

    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code('project.task') or 'New'       
        result = super(ProjectProjectInherit, self).create(vals)       
        return result

class OLBuilding(models.Model):
    _name='property.building'
    name=fields.Char("Name")
    project_id=fields.Many2one("project.project","Project")
    short_name = fields.Char(string='Short Name')
    code = fields.Char(string='Code',default="New")
    number_of_floors=fields.Integer("Number Of Floors")
    floor_ids = fields.One2many('property.floor', 'building_id', string='Floor')
    project_analytical = fields.Many2one(related="project_id.analytic_account_id", string="Project Analytic Account")
    building_account_analytical = fields.Many2one('account.analytic.account', string="Building Account Analytical")

    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            buildings=self.env['property.building'].search([('project_id','=',self.project_id.id)]).ids
            project=self.env['project.project'].search([('id','=',vals['project_id'])])
            if project.code:
                vals['code'] = project.code+"-"+f'{len(buildings)+1:02}' or 'New'
        result = super(OLBuilding, self).create(vals)       
        return result

    # def generate_floor(self):
    #     if self.number_of_floors:
    #         floor_obj=self.env['property.floor']
    #         for i in range(self.number_of_floors):
    #             floor_obj.create({
    #                 'code':self.code+'-'+f'{i+1:02}',
    #                 'building_id':self.id
    #             })
    #     else:
    #         raise UserError("Enter Number Of Floors First")
    
class OLFloor(models.Model):
    _name="property.floor"
    name=fields.Char("Name")
    project_id=fields.Many2one("project.project","Project")
    short_name = fields.Char(string='Short Name')
    code = fields.Char(string='Code')
    units = fields.Many2many(comodel_name='product.product', string='Units')
    building_id = fields.Many2one(comodel_name='property.building', string='Building')
    unit_ids = fields.One2many('product.product', 'floor_id', string='Unit')
    project_analytical = fields.Many2one(related="building_id.project_id.analytic_account_id", string="Project Analytic Account")
    building_analytic_account = fields.Many2one(related="building_id.building_account_analytical", string="Building Analytic Account")
    floor_analytic_account = fields.Many2one('account.analytic.account', string="Floor Account Analytical")
    project_name = fields.Many2one(related="building_id.project_id", string="Project Name")

class PDC(models.Model):
    _name = "post.date.checks"

    customer_name = fields.Many2one("res.partner", string="Customer Name")
    name_of_cheque = fields.Char(string="Name of Cheque")
    date_of_cheqeu = fields.Date(string="Date of Cheque")
    Bank = fields.Char(string="Bank")
    attach = fields.Many2many('ir.attachment', 'ir_attach_rel',  'unit_ids', 'attachment_id', string="Attachments",help="If any")
    type_char = fields.Char("Type")



class ProductInh(models.Model):
    _inherit = 'product.product'
    short_name = fields.Char(string='Short Name')
    code = fields.Char(string='Code',default="New")
    building = fields.Many2one(comodel_name='property.building', string='Building')
    unit_type = fields.Selection(string='Unit Type', selection=[('parking', 'Parking'), ('appartment', 'Appartment'),])
    property_name = fields.Char(string='Name')
    property_type = fields.Selection(string='Property Type', selection=[('rent', 'Rent'), ('sale', 'Sale'),])
    property_price = fields.Float(string='Property Price')
    allow_discount = fields.Float(string='Allow Discount')
    reasonable_price = fields.Float(string='Reasonable Price')
    property_owner = fields.Many2one(comodel_name='res.partner', string='Property Owner')
    construction_status = fields.Char(string='Construction Status')
    floor_id = fields.Many2one('property.floor', string='Floor')
    state = fields.Selection([('new','NEW'),("reserve","RESERVE")],string="Status",default="new")
    sale_order = fields.Many2one('sale.order', string='Sale Order')
    project_analytical = fields.Many2one(related="floor_id.building_id.project_id.analytic_account_id", string="Project Analytic Account")
    building_analytic_account = fields.Many2one(related="floor_id.building_id.building_account_analytical", string="Building Analytic Account")
    floor_analytic_account = fields.Many2one(related="floor_id.floor_analytic_account", string="Floor Account Analytical")
    units_analytic_account = fields.Many2one('account.analytic.account', string="Units Account Analytical")
    order = fields.Many2one(related='sale_order.order_line.product_id')
    def action_confirm(self):
        for rec in self:
            rec.state = "new"
    def action_reserve(self):
        for rec in self:
            rec.state = "reserve"
    
        

class Sales_Order(models.Model):
    _inherit = "sale.order.line"

    @api.onchange('product_id')
    def order_create(self):
        # obj = self.env['product.product'].search([])
        ids= 0
        for rec in self:
            if rec.product_id:
                
                rec.product_id.sale_order = rec.order_id.ids[0]

                rec.product_id.state = "reserve"
                  
class Analytic_Account(models.Model):
    _inherit = "account.analytic.account"
    project_id = fields.Many2one('project.project', string='One')
    building_id = fields.Many2one('property.building', string='Building')
    floor_id = fields.Many2one("property.floor" , string="Floor Analytic Account")
    unit_id= fields.Many2one("product.product", string="Units Analytic Account")
    



