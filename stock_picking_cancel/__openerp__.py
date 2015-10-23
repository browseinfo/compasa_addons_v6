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
    "name" : "Stock Picking Cancel",
    "version" : "1.0",
    "author" : "BrowseInfo",
    "category" : "Stock",
    "description" : """This module add a button to cancel after to done""",
    "website" : "http://www.browseinfo.in",
    "license" : "AGPL-3",
    "depends" : [
        "stock",
        "account_relation_move"
        ],
    "demo" : [],
    "data" : [
        "security/picking_security.xml",
        "stock_workflow.xml",
        "stock_view.xml",
        ],
    "installable" : True,
    "active" : False,
}
