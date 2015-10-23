# -*- encoding: utf-8 -*-
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
{
    "name": "Account relation move",
    "version": "1.0",
    'author': 'BrowseInfo',
    'website': 'http://www.browseinfo.in',
    "category": "Generic Modules/Account",
    "description": """ Adds 4 fields to generate a connection between account
    and production models
    """,
    'depends': ['mrp'],
    'init_xml': [],
    'update_xml': [
        #'account_view.xml',
        ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
}
