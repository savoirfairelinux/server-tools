# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2010 - 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
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
from openerp import models, fields


class prototype(models.Model):
    _name = "prototype"
    _description = "Prototype"

    name = fields.Char('Technical Name', required=True)
    category_id = fields.Many2one('ir.module.category', 'Category')
    shortdesc = fields.Char('Module Name', required=True)
    summary = fields.Char('Summary', required=True)
    description = fields.Html('Description', required=True)
    author = fields.Char('Author', required=True)
    maintainer = fields.Char('Maintainer')
    website = fields.Char('Website')
    icon_image = fields.Binary('Icon')
    version = fields.Char('Version', size=3, default='0.1')
    auto_install = fields.Boolean('Auto Install', default=False)
    # Relations
    dependencies = fields.Many2many(
        'ir.module.module', 'prototype_module_rel',
        'prototype_id', 'module_id',
        'Dependencies'
    )
    data = fields.Many2many(
        'ir.filters',
        'prototype_data_rel',
        'prototype_id', 'filter_id',
        'Data filters',
        help="The records matching the filters will be added as data."
    )
    demo = fields.Many2many(
        'ir.filters',
        'prototype_demo_rel',
        'prototype_id', 'filter_id',
        'Demo filters',
        help="The records matching the filters will be added as demo data."
    )
    fields = fields.Many2many(
        'ir.model.fields', 'prototype_fields_rel',
        'prototype_id', 'field_id', 'Fields'
    )
    menu = fields.Many2many(
        'ir.ui.menu', 'prototype_menu_rel',
        'prototype_id', 'menu_id', 'Menu Items'
    )
    views = fields.Many2many(
        'ir.ui.view', 'prototype_view_rel',
        'prototype_id', 'view_id', 'Views'
    )
    groups = fields.Many2many(
        'res.groups', 'prototype_groups_rel',
        'prototype_id', 'group_id', 'Groups'
    )
    rights = fields.Many2many(
        'ir.model.access', 'prototype_rights_rel',
        'prototype_id', 'right_id',
        'Access Rights'
    )
    rules = fields.Many2many(
        'ir.rule', 'prototype_rule_rel',
        'prototype_id', 'rule_id', 'Record Rules'
    )

