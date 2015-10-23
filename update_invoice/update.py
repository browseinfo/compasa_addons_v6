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
import openerp.netsvc as netsvc

class update_invoice(osv.osv):
	_name = 'update.invoice'
	_columns = {
		'file': fields.binary('Select File'),
	}


	def fix_product(self, cr, uid, ids, context=None):
		inventory_line_obj = self.pool.get('stock.inventory.line')
		product_pool = self.pool.get('product.product')
		move_pool = self.pool.get('stock.move')
		account_move_line = self.pool.get('account.move.line')
		wf_service = netsvc.LocalService("workflow")
		for self_obj in self.browse(cr, uid, ids):
			if self_obj.file:
				file_data = base64.decodestring(self_obj.file)
				input = cStringIO.StringIO(file_data)
				reader = csv.reader(input, delimiter=',', quotechar='"')
				csv_invoices = []
				for row in reader:
					product_id = product_pool.search(cr, uid, [('default_code','=', row[0]),('name','=', row[1]),('qty_available','=', row[2])])
					print product_id
					if product_id:
						stock_inventoryline_ids = inventory_line_obj.search(cr, uid, [('product_id','=', product_id[0]),('product_qty','=', row[2])])
						inventory_line_obj.unlink(cr, uid, stock_inventoryline_ids)
						stock_move_ids = move_pool.search(cr, uid, [('product_id','=', product_id[0])])
						print "stock_move_ids***************",stock_move_ids
						for move in move_pool.browse(cr,uid,stock_move_ids):
							move_pool.write(cr, uid, move.id, {'state': 'draft'})
							print "movestate==========",move.state,move.picking_id.id
							if move.picking_id:
								wf_service.trg_delete(uid, 'stock.picking', move.picking_id.id, cr)
								wf_service.trg_create(uid, 'stock.picking', move.picking_id.id, cr)
							move_pool.unlink(cr, uid, [move.id])
#							account_move_line_id = account_move_line.search(cr, uid, [('stock_move_id', '=', move.id)])
#							for move_line in account_move_line.browse(cr, uid, account_move_line_id,context=context):
#								print "move_line***************",move_line
#								result.setdefault(move_line.move_id.id, move.id)
#								account_move_line.unlink(cr, uid, [move_line.id])
#								print "unlinked--------------------"
							#move = move_pool.browse(cr,uid,move_id,context=context)
							#move_pool.unlink(cr, uid, move.id,context=context)
					product_pool.unlink(cr, uid, product_id,context=context)
		return True

	def update_product_single(self, cr, uid, ids, context=None):
		product_pool = self.pool.get('product.product')
		categ_pool = self.pool.get('product.category')
		for self_obj in self.browse(cr, uid, ids):
			if self_obj.file:
				file_data = base64.decodestring(self_obj.file)
				input = cStringIO.StringIO(file_data)
				reader = csv.reader(input, delimiter=',', quotechar='"')
				csv_invoices = []
				for row in reader:
					product_search = product_pool.search(cr, uid, [('default_code','=',row[3])])
					if product_search:
						for product in product_search:
							categ_search  = categ_pool.search(cr, uid, [('name', '=', row[1]),('parent_id.name','=',row[0])])
							if categ_search:
								categ_browse = categ_pool.browse(cr, uid, categ_search[0])
								product_pool.write(cr, uid, product, {'categ_id': categ_browse.id})
							else:
								#check for parent category
								parent_categ_search = categ_pool.search(cr, uid, [('name','=',row[0]),('parent_id','=',None)])
								#check for sub parent category
								if parent_categ_search:
									parent_categ_id = parent_categ_search[0]
								else:
									parent_categ_dic = {
														'name': row[0],
														}

									parent_categ_id = categ_pool.create(cr, uid, parent_categ_dic)

								#check for category
								categ_search = categ_pool.search(cr, uid, [('name','=',row[1]),('parent_id','=',parent_categ_id)])
								print '_______categ_search_1_______',categ_search
								if categ_search:
									categ_id = categ_search[0]
								else:
									categ_dic = {
												'name': row[1],
												'parent_id': parent_categ_id,
												}
									print '________categ_dic__________',categ_dic
									categ_id = categ_pool.create(cr, uid, categ_dic)

								product_pool.write(cr, uid, product, {'categ_id': categ_id})
					else:
						categ_search  = categ_pool.search(cr, uid, [('name', '=', row[1]),('parent_id.name','=' ,row[0])])
						print '______categ_search________',categ_search
						if categ_search:
							categ_id = categ_search[0]
						else:
							#check for sub parent category
							parent_categ_search = categ_pool.search(cr, uid, [('name','=',row[0])])
							if parent_categ_search:
								parent_categ_id = parent_categ_search[0]
							else:
								parent_categ_dic = {
													'name': row[0],
													}

								parent_categ_id = categ_pool.create(cr, uid, parent_categ_dic)
							print '______parent_categ_id_____',parent_categ_id
							categ_search = categ_pool.search(cr, uid, [('name','=',row[1]),('parent_id','=',parent_categ_id)])
							#check for category
							if categ_search:
								categ_id = categ_search[0]
							else:
								categ_dic = {
											'name': row[1],
											'parent_id': parent_categ_id,
											}
								categ_id = categ_pool.create(cr, uid, categ_dic)
						product_dic = {
										'name': row[4],
										'categ_id': categ_id,
										'default_code': row[3]
									}
						print '___product_dic________',product_dic
						product_id = product_pool.create(cr, uid, product_dic)
		return True


	def update_product(self, cr, uid, ids, context=None):
		product_pool = self.pool.get('product.product')
		categ_pool = self.pool.get('product.category')
		for self_obj in self.browse(cr, uid, ids):
			if self_obj.file:
				file_data = base64.decodestring(self_obj.file)
				input = cStringIO.StringIO(file_data)
				reader = csv.reader(input, delimiter=',', quotechar='"')
				csv_invoices = []
				for row in reader:
					print '_RRRRRRRRRRR__',row[2],row[3]
					product_search = product_pool.search(cr, uid, [('default_code','=',row[3])])
					print '_______product_search________',product_search
					if product_search:
						for product in product_search:
							categ_search  = categ_pool.search(cr, uid, [('name', '=', row[2]),('parent_id.name','=',row[1]),('parent_id.parent_id.name','=',row[0])])
							print '______categ_search________',categ_search
							if categ_search:
								categ_browse = categ_pool.browse(cr, uid, categ_search[0])
								product_pool.write(cr, uid, product, {'categ_id': categ_browse.id})
							else:
								print 'EeEeEeEeEeEeE___________'

								sub_parent_categ_search = categ_pool.search(cr, uid, [('name','=',row[0])])
								#check for sub parent category
								if sub_parent_categ_search:
									sub_parent_categ_id = sub_parent_categ_search[0]
								else:
									sub_parent_categ_dic = {
														'name': row[0],
														}

									sub_parent_categ_id = categ_pool.create(cr, uid, sub_parent_categ_dic)

								#check for parent category
								parent_categ_search = categ_pool.search(cr, uid, [('name','=',row[1]),('parent_id','=',sub_parent_categ_id)])
								#check for sub parent category
								if parent_categ_search:
									parent_categ_id = parent_categ_search[0]
								else:
									parent_categ_dic = {
														'name': row[1],
														'parent_id': sub_parent_categ_id
														}

									parent_categ_id = categ_pool.create(cr, uid, parent_categ_dic)

								#check for category
								categ_search = categ_pool.search(cr, uid, [('name','=',row[1]),('parent_id','=',parent_categ_id)])
								if categ_search:
									categ_id = categ_search[0]
								else:
									categ_dic = {
												'name': row[2],
												'parent_id': parent_categ_id,
												}

									categ_id = categ_pool.create(cr, uid, categ_dic)

								product_pool.write(cr, uid, product, {'categ_id': categ_id})
					else:
						print '_EEEEEEEEEEEEE______'
						categ_search  = categ_pool.search(cr, uid, [('name', '=', row[2]),('parent_id.name','=' ,row[1]),('parent_id.parent_id.name','=', row[0])])
						print '___E_____categ_search__________',categ_search
						if categ_search:
							categ_id = categ_search[0]
						else:
							#check for sub parent category
							sub_parent_categ_search = categ_pool.search(cr, uid, [('name','=',row[0])])
							if sub_parent_categ_search:
								sub_parent_categ_id = sub_parent_categ_search[0]
							else:
								sub_parent_categ_dic = {
													'name': row[0],
													}

								sub_parent_categ_id = categ_pool.create(cr, uid, sub_parent_categ_dic)

							#check for sub parent category
							parent_categ_search = categ_pool.search(cr, uid, [('name','=',row[1]),('parent_id','=',sub_parent_categ_id)])
							if parent_categ_search:
								parent_categ_id = parent_categ_search[0]
							else:
								parent_categ_dic = {
													'name': row[1],
													'parent_id': sub_parent_categ_id
													}

								parent_categ_id = categ_pool.create(cr, uid, parent_categ_dic)

							categ_search = categ_pool.search(cr, uid, [('name','=',row[1]),('parent_id','=',parent_categ_id)])
							#check for category
							if categ_search:
								categ_id = categ_search[0]
							else:

								categ_dic = {
											'name': row[2],
											'parent_id': parent_categ_id,
											}
								categ_id = categ_pool.create(cr, uid, categ_dic)
						product_dic = {
										'name': row[4],
										'categ_id': categ_id,
										'default_code': row[3]
									}
						print '___E____product_dic_______',product_dic
						product_id = product_pool.create(cr, uid, product_dic)
						print '___E_____product_id______',product_id
		return True

	def invoice_create(self, cr, uid, ids, context=None):
		invoice_pool = self.pool.get('account.invoice')
		invoice_line_pool = self.pool.get('account.invoice.line')
		wf_service = netsvc.LocalService("workflow")
		voucher_line_pool = self.pool.get('account.voucher.line')
		voucher_pool = self.pool.get('account.voucher')
		for self_obj in self.browse(cr, uid, ids):
			if self_obj.file:
				file_data = base64.decodestring(self_obj.file)
				input = cStringIO.StringIO(file_data)
				reader = csv.reader(input, delimiter='\t', quotechar='"')
				csv_invoices = []
				for row in reader:
					if row[2][-2:] in ('NC', 'FA', 'ND'):
						if row[2][-2:] == 'NC':
							invoice_type = 'out_refund'
						else:
							invoice_type = 'out_invoice'
						partner = self.pool.get('res.partner').search(cr, uid, [('name','=',row[1])])
						address_invoice_id = self.pool.get('res.partner').address_get(cr, uid, partner, ['contact', 'invoice'])
						if partner and address_invoice_id:
							partner_browse = self.pool.get('res.partner').browse(cr, uid, partner)
							dic_inv = {
								'partner_id': partner[0],
								'account_id': partner_browse[0].property_account_receivable.id,
								'address_invoice_id': address_invoice_id['invoice'],
								'type': invoice_type,
								'date_invoice': row[3],
							}
							invoice_id = invoice_pool.create(cr, uid, dic_inv)
							property_id = self.pool.get('ir.property').get(cr, uid, 'property_account_income_categ', 'product.category', context=context)
							dic_inv_line = {
								'name': 'Imported Invoice',
								'account_id': property_id.id,
								'quantity': 1,
								'price_unit': float(row[4]),
								'invoice_id': invoice_id
							}
							invoice_line_id = invoice_line_pool.create(cr, uid, dic_inv_line)


							invoice_pool.button_reset_taxes(cr, uid, [invoice_id])
							wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cr)

							invoice_pool.write(cr, uid, [invoice_id], {'number': row[2][:-2]})
					else:
						partner = self.pool.get('res.partner').search(cr, uid, [('name','=',row[1])])
						address_invoice_id = self.pool.get('res.partner').address_get(cr, uid, partner, ['contact', 'invoice'])
						journal_search = self.pool.get('account.journal').search(cr, uid, [('type','=','sale')])
						if partner and address_invoice_id:
							partner_browse = self.pool.get('res.partner').browse(cr, uid, partner)
							dic_voucher = {}
							dic_voucher =   {
									'partner_id': partner[0],
									'date' : row[3],
									'journal_id': journal_search[0],
									'number' : row[2][:-2],
									'type': 'sale',
									'account_id': partner_browse[0].property_account_receivable.id,
							}
							voucher_id = voucher_pool.create(cr, uid, dic_voucher,context=context)
							property_id = self.pool.get('ir.property').get(cr, uid, 'property_account_income_categ', 'product.category', context=context)
							dic_voucher_line = {
								'account_id': property_id.id,
								'amount': float(row[4]),
								'voucher_id': voucher_id
							}
							line_id = voucher_line_pool.create(cr, uid, dic_voucher_line,context=context)
							print "%%%%%%%%%%%%%%%%", line_id
							ans = wf_service.trg_validate(uid, 'account.voucher', voucher_id, 'proforma_voucher', cr)


		return True

	def invoice_paid(self, cr, uid, ids, context=None):
		invoice_pool = self.pool.get('account.invoice')
		invoice_line_pool = self.pool.get('account.invoice.line')
		voucher_pool = self.pool.get('account.voucher')
		voucher_line_pool = self.pool.get('account.voucher.line')
		wf_service = netsvc.LocalService("workflow")
		invoice_search = invoice_pool.search(cr, uid, [('state','=','open'),('type','=','out_invoice')])
		journal_search = self.pool.get('account.journal').search(cr, uid, [('type','in',['bank','cash'])])
		for open_inv in invoice_search:
			open_inv_browse = invoice_pool.browse(cr, uid, open_inv)
			dic_voucher = {}
			dic_voucher = {
				'partner_id': open_inv_browse.partner_id.id,
				'amount': open_inv_browse.amount_total,
				'journal_id': journal_search[0],
				'company_id': open_inv_browse.company_id.id,
				'account_id': open_inv_browse.account_id.id,
				'type': 'receipt'
			}
			voucher_id = voucher_pool.create(cr, uid, dic_voucher,context=context)
			voucher_browse = voucher_pool.browse(cr, uid, voucher_id)
			price = open_inv_browse.amount_total
			ttype = voucher_browse.type
			res = voucher_pool.recompute_voucher_lines(cr, uid, [voucher_id], open_inv_browse.partner_id.id, journal_search[0], price, open_inv_browse.currency_id.id, ttype, open_inv_browse.date_invoice)
			for cr_dic in res['value']['line_cr_ids']:
				cr_dic.update({'voucher_id': voucher_id})
				voucher_line_id = voucher_line_pool.create(cr, uid, cr_dic ,context=context)
			ans = wf_service.trg_validate(uid, 'account.voucher', voucher_id, 'proforma_voucher', cr)


	def refund_paid(self, cr, uid, ids, context=None):
		invoice_pool = self.pool.get('account.invoice')
		invoice_line_pool = self.pool.get('account.invoice.line')
		voucher_pool = self.pool.get('account.voucher')
		voucher_line_pool = self.pool.get('account.voucher.line')
		wf_service = netsvc.LocalService("workflow")
		invoice_search = invoice_pool.search(cr, uid, [('state','=','open'),('type','=','out_refund')])
		journal_search = self.pool.get('account.journal').search(cr, uid, [('type','in',['bank','cash'])])
		for open_inv in invoice_search:
			open_inv_browse = invoice_pool.browse(cr, uid, open_inv)
			dic_voucher = {}
			dic_voucher = {
				'partner_id': open_inv_browse.partner_id.id,
				'amount': open_inv_browse.amount_total,
				'journal_id': journal_search[0],
				'company_id': open_inv_browse.company_id.id,
				'account_id': open_inv_browse.account_id.id,
				'type': 'payment'
			}
			voucher_id = voucher_pool.create(cr, uid, dic_voucher,context=context)
			voucher_browse = voucher_pool.browse(cr, uid, voucher_id)
			price = open_inv_browse.amount_total
			ttype = voucher_browse.type
			res = voucher_pool.recompute_voucher_lines(cr, uid, [voucher_id], open_inv_browse.partner_id.id, journal_search[0], price, open_inv_browse.currency_id.id, ttype, open_inv_browse.date_invoice)
			for cr_dic in res['value']['line_cr_ids']:
				cr_dic.update({'voucher_id': voucher_id})
				voucher_line_id = voucher_line_pool.create(cr, uid, cr_dic ,context=context)
			ans = wf_service.trg_validate(uid, 'account.voucher', voucher_id, 'proforma_voucher', cr)
			#voucher_pool.proforma_voucher(cr, uid, [voucher_id],context=context)
		return True


	def invoice_validate(self, cr, uid, ids, context=None):
		invoice_pool = self.pool.get('account.invoice')
		wf_service = netsvc.LocalService("workflow")
		invoice_search = invoice_pool.search(cr, uid, [('state','=','draft'),('type','in',('out_invoice','out_refund'))])
		for invoice in invoice_search:
			print "$$$$$$$$$$$$$$$$$$", invoice
			ans = wf_service.trg_validate(uid, 'account.invoice', invoice, 'invoice_open', cr)
			#voucher_pool.proforma_voucher(cr, uid, [voucher_id],context=context)
		return True
update_invoice()
