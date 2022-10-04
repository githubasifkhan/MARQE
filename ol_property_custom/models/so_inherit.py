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

class OLStartDate(models.Model):
    _inherit = 'sale.order'
    purchase_1_individual = fields.Many2one(comodel_name='res.partner', string='Individual')
    purchase_1_company = fields.Many2one(comodel_name='res.company', string='Company')
    purchase_2_individual = fields.Many2one(comodel_name='res.partner', string='Individual')
    purchase_2_company = fields.Many2one(comodel_name='res.company', string='Company')
    location = fields.Char(string='Location')
    relevent_unit_no = fields.Many2one(comodel_name='product.product', string='Relevent Unit No')
    relevent_unit_area = fields.Char(string='Relevent Unit Area')
    relevent_bays_no = fields.Char(string='Relevent Bays No')
    bank_details = fields.Many2one(comodel_name='res.bank', string='Bank Details')
    anticipated_completion_date = fields.Date(string='Anticipated Completion Date')
    permitted_use = fields.Char(string='Permitted Use')
    late_payment_fee = fields.Char(string='Late Payment Fee')
    
class ContactInherit(models.Model):
    _inherit = 'res.partner'
    country_arabic = fields.Many2one(comodel_name='res.country', string='Nationality (Arabic)')
    passport_eng = fields.Char(string='Passport (English)')
    passport_arabic = fields.Char(string='Passport (Arabic)')
    fax_eng = fields.Char(string='Fax No (English)')
    fax_arabic = fields.Char(string='Fax No (Arabic)')
    street_arabic=fields.Char(String="Street (Arabic)")
    street2_arabic=fields.Char(String="street2 (Arabic)")
    zip_arabic=fields.Char(String="Zip(Arabic)")
    city_arabic=fields.Char(String="City (Arabic)")
    state_id_arabic = fields.Many2one(comodel_name='res.country.state', string='State')

class ContactInheritInCompany(models.Model):
    _inherit = 'res.company'
    country_arabic = fields.Many2one(comodel_name='res.country', string='Nationality (Arabic)')
    passport_eng = fields.Char(string='Passport (English)')
    passport_arabic = fields.Char(string='Passport (Arabic)')
    fax_eng = fields.Char(string='Fax No (English)')
    fax_arabic = fields.Char(string='Fax No (Arabic)')
    street_arabic=fields.Char(String="Street (Arabic)")
    street2_arabic=fields.Char(String="street2 (Arabic)")
    zip_arabic=fields.Char(String="Zip(Arabic)")
    city_arabic=fields.Char(String="City (Arabic)")
    state_id_arabic = fields.Many2one(comodel_name='res.country.state', string='State')


