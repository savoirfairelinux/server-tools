# -*- encoding: utf-8 -*- #
# OpenERP, Open Source Management Solution
#    This module copyright (C) 2013 Savoir-faire Linux
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

from openerp.tests import common


class test_prototype(common.TransactionCase):
    def setUp(self):
        super(test_prototype, self).setUp()
        self.main_model = self.env[
            'prototype'
        ]
        self.module_category_model = self.env[
            'ir.module.category'
        ]

        self.prototype = self.main_model.create({
            'name': 't_name',
            'category_id': self.module_category_model.browse(1).id,
            'human_name': 't_human_name',
            'summary': 't_summary',
            'description': 't_description',
            'author': 't_author',
            'maintainer': 't_maintainer',
            'website': 't_website',
        })

    def _test_generate_files(self):
        """Test it returns a ."""
        self.assertTrue(False)
