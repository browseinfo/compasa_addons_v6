# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from lxml import etree
import decimal_precision as dp

import netsvc
import pooler
from osv import fields, osv, orm
from tools.translate import _

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'rtn_field': fields.char('RTN',size=64),
    }


class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _columns = {
        'rtn_field': fields.char('RTN',size=64),
        'amount_in_words': fields.char('Amount In Words',size=64),
    }

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,\
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        invoice_addr_id = False
        contact_addr_id = False
        print "Fired Onchage+++++++++++++++++++++++++++++",partner_id
        partner_payment_term = False
        acc_id = False
        bank_id = False
        fiscal_position = False

        opt = [('uid', str(uid))]
        if partner_id:

            opt.insert(0, ('id', partner_id))
            res = self.pool.get('res.partner').address_get(cr, uid, [partner_id], ['contact', 'invoice'])
            contact_addr_id = res['contact']
            invoice_addr_id = res['invoice']
            p = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if company_id:
                if p.property_account_receivable.company_id.id != company_id and p.property_account_payable.company_id.id != company_id:
                    property_obj = self.pool.get('ir.property')
                    rec_pro_id = property_obj.search(cr,uid,[('name','=','property_account_receivable'),('res_id','=','res.partner,'+str(partner_id)+''),('company_id','=',company_id)])
                    pay_pro_id = property_obj.search(cr,uid,[('name','=','property_account_payable'),('res_id','=','res.partner,'+str(partner_id)+''),('company_id','=',company_id)])
                    if not rec_pro_id:
                        rec_pro_id = property_obj.search(cr,uid,[('name','=','property_account_receivable'),('company_id','=',company_id)])
                    if not pay_pro_id:
                        pay_pro_id = property_obj.search(cr,uid,[('name','=','property_account_payable'),('company_id','=',company_id)])
                    rec_line_data = property_obj.read(cr,uid,rec_pro_id,['name','value_reference','res_id'])
                    pay_line_data = property_obj.read(cr,uid,pay_pro_id,['name','value_reference','res_id'])
                    rec_res_id = rec_line_data and rec_line_data[0].get('value_reference',False) and int(rec_line_data[0]['value_reference'].split(',')[1]) or False
                    pay_res_id = pay_line_data and pay_line_data[0].get('value_reference',False) and int(pay_line_data[0]['value_reference'].split(',')[1]) or False
                    if not rec_res_id and not pay_res_id:
                        raise osv.except_osv(_('Configuration Error !'),
                            _('Can not find a chart of accounts for this company, you should create one.'))
                    account_obj = self.pool.get('account.account')
                    rec_obj_acc = account_obj.browse(cr, uid, [rec_res_id])
                    pay_obj_acc = account_obj.browse(cr, uid, [pay_res_id])
                    p.property_account_receivable = rec_obj_acc[0]
                    p.property_account_payable = pay_obj_acc[0]

            if type in ('out_invoice', 'out_refund'):
                acc_id = p.property_account_receivable.id
            else:
                acc_id = p.property_account_payable.id
            fiscal_position = p.property_account_position and p.property_account_position.id or False
            partner_payment_term = p.property_payment_term and p.property_payment_term.id or False
            if p.bank_ids:
                bank_id = p.bank_ids[0].id

        result = {'value': {
            'address_contact_id': contact_addr_id,
            'address_invoice_id': invoice_addr_id,
            'account_id': acc_id,
            'payment_term': partner_payment_term,
            'fiscal_position': fiscal_position
            }
        }

        if type in ('in_invoice', 'in_refund'):
            result['value']['partner_bank_id'] = bank_id
        
        result['value']['rtn_field'] = p.rtn_field or ''
        
        if payment_term != partner_payment_term:
            if partner_payment_term:
                to_update = self.onchange_payment_term_date_invoice(
                    cr, uid, ids, partner_payment_term, date_invoice)
                result['value'].update(to_update['value'])
            else:
                result['value']['date_due'] = False

        if partner_bank_id != bank_id:
            to_update = self.onchange_partner_bank(cr, uid, ids, bank_id)
            result['value'].update(to_update['value'])
        return result

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'

    def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, address_invoice_id=False, currency_id=False, context=None, company_id=None):
        if context is None:
            context = {}

        company_id = company_id

        if company_id != None:
            company_id = context.get('company_id',False)
        context = dict(context)
        context.update({'company_id': company_id})

        context = dict(context)
        context.update({'company_id': company_id})
        if not partner_id:
            raise osv.except_osv(_('No Partner Defined !'),_("You must first select a partner !") )
        if not product:
            if type in ('in_invoice', 'in_refund'):
                return {'value': {}, 'domain':{'product_uom':[]}}
            else:
                return {'value': {'price_unit': 0.0}, 'domain':{'product_uom':[]}}
        part = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
        fpos_obj = self.pool.get('account.fiscal.position')
        fpos = fposition_id and fpos_obj.browse(cr, uid, fposition_id, context=context) or False

        if part.lang:
            context.update({'lang': part.lang})
        result = {}
        res = self.pool.get('product.product').browse(cr, uid, product, context=context)
        print "ressssssssssssssssss",res.qty_available,qty
        if qty > res.qty_available:
            raise osv.except_osv(_('No Enough QTY !'),_("Can not create invoice because of not enough quantity for this product !") )

        if type in ('out_invoice','out_refund'):
            a = res.product_tmpl_id.property_account_income.id
            if not a:
                a = res.categ_id.property_account_income_categ.id
        else:
            a = res.product_tmpl_id.property_account_expense.id
            if not a:
                a = res.categ_id.property_account_expense_categ.id

        if context.get('account_id',False):
            # this is set by onchange_account_id() to force the account choosen by the
            # user - to get defaults taxes when product have no tax defined.
            a = context['account_id']

        a = fpos_obj.map_account(cr, uid, fpos, a)
        if a:
            result['account_id'] = a

        if type in ('out_invoice', 'out_refund'):
            taxes = res.taxes_id and res.taxes_id or (a and self.pool.get('account.account').browse(cr, uid, a, context=context).tax_ids or False)
        else:
            taxes = res.supplier_taxes_id and res.supplier_taxes_id or (a and self.pool.get('account.account').browse(cr, uid, a, context=context).tax_ids or False)
        tax_id = fpos_obj.map_tax(cr, uid, fpos, taxes)
        result['invoice_line_tax_id'] = tax_id

        warning = {}
        # When product changes, price ALWAYS need to be reset. If not price
        # found in product, or pricelist, it should become False. Only if
        # product_id has been cleared by user, we will leave price_unit as is.
        if  product:
            price_unit, pu_warning = self._price_unit_get(
                cr, uid, product, uom, qty, type, partner_id,
                currency_id, context=context)

            result['price_unit'] = price_unit
            warning.update(pu_warning)

        result['name'] = res.partner_ref

        domain = {}
        result['uos_id'] = res.uom_id.id or uom or False
        result['note'] = res.description
        if result['uos_id']:
            res2 = res.uom_id.category_id.id
            if res2:
                domain = {'uos_id':[('category_id','=',res2 )]}

        res_final = {'value': result, 'domain': domain, 'warning': warning}
        return res_final
