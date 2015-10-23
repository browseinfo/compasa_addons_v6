# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
import logging
import csv
import base64
import cStringIO
from openerp.tools.translate import _
import sys
from urllib2 import urlopen
from xlwt import Workbook, easyxf, Formula
import StringIO


class stock_inventory(osv.osv):
    _inherit = 'stock.inventory'
    _columns = {
        'attachment_csv' : fields.binary('File'),
        }

    def import_csv(self, cr, uid, ids, context=None):
            stock_move_obj = self.pool.get('stock.move')
            product_obj = self.pool.get('product.product')
            location_obj = self.pool.get('stock.location')
            uom_obj = self.pool.get('product.uom')
            aa = self.browse(cr,uid,ids)[0]
            product_ids = product_obj.search(cr, uid, [])
            csv_invoices = []
            if not aa.attachment_csv:
                raise osv.except_osv(_('Import Error!'), _('Please Select Valid File.'))  
            if aa.attachment_csv:
                file_data = base64.decodestring(aa.attachment_csv)
                input = cStringIO.StringIO(file_data)
                reader = csv.reader(input,delimiter='\t')
                data = []
#                count = 1 
                row_len = 1
                
                for row in reader:
#                    if count == 1:
#                    	count = 0
#                    	continue
                    #uom_id = uom_obj.search(cr, uid, [('name', '=', row[2])])
 #                   csv_invoices.append(row[0])
 #               for product_id in product_ids:
                    product_id = product_obj.search(cr, uid, [('default_code', '=', row[0])])[0]
                    if not product_id:
                        raise osv.except_osv(_('Error!'), _("There is no Product '%s' Please Create!" % row[1]))
                    uom_id = product_obj.browse(cr, uid, product_id, context=context).uom_id.id
#                    location_id = location_obj.search(cr, uid, [('name', '=', row[4])],context=context)
#                    if not location_id:
#                        raise osv.except_osv(_('Error!'), _("There is no Location '%s' Please Create!" % row[4]))
#                    if product_id in csv_invoices:
#                        continue
 #                   if len(product_id) > 0:
 #                   else:
                    data_create = {'product_id':product_id,'location_id':12,
        		                           'product_uom' : uom_id, 'product_qty' : row[3], 'inventory_id' : aa.id}
                    self.pool.get('stock.inventory.line').create(cr, uid,data_create,context=context)

#			product_obj.write(cr, uid, [product_id],{'list_price':0.0, 'standard_price':0.0}) 	

stock_inventory()



