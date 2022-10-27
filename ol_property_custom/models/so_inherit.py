import datetime
from email.policy import default
from pyexpat import model
from re import U
from tokenize import String

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import base64
import requests
import datetime
from datetime import timedelta


class purchaser(models.Model):
    _name = 'purchaser.company'
    purchase_individual = fields.Many2one(comodel_name='res.partner', string='Individual')
    purchase_company = fields.Many2one(comodel_name='res.company', string='Company')
    purchaser_id = fields.Many2one(comodel_name='sale.order')


# class paymentterms(models.Model):
#     _name = 'payment.terms'
#     installment = fields.Many2one(comodel_name='account.payment', string='Individual')
#     payment_id = fields.Many2one(comodel_name = 'account.payment')

class payment(models.Model):
    _inherit = 'account.move'
    so_ids = fields.Many2one(comodel_name='sale.order')
    # per_invoices = fields.Integer(string='% of installment')
    #
    #
    # @api.onchange('invoice_line_ids','invoice_line_ids.percentage_of_invoice')
    # def treeview(self):
    #
    #     self.per_invoices = self.invoice_line_ids.percentage_of_invoice
    #     print(self.per_invoices)



    # payment_id = fields.Many2one(comodel_name='sale.order',relation='payment_terms_ids', string="Sale Order")

class subtotal(models.Model):
    _inherit = 'account.move.line'

    subtotal_so = fields.Integer(string='Subtotal of SO')
    percentage_of_invoice = fields.Integer(String='% of installment', compute='substraction')


    def substraction(self):
        self.percentage_of_invoice = (self.price_subtotal / float(self.subtotal_so))*100
        print(self.percentage_of_invoice)




class saleorderline(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def onchangeionid(self):

        var = self.env["product.product"].search([('name', '=' , self.partner_id.name)])
        product_ids=[]
        for p in var:
            product_ids.append((0,0,{
                'product_id':p.id,
                'name': p.name,
                'product_uom_qty': 1,
                'price_unit': p.list_price,
                'order_id': self.id,
                'product_uom_qty':p.uom_id.id if p.uom_id else False,
                'tax_id':False
            }))
        self.write({
            'order_line':product_ids
        })


class OLStartDate(models.Model):
    _inherit = 'sale.order'
    purchaser_ids = fields.One2many('purchaser.company', 'purchaser_id')
    payment_terms_ids = fields.One2many('account.move', 'so_ids', string='Payment Terms')

    # select_purchase = fields.Selection([('purchase_1', 'Purchaser 1'), ('purchase_2', 'Purchaser 2'), ('purchase_3', 'Purchaser 3'), ('purchase_4', 'Purchaser 4')],
    #                                                string='Select Purchase',
    #                                                default='purchase_1')
    location = fields.Char(string='Location')
    location_arabic = fields.Char(string='Location Arabic')
    relevent_unit_no = fields.Many2one(comodel_name='product.product', string='Relevent Unit No')
    relevent_unit_area = fields.Char(string='Relevent Unit Area')
    relevent_bays_no = fields.Char(string='Relevent Bays No')

    bank_details = fields.Many2one(comodel_name='res.bank', string='Bank Details')
    anticipated_completion_date = fields.Date(string='Anticipated Completion Date')
    permitted_use = fields.Char(string='Permitted Use')
    permitted_use_arabic = fields.Char(string='Permitted Use(Arabic)')
    late_payment_fee = fields.Char(string='Late Payment Fee')
    late_payment_arabic = fields.Char(string='Late Payment Fee(Arabic)')
    down_payment = fields.Selection([('amount', 'Amount'), ('percentage', 'Percentage')],
                                    string='Down Payment',
                                    default='amount')
    down_payment_amount = fields.Integer(String= "Down Payment Amount", compute='downpaymentamount')
    amount = fields.Char(String='Amount')
    payment = fields.Selection(
        [('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('byannual', 'By Annual'), ('annual', 'Annual')],
        default='monthly')
    start_date = fields.Date(String='Starting Date')
    end_date = fields.Date(String='Ending Date')
    percentage = fields.Float(String='Percentage')
    payment_duration = fields.Integer(String='Duration', default=1)
    installment_amount = fields.Integer(String='Duration', compute='installmentamount')
    installment_payable_amount = fields.Float(String='Installment Payable Amount', compute='subtractioninamount')
    project = fields.Many2one('project.project', string='Project')

    # @api.depends('amount','amount_total')
    def subtractioninamount(self):
        if self.down_payment == "amount":
            self.installment_payable_amount = self.amount_total - float(self.amount)

        else:
            var = (self.percentage * self.amount_total)
            self.installment_payable_amount = self.amount_total - var
            # print(self.installment_payable_amount)

    def installmentamount(self):
        self.installment_amount = self.installment_payable_amount / float(self.payment_duration)

    def downpaymentamount(self):
        self.down_payment_amount = self.amount_total - self.installment_payable_amount


    def create_invoice_installment(self):
        # raise  UserError("check")
        invoice_lines = []
        order=self
        so_line=self.order_line[0]

        invoice_vals = {
            'ref': order.client_order_ref,
            'move_type': 'out_invoice',
            'invoice_origin': order.name,
            'invoice_user_id': order.user_id.id,
            'narration': order.note,
            'partner_id': order.partner_invoice_id.id,
            'fiscal_position_id': (order.fiscal_position_id or order.fiscal_position_id.get_fiscal_position(
                order.partner_id.id)).id,
            'partner_shipping_id': order.partner_shipping_id.id,
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_reference': order.reference,
            'invoice_payment_term_id': order.date_order,
            'partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
            'team_id': order.team_id.id,
            'campaign_id': order.campaign_id.id,
            'medium_id': order.medium_id.id,
            'source_id': order.source_id.id,
            'so_ids': order.id,
            'invoice_line_ids': [(0, 0, {
                'name': so_line.name,
                'price_unit': order.down_payment_amount,
                'quantity': 1.0,
                'product_id': so_line.product_id.id,
                'product_uom_id': so_line.product_uom.id,
                'tax_ids': [(6, 0, so_line.tax_id.ids)],
                'sale_line_ids': [(6, 0, [so_line.id])],
                'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'analytic_account_id': order.analytic_account_id.id or False,
                'subtotal_so': so_line.price_subtotal,

            })],
        }
        invoice = self.env['account.move'].with_company(order.company_id) \
            .sudo().create(invoice_vals).with_user(self.env.uid)

        if self.payment == "monthly":
            pass

            # for i in range(0,self.payment_duration):
            #     order = self
            #     so_line = self.order_line[0]

            #     trigger = self.start_date + relativedelta(months=i+0)



            #     invoice_vals = {
            #         'ref': order.client_order_ref,
            #         'move_type': 'out_invoice',
            #         'invoice_origin': order.name,
            #         'invoice_user_id': order.user_id.id,
            #         'narration': order.note,
            #         'partner_id': order.partner_invoice_id.id,
            #         'fiscal_position_id': (order.fiscal_position_id or order.fiscal_position_id.get_fiscal_position(
            #             order.partner_id.id)).id,
            #         'partner_shipping_id': order.partner_shipping_id.id,
            #         'currency_id': order.pricelist_id.currency_id.id,
            #         'payment_reference': order.reference,
            #         'invoice_date_due': trigger,

            #         # 'invoice_payment_term_id': trigger,
            #         'partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
            #         'team_id': order.team_id.id,
            #         'campaign_id': order.campaign_id.id,
            #         'medium_id': order.medium_id.id,
            #         'source_id': order.source_id.id,
            #         'so_ids': order.id,

            #         'invoice_line_ids': [(0, 0, {
            #             'name': so_line.name,
            #             'price_unit': order.installment_amount,
            #             'quantity': 1.0,
            #             'product_id': so_line.product_id.id,
            #             'product_uom_id': so_line.product_uom.id,
            #             'tax_ids': [(6, 0, so_line.tax_id.ids)],
            #             'sale_line_ids': [(6, 0, [so_line.id])],
            #             'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
            #             'analytic_account_id': order.analytic_account_id.id or False,
            #             'subtotal_so': so_line.price_subtotal,



            #         })],
            #     }
            #     invoice = self.env['account.move'].with_company(order.company_id) \
            #         .sudo().create(invoice_vals).with_user(self.env.uid)


        elif self.payment == "quarterly":
            pass
            # counter = 0
            # for i in range(0, self.payment_duration):
            #     order = self

            #     so_line = self.order_line[0]

            #     trigger = self.start_date + relativedelta(months=counter)
            #     counter = counter + 3

            #     invoice_vals = {
            #         'ref': order.client_order_ref,
            #         'move_type': 'out_invoice',
            #         'invoice_origin': order.name,
            #         'invoice_user_id': order.user_id.id,
            #         'narration': order.note,
            #         'partner_id': order.partner_invoice_id.id,
            #         'fiscal_position_id': (order.fiscal_position_id or order.fiscal_position_id.get_fiscal_position(
            #             order.partner_id.id)).id,
            #         'partner_shipping_id': order.partner_shipping_id.id,
            #         'currency_id': order.pricelist_id.currency_id.id,
            #         'payment_reference': order.reference,
            #         'invoice_date_due': trigger,
            #         'partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
            #         'team_id': order.team_id.id,
            #         'campaign_id': order.campaign_id.id,
            #         'medium_id': order.medium_id.id,
            #         'source_id': order.source_id.id,
            #         'so_ids': order.id,
            #         'invoice_line_ids': [(0, 0, {
            #             'name': so_line.name,
            #             'price_unit': order.installment_amount,
            #             'quantity': 1.0,
            #             'product_id': so_line.product_id.id,
            #             'product_uom_id': so_line.product_uom.id,
            #             'tax_ids': [(6, 0, so_line.tax_id.ids)],
            #             'sale_line_ids': [(6, 0, [so_line.id])],
            #             'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
            #             'analytic_account_id': order.analytic_account_id.id or False,


            #         })],
            #     }
            #     invoice = self.env['account.move'].with_company(order.company_id) \
            #         .sudo().create(invoice_vals).with_user(self.env.uid)
        elif self.payment == "byannual":
            pass
            # counter1 = 0
            # for i in range(0, self.payment_duration):
            #     order = self
            #     so_line = self.order_line[0]
            #     trigger = self.start_date + relativedelta(months=counter1)
            #     counter1 = counter1 + 6
            #     invoice_vals = {
            #         'ref': order.client_order_ref,
            #         'move_type': 'out_invoice',
            #         'invoice_origin': order.name,
            #         'invoice_user_id': order.user_id.id,
            #         'narration': order.note,
            #         'partner_id': order.partner_invoice_id.id,
            #         'fiscal_position_id': (order.fiscal_position_id or order.fiscal_position_id.get_fiscal_position(
            #             order.partner_id.id)).id,
            #         'partner_shipping_id': order.partner_shipping_id.id,
            #         'currency_id': order.pricelist_id.currency_id.id,
            #         'payment_reference': order.reference,
            #         'invoice_date_due': trigger,
            #         'partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
            #         'team_id': order.team_id.id,
            #         'campaign_id': order.campaign_id.id,
            #         'medium_id': order.medium_id.id,
            #         'source_id': order.source_id.id,
            #         'so_ids': order.id,
            #         'invoice_line_ids': [(0, 0, {
            #             'name': so_line.name,
            #             'price_unit': order.installment_amount,
            #             'quantity': 1.0,
            #             'product_id': so_line.product_id.id,
            #             'product_uom_id': so_line.product_uom.id,
            #             'tax_ids': [(6, 0, so_line.tax_id.ids)],
            #             'sale_line_ids': [(6, 0, [so_line.id])],
            #             'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
            #             'analytic_account_id': order.analytic_account_id.id or False,


            #         })],
            #     }
            #     invoice = self.env['account.move'].with_company(order.company_id) \
            #         .sudo().create(invoice_vals).with_user(self.env.uid)
        else:
            pass

            # counter3 = 0
            # for i in range(0, self.payment_duration):
            #     order = self
            #     so_line = self.order_line[0]
            #     trigger = self.start_date + relativedelta(months=counter3)
            #     counter3 = counter3 + 12
            #     invoice_vals = {
            #         'ref': order.client_order_ref,
            #         'move_type': 'out_invoice',
            #         'invoice_origin': order.name,
            #         'invoice_user_id': order.user_id.id,
            #         'narration': order.note,
            #         'partner_id': order.partner_invoice_id.id,
            #         'fiscal_position_id': (order.fiscal_position_id or order.fiscal_position_id.get_fiscal_position(
            #             order.partner_id.id)).id,
            #         'partner_shipping_id': order.partner_shipping_id.id,
            #         'currency_id': order.pricelist_id.currency_id.id,
            #         'payment_reference': order.reference,
            #         'invoice_date_due': trigger,
            #         'partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
            #         'team_id': order.team_id.id,
            #         'campaign_id': order.campaign_id.id,
            #         'medium_id': order.medium_id.id,
            #         'source_id': order.source_id.id,
            #         'so_ids': order.id,
            #         'invoice_line_ids': [(0, 0, {
            #             'name': so_line.name,
            #             'price_unit': order.installment_amount,
            #             'quantity': 1.0,
            #             'product_id': so_line.product_id.id,
            #             'product_uom_id': so_line.product_uom.id,
            #             'tax_ids': [(6, 0, so_line.tax_id.ids)],
            #             'sale_line_ids': [(6, 0, [so_line.id])],
            #             'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
            #             'analytic_account_id': order.analytic_account_id.id or False,


            #         })],
            #     }
            #     invoice = self.env['account.move'].with_company(order.company_id) \
            #         .sudo().create(invoice_vals).with_user(self.env.uid)
        # for line in self.order_line:
        #     vals = {
        #         'product_id': line.product_id.id,
        #         'name': line.name,
        #         'price_unit': line.price_unit,
        #         'quantity': line.product_uom_qty,
        #     }
        #
        #     invoice_lines.append((0, 0, vals))
        # # product_line = self.env['sale.order'].search([('partner_id', '=', self.id)])
        # # self.so_ids = product_line.name
        #
        # created = self.env['account.move'].create({
        #     'partner_id': self.partner_id.id,
        #     'move_type': 'out_invoice',
        #     'invoice_user_id': self.user_id.id,
        #     'currency_id': self.pricelist_id.currency_id.id,
        #     'invoice_line_ids': invoice_lines,
        #     'so_ids': self.id,
        # })

    # def _prepare_invoice_line(self, **optional_values):
    #     res = super(OLStartDate, self)._prepare_invoice_line(**optional_values)
    #     # stock_move_line=self.env['stock']
    #     res.update({
    #         'product_id': self.product_id.id,
    #         'name': self.name,
    #         'price_unit': self.price_unit,
    #         'quantity': self.product_uom_qty,
    #     })
    #     return res


class ContactInherit(models.Model):
    _inherit = 'res.partner'
    country_arabic = fields.Many2one(comodel_name='res.country', string='Nationality (Arabic)')
    passport_eng = fields.Char(string='Passport (English)')
    passport_arabic = fields.Char(string='Passport (Arabic)')
    fax_eng = fields.Char(string='Fax No (English)')
    fax_arabic = fields.Char(string='Fax No (Arabic)')
    street_arabic = fields.Char(String="Street (Arabic)")
    street2_arabic = fields.Char(String="street2 (Arabic)")
    zip_arabic = fields.Char(String="Zip(Arabic)")
    city_arabic = fields.Char(String="City (Arabic)")
    state_id_arabic = fields.Many2one(comodel_name='res.country.state', string='State')


class ContactInheritInCompany(models.Model):
    _inherit = 'res.company'
    country_arabic = fields.Many2one(comodel_name='res.country', string='Nationality (Arabic)')
    passport_eng = fields.Char(string='Passport (English)')
    passport_arabic = fields.Char(string='Passport (Arabic)')
    fax_eng = fields.Char(string='Fax No (English)')
    fax_arabic = fields.Char(string='Fax No (Arabic)')
    street_arabic = fields.Char(String="Street (Arabic)")
    street2_arabic = fields.Char(String="street2 (Arabic)")
    zip_arabic = fields.Char(String="Zip(Arabic)")
    city_arabic = fields.Char(String="City (Arabic)")
    registration_no = fields.Char(String="Registration No")
    state_id_arabic = fields.Many2one(comodel_name='res.country.state', string='State')


class inheritanceinbank(models.Model):
    _inherit = 'res.bank'

    account_no = fields.Char(String='Account Number')
    account_name = fields.Char(String='Account Name')
    IBAN = fields.Char(String='IBAN')
    swift = fields.Char(String='SWIFT')
