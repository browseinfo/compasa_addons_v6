# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2014-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

import time
from lxml import etree
import decimal_precision as dp
import netsvc
import pooler
from osv import fields, osv, orm
from tools.translate import _
from osv import osv,fields
import base64
import csv
import cStringIO
import math
from tools import ustr
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare


class sale_order_cancel_reason(osv.osv):
    _name = 'sale.order.cancel.reason'
    _description = 'Sale Order Cancel Reason'
    _columns = {
        'name': fields.char('Reason', size=64, required=True, translate=True),
    }

class sale_order(osv.osv):
    _inherit = 'sale.order'

    _columns = {
        'cancel_reason_id': fields.many2one(
            'sale.order.cancel.reason',
            string="Reason for cancellation",
            readonly=True,
        ),
    }

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    def _product_markup(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = 0
            if line.product_id:
                res[line.id] = ((line.price_unit-line.purchase_price)/line.purchase_price)*100
                # 100 - (((line.price_unit - line.purchase_price) * 100) / line.price_unit)
                #res[line.id] = line.price_unit - line.purchase_price
        return res

    _columns = {
        'markup': fields.function(_product_markup, method=True, string='Markup(%)'),
    }
