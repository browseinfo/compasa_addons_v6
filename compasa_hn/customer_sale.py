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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import netsvc

import time
from lxml import etree

import decimal_precision as dp
from osv import fields, osv, orm
from tools.translate import _


class purchase_requisition(osv.osv):
    _inherit = 'purchase.requisition'
    _columns = {
        'x_tipo_proveedor':fields.selection([('nacional','Nacional'),('extranjero','Extranjero')], 'Tipo Proveedor'),
    }

class payment_order(osv.osv):
    _inherit = 'payment.order'
    _columns = {
        'x_numcheque':fields.char('Numero de Cheque', size=64, required=True),
    }

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    _columns = {
        'x_stock':fields.selection([('compasa','Compasa'),('externo','Externo')], 'Stock'),
    }

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    _columns = {
        'x_tipo_proveedor':fields.selection([('nacional','Nacional'),('extranjero','Extranjero')], 'Tipo Compra'),
    }

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _columns = {
        'x_tipo_proveedor':fields.selection([('nacional','Nacional'),('extranjero','Extranjero')], 'Tipo Compra'),
        'x_numfacruta': fields.char('Numero Factura', size=64),
        'x_tipo_contenedor':fields.selection([('20 pies','20 Pies'),('40 pies','40 Pies')], 'Tipo Contenedor'),
        'x_cantidad_contenedor': fields.char('Cantidad Contenedores', size=64),
        ##'x_vende':fields.many2one('res.users', 'Vendedor'),
        'x_proyecto': fields.many2one('project.project', 'Proyecto', domain=[('state', '=','open')]),
        'x_nombre_contado': fields.char('Nombre en factura', size=64),
    }



    def create(self, cr, uid, vals, context=None):
        vals.update({'x_numfacruta':self.pool.get('ir.sequence').get(cr, uid, 'account.factura')})
        return super(account_invoice, self).create(cr, uid, vals, context=context)

    _defaults = {
        'x_numfacruta':'/'
        }

class sale_order(osv.osv):
    _inherit = 'sale.order'

    _columns = {
        'x_proyecto': fields.many2one('project.project', 'Proyecto', domain=[('state', '=','open')]),
        'x_nombre_contado': fields.char('Nombre en factura', size=64),
    }

    def action_wait(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.partner_id.credit_limit:
                raise osv.except_osv(_('Error !'),_('You cannot confirm a sale order for the customer whose credit limit is not set.'))
            for l in o.order_line:
                if not l.product_id:
                    raise osv.except_osv(_('Error !'),_('You cannot confirm a sale order which has lines without product.'))
        return super(sale_order, self).action_wait(cr, uid, ids, context=context)

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        invoice_vals['x_nombre_contado'] = order.x_nombre_contado
        invoice_vals['x_proyecto'] = order.x_proyecto.id
        return invoice_vals

class res_partner(osv.osv):
    """

    def _check_permissions(self, cr, uid, ids, field_name, arg, context):
        res = {}

        # Get the Sale Manager id's
        manager_id = self.pool.get('ir.model.data').get_object(cr, uid, 'base', 'group_sale_manager').id

        # Get the user and see what groups he/she is in
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)

        group_ids = []
        for grp in user.groups_id:
            group_ids.append(grp.id)

        if (manager_id in group_ids):
            isManager =True
        else:
            isManager = False

        for i in ids:
            if not i:
                continue

            res[i] = isManager

        return res
    """

    _inherit = "res.partner"
    _columns = {
        'credit_limit': fields.float(string='Credit Limit',read=['base.group_sale_salesman'],write=['base.group_sale_manager']),
        ###'is_manager': fields.function(_check_permissions, type='char', method=True, string="Is Manager"),
    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
