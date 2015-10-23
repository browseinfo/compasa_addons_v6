##############################################################################
#
# Copyright (c) 2008-2011 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
#                    General contacts <info@alistek.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from report import report_sxw
from report.report_sxw import rml_parse

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'chunks2':self._chunks2,
            'get_digits':self.get_digits,
            'get_discount': self.get_discount,
            'get_subtotal': self.get_subtotal,
            'get_discount_tax': self.get_discount_tax,
        })

    def _chunks2(self, l, n):
        """ Yield successive n-sized chunks from l.
        """
        for i in xrange(0, len(l), n):
            last = i+n >= len(l)
            yield {'last_chunk':last,'lines':l[i:i+n]}


    def get_discount(self, obj):
        total_discount = 0.00
        for line in obj.invoice_line:
            discount = (line.price_unit * line.discount) / 100
            total_discount += discount
        return total_discount

    def get_discount_tax(self, obj):
        total_with_discount = 0.0
        discount_tax = 0.00
        for line in obj.invoice_line:
            discount = (line.price_unit * line.discount) / 100
            discount_tax += discount
        total_with_discount = line.invoice_id.amount_untaxed + discount_tax
        return total_with_discount

    def get_subtotal(self, obj):
        total_subtotal = 0.00
        for line in obj.invoice_line:
            total_subtotal += line.price_unit
        return total_subtotal

