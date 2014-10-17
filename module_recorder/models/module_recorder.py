# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

import base64
import csv
import StringIO
import time
import zipfile

from openerp.tools.translate import _
from openerp import models, api
# I use osv as it seems the api v8 raises some issues as the fields
# are not found in the view if I use the syntax field_name = field.FieldType()
from openerp.osv import fields

def _get_data_filename(models, filetype):
    if filetype != 'csv':
        models = [model.replace('.', '_') for model in models]
    filenames = []
    for model in models:
        filename = 'data/%s.%s' % (model, filetype)
        if filename in filenames:
            filenames.append('data_addition/%s.%s' % (model, filetype))
        else:
            filenames.append(filename)
    return filenames

class ModuleRecorder(models.TransientModel):
    _name = 'module.recorder'
    _description = "Module Recorder"

    _columns = {
        'state': fields.selection([('draft', 'Draft'), ('done', 'Done')], 'State', readonly=True),
        'start_date': fields.datetime('Records from', required=True),
        'date_filter': fields.selection([
                                            ('create', 'created'),
                                            ('write', 'modified'),
                                            ('create_write', 'created or modified'),
                                            ], 'Records only', required=True),
        'model_ids': fields.many2many('ir.model', 'base_module_record_model_rel',
                                      'wizard_id', 'model_id', 'Objects',
                                      domain=[('osv_memory', '=', False)]),
        'file': fields.binary('File', filename='filename', readonly=True),
        'filename': fields.char('Filename', size=64, required=True),
        'filetype': fields.selection([('csv', 'CSV'), ('yml', 'YAML')], 'Filetype', required=True),
        }

    _defaults = {
        'state': 'draft',
        'start_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'date_filter': 'create_write',
        'filename': 'data_module.zip',
        'filetype': 'csv',
        }

    @api.model
    def _get_models(self, wizard):
        models = wizard.model_ids
        if not models:
            model_obj = self.pool.get('ir.model')
            model_ids = model_obj.search(
                self._cr, self._uid,
                [('osv_memory', '=', False)],
                context=self._context,
            )
            models = [
                model for model in model_obj.browse(
                    self._cr, self._uid, model_ids, context=self._context)
                if self.pool.get(model.model)._auto
            ]
        return models

    @api.model
    def _get_domain(self, wizard):
        domain = []
        if 'create' in wizard.date_filter:
            domain.append(('create_date', '>=', wizard.start_date))
        if 'write' in wizard.date_filter:
            domain.append(('write_date', '>=', wizard.start_date))
        if wizard.date_filter == 'create_write':
            domain = ['|'] + domain
        return domain

    def _export_ir_properties(self, cr, uid, models,
                              res_ids_by_model, context=None):
        if 'ir.property' in (model.model for model in models):
            return []
        property_obj = self.pool.get('ir.property')
        property_ids = []
        for model in models:
            res_ids = [False] + [
                '%s,%s' % (model, res_id)
                for res_id in res_ids_by_model[model.model]
            ]
            property_ids.extend(property_obj.search(cr, uid, [
                ('fields_id.model_id', '=', model.id),
                ('res_id', 'in', res_ids),
            ], context=context))
        fields_to_export = property_obj.get_fields_to_export()
        rows = [fields_to_export]
        rows.extend(property_obj.export_data(
            cr, uid, property_ids, fields_to_export, context)['datas']
        )
        return [('ir.property', rows)]

    def _export_data_by_model(self, cr, uid, wizard, context=None):
        models = self._get_models(cr, uid, wizard, context)
        model_ids = [model.id for model in models]
        datas = self.pool.get('ir.model').get_model_graph(
            cr, uid, model_ids, context
        )
        domain = self._get_domain(
            cr, uid, wizard, context
        )
        res_ids_by_model = {}
        for index, (model, fields_to_export) in enumerate(datas):
            res_obj = self.pool.get(model)
            res_ids = res_obj.search(
                cr, uid, res_obj._log_access and domain or [], context=context
            )
            if 'parent_left' in res_obj._columns:
                res_ids = res_obj.search(
                    cr, uid,  [('id', 'in', res_ids)],
                    order='parent_left', context=context
                )
            res_ids_by_model[model] = res_ids
            rows = [fields_to_export]
            rows.extend(
                res_obj.export_data(
                    cr, uid, res_ids, fields_to_export, context
                )['datas']
            )
            datas[index] = (model, rows)
        datas.extend(
            self._export_ir_properties(
                cr, uid, models, res_ids_by_model, context
            )
        )
        return datas

    @staticmethod
    def _convert_to_csv(rows):
        s = StringIO.StringIO()
        writer = csv.writer(s, quoting=csv.QUOTE_NONNUMERIC)
        for row in rows:
            for index, data in enumerate(row):
                if not data:
                    data = None
                if data is True:
                    data = 1
                if isinstance(data, basestring):
                    data = data.replace('\n', ' ').replace('\t', ' ')
                    try:
                        data = data.encode('utf-8')
                    except UnicodeError:
                        pass
                row[index] = data
            writer.writerow(row)
        return s.getvalue()

    @staticmethod
    def _convert_to_yml(rows):
        raise NotImplemented

    @api.model
    def _get_data_filecontent(self, wizard):
        data_files = []
        for model, rows in self._export_data_by_model(wizard):
            data_files.append(
                (
                    model,
                    getattr(
                        ModuleRecorder,
                        '_convert_to_%s' % wizard.filetype
                    )(rows)
                )
            )
        return data_files


    @api.model
    def _get_dependencies(self, wizard):
        modules = []
        for model in self._get_models(wizard):
            modules.extend(model.modules.split(', '))
        return ', '.join(map(lambda mod: '"%s"' % mod, set(modules)))

    @property
    def openerp_filecontent(self):
        return """{
    "name" : "Data Module",
    "version" : "1.0",
    'author': 'Savoir-faire Linux',
    'maintainer': 'Savoir-faire Linux',
    'website': 'http://www.savoirfairelinux.com',
    "description": "Data module created from module_record",
    "category" : "Data",
    "depends" : [%(dependencies)s],
    "data" : [
        %(data_files)s,
    ],
    "demo" : [],
    "test": [],
    "installable": True,
}"""

    @api.model
    def create_module(self, ids):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for wizard in self.browse(ids):
            datas = self._get_data_filecontent(wizard)
            models = [model for model, rows in datas]
            filenames = _get_data_filename(models, wizard.filetype)
            zip_content = {
                '__init__.py': "#\n# Generated by module_record\n#\n",
                '__openerp__.py': self.openerp_filecontent % {
                    'dependencies': self._get_dependencies(wizard),
                    'data_files': ',\n        '.join(
                        map(lambda model: '"%s"' % model, filenames)
                    ),
                },
            }
            for index, filename in enumerate(filenames):
                zip_content[filename] = datas[index][1]
            s = StringIO.StringIO()
            zip = zipfile.ZipFile(s, 'w')
            for filename, filecontent in zip_content.iteritems():
                info = zipfile.ZipInfo(filename)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 2175008768  # specifies mode 0644
                zip.writestr(info, filecontent)
            zip.close()
            wizard.write(
                {'file': base64.encodestring(s.getvalue()), 'state': 'done'}
            )
        return True

    @api.model
    def open_wizard(self, ids):
        assert len(ids) == 1, "ids must be a list with only one id"
        return {
            'name': _('Export Customizations as a Module'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'module.recorder',
            'domain': [],
            'context': self._context,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': ids[0],
        }

    @api.model
    def button_create_module(self, ids):
        self.create_module(ids)
        return self.open_wizard(ids)

