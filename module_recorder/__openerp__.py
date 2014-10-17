# -*- encoding: utf-8 -*-
# #############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
#
# This program is free software: you can redistribute it and/or modify
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Module Recorder',
    'version': '1.0',
    'author': 'Savoir-faire Linux',
    'maintainer': 'Savoir-faire Linux',
    'website': 'http://www.savoirfairelinux.com',
    'license': 'AGPL-3',
    'category': 'Website',
    'summary': 'This module records modifications of models during a session.',
    'description': """
Module Recorder
===============
Module to record the modifications done during a session in models.
With this module installed, data will be exported in a csv file.

Features
    * Export data in CSV through a new module compatible with import
      (i.e. data files are ordered and splitted if necessary)
    * Export automatically properties linked to selected models

TODO
    * Manage workflow - Eg.: export a validated invoice and import it at
      this same state, in particular if account moves were exported

Contributors
------------
* Jordi RIERA (jordi.riera@savoirfairelinux.com)
* Bruno JOLIVEAU (bruno.joliveau@savoirfairelinux.com)

Thanks to
---------
* Corentin Pouhet-brunerie (corentin.pouhet-brunerie@smile.fr)

More information
----------------
* Module developed and tested with Odoo version 8.0
* For questions, please contact our support services \
(support@savoirfairelinux.com)
    """,
    'depends': [],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        'wizard/module_recorder_view.xml',
    ],
    'demo': [],
    'installable': True,
}
