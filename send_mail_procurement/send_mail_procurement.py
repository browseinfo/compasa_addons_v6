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
from openerp import tools

import datetime
import logging
import pooler
import tools
import netsvc
from datetime import date, timedelta
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import html2plaintext

class sale_order(osv.osv):
    _inherit = "sale.order"

    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        procurement_obj = self.pool.get('procurement.order')
        message = self.pool.get('mail.message')
        proc_ids = []

        for line in order_lines:
            if line.state == 'done':
                continue

            date_planned = self._get_date_planned(cr, uid, order, line, order.date_order, context=context)

            if line.product_id:
                if line.product_id.product_tmpl_id.type in ('product', 'consu'):
                    if not picking_id:
                        picking_id = picking_obj.create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
                    move_id = move_obj.create(cr, uid, self._prepare_order_line_move(cr, uid, order, line, picking_id, date_planned, context=context))
                else:
                    # a service has no stock move
                    move_id = False

                proc_id = procurement_obj.create(cr, uid, self._prepare_order_line_procurement(cr, uid, order, line, move_id, date_planned, context=context))
                proc_ids.append(proc_id)
                line.write({'procurement_id': proc_id})
                self.ship_recreate(cr, uid, order, line, move_id, proc_id)

        wf_service = netsvc.LocalService("workflow")
        if picking_id:
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)

        for proc_id in proc_ids:
            wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)

        logg_user = self.pool.get('res.users').browse(cr,uid, [uid], context)[0]
        category_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'group_stock_manager')[1]
        group = self.pool.get('res.groups').browse(cr, uid, category_id, context=context)
        template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'send_mail_procurement', 'email_template_procurement')[1]
        print "template_id**********",template_id
        if group.users and uid in [x.id for x in group.users]:
            procure_obj = self.pool.get('procurement.order').browse(cr, uid, proc_ids[0], context=context)
            if procure_obj.procure_method == 'make_to_stock' :
                print "in condition**********"
#                    email_from = logg_user.user_email or ''
#                    email_to = user_id.user_email or ''
#                    subject = "Create Procurement Order"
#                    body = "Details Of Procurement \n Product Name :%s \n Source :%s \n Quantity :%s %s "%(
#                        procure_obj.product_id.name,procure_obj.origin,procure_obj.product_qty,procure_obj.product_uom.name)
                self.pool.get('email.template').send_mail(cr, uid, template_id, procure_obj.id,
                                                          force_send=False, context=context)
                    #return message.schedule_with_attach(cr, uid, email_from, [email_to], subject, body)

        val = {}
        if order.state == 'shipping_except':
            val['state'] = 'progress'
            val['shipped'] = False

            if (order.order_policy == 'manual'):
                for line in order.order_line:
                    if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                        val['state'] = 'manual'
                        break
        order.write(val)
        return True


class procurement_order(osv.osv):
    _inherit = 'procurement.order'

    def _procure_orderpoint_confirm(self, cr, uid, automatic=False,\
            use_new_cursor=False, context=None, user_id=False):
        if context is None:
            context = {}
        if use_new_cursor:
            cr = pooler.get_db(use_new_cursor).cursor()
        orderpoint_obj = self.pool.get('stock.warehouse.orderpoint')
        location_obj = self.pool.get('stock.location')
        procurement_obj = self.pool.get('procurement.order')
        request_obj = self.pool.get('res.request')
        wf_service = netsvc.LocalService("workflow")
        message = self.pool.get('mail.message')
        report = []
        offset = 0
        ids = [1]
        if automatic:
            self.create_automatic_op(cr, uid, context=context)
        while ids:
            ids = orderpoint_obj.search(cr, uid, [], offset=offset, limit=100)
            for op in orderpoint_obj.browse(cr, uid, ids, context=context):
                if op.procurement_id.state != 'exception':
                    if op.procurement_id and op.procurement_id.purchase_id and op.procurement_id.purchase_id.state in ('draft', 'confirmed'):
                        continue
                prods = location_obj._product_virtual_get(cr, uid,
                        op.location_id.id, [op.product_id.id],
                        {'uom': op.product_uom.id})[op.product_id.id]

                if prods < op.product_min_qty:
                    qty = max(op.product_min_qty, op.product_max_qty)-prods

                    reste = qty % op.qty_multiple
                    if reste > 0:
                        qty += op.qty_multiple - reste

                    if qty <= 0:
                        continue
                    if op.product_id.type not in ('consu'):
                        if op.procurement_draft_ids:
                        # Check draft procurement related to this order point
                            pro_ids = [x.id for x in op.procurement_draft_ids]
                            procure_datas = procurement_obj.read(cr, uid, pro_ids, ['id','product_qty'], context=context, order='product_qty desc')
                            to_generate = qty
                            for proc_data in procure_datas:
                                if to_generate >= proc_data['product_qty']:
                                    wf_service.trg_validate(uid, 'procurement.order', proc_data['id'], 'button_confirm', cr)
                                    procurement_obj.write(cr, uid, [proc_data['id']],  {'origin': op.name}, context=context)
                                    to_generate -= proc_data['product_qty']
                                if not to_generate:
                                    break
                            qty = to_generate

                    if qty:
                        proc_id = procurement_obj.create(cr, uid,
                                                         self._prepare_orderpoint_procurement(cr, uid, op, qty, context=context),
                                                         context=context)
                        wf_service.trg_validate(uid, 'procurement.order', proc_id,
                                'button_confirm', cr)
                        wf_service.trg_validate(uid, 'procurement.order', proc_id,
                                'button_check', cr)
                        orderpoint_obj.write(cr, uid, [op.id],
                                {'procurement_id': proc_id}, context=context)
                        logg_user = self.pool.get('res.users').browse(cr,uid, [uid], context)[0]
                        category_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'group_stock_manager')[1]
                        group = self.pool.get('res.groups').browse(cr, uid, category_id, context=context)
                        template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'send_mail_procurement', 'email_template_procurement')[1]
                        if group.users and uid in [x.id for x in group.users]:
                                procure_obj = self.pool.get('procurement.order').browse(cr, uid, proc_id, context=context)
                                if procure_obj.procure_method == 'make_to_stock' :
#                                email_from = logg_user.user_email or ''
#                                email_to = user_id.user_email or ''
#                                subject = "Automatic Procurement Order me"
#                                body = "Details Of Procurement \n Product Name :%s \n Source :%s \n Quantity :%s %s "%(
#                                    procure_obj.product_id.name,procure_obj.origin,procure_obj.product_qty,procure_obj.product_uom.name)
#                                message.schedule_with_attach(cr, uid, email_from, [email_to], subject, body)
                                    self.pool.get('email.template').send_mail(cr, uid, template_id, procure_obj.id,
                                                          force_send=False, context=context)


            offset += len(ids)
            if use_new_cursor:
                cr.commit()
        if user_id and report:
            request_obj.create(cr, uid, {
                'name': 'Orderpoint report.',
                'act_from': user_id,
                'act_to': user_id,
                'body': '\n'.join(report)
            })
        if use_new_cursor:
            cr.commit()
            cr.close()
        return {}