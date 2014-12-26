# -*- encoding: utf-8 -*-
# #############################################################################
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
import os
from datetime import date
from collections import namedtuple
from jinja2 import Environment, FileSystemLoader
from openerp import models, api

# to avoid conflicts with a field of the new model.
from openerp import fields as oe_fields


class prototype(models.Model):
    _name = "prototype"
    _description = "Prototype"

    name = oe_fields.Char('Technical Name', required=True)
    category_id = oe_fields.Many2one('ir.module.category', 'Category')
    human_name = oe_fields.Char('Module Name', required=True)
    summary = oe_fields.Char('Summary', required=True)
    description = oe_fields.Text('Description', required=True)
    author = oe_fields.Char('Author', required=True)
    maintainer = oe_fields.Char('Maintainer')
    website = oe_fields.Char('Website')
    icon_image = oe_fields.Binary('Icon')
    version = oe_fields.Char('Version', size=3, default='0.1')
    auto_install = oe_fields.Boolean('Auto Install', default=False)
    # Relations
    dependency_ids = oe_fields.Many2many(
        'ir.module.module', 'prototype_module_rel',
        'prototype_id', 'module_id',
        'Dependencies'
    )
    data_ids = oe_fields.Many2many(
        'ir.filters',
        'prototype_data_rel',
        'prototype_id', 'filter_id',
        'Data filters',
        help="The records matching the filters will be added as data."
    )
    demo_ids = oe_fields.Many2many(
        'ir.filters',
        'prototype_demo_rel',
        'prototype_id', 'filter_id',
        'Demo filters',
        help="The records matching the filters will be added as demo data."
    )
    field_ids = oe_fields.Many2many(
        'ir.model.fields', 'prototype_fields_rel',
        'prototype_id', 'field_id', 'Fields'
    )
    menu_ids = oe_fields.Many2many(
        'ir.ui.menu', 'prototype_menu_rel',
        'prototype_id', 'menu_id', 'Menu Items'
    )
    view_ids = oe_fields.Many2many(
        'ir.ui.view', 'prototype_view_rel',
        'prototype_id', 'view_id', 'Views'
    )
    group_ids = oe_fields.Many2many(
        'res.groups', 'prototype_groups_rel',
        'prototype_id', 'group_id', 'Groups'
    )
    right_ids = oe_fields.Many2many(
        'ir.model.access', 'prototype_rights_rel',
        'prototype_id', 'right_id',
        'Access Rights'
    )
    rule_ids = oe_fields.Many2many(
        'ir.rule', 'prototype_rule_rel',
        'prototype_id', 'rule_id', 'Record Rules'
    )

    __data_files = []
    _env = None
    File_details = namedtuple('file_details', ['filename', 'filecontent'])
    template_path = '{}/../templates/'.format(os.path.dirname(__file__))

    @api.model
    def set_jinja_env(self, api_version):
        """Set the Jinja2 environment.
        The environment will helps the system to find the templates to render.
        :param api_version: string, odoo api
        :return: jinja2.Environment instance.
        """
        if self._env is None:
            self._env = Environment(
                loader=FileSystemLoader(
                    os.path.join(self.template_path, api_version)
                )
            )
        return self._env

    @api.model
    def generate_files(self):
        """ Generates the files from the details of the prototype.
        :return: tuple
        """
        assert self._env is not None, \
            'Run set_env(api_version) before to generate files.'

        file_details = []
        file_details.extend(self.generate_models_details())
        file_details.extend(self.generate_views_details())
        file_details.append(self.generate_module_init_file_details())
        # must be the last as the other generations might add information
        # to put in the __openerp__: additional dependencies, views files, etc.
        file_details.append(self.generate_module_openerp_file_details())

        return file_details

    @api.model
    def generate_module_openerp_file_details(self):
        """Wrapper to generate the __openerp__.py file of the module."""
        return self.generate_file_details(
            '__openerp__.py',
            '__openerp__.py.template',
            name=self.name,
            version=self.version,
            author=self.author,
            maintainer=self.maintainer,
            website=self.website,
            category=self.category_id.name,
            summary=self.summary,
            description=self.description,
            dependencies=[
                dependency.name for dependency in self.dependency_ids
            ],
            auto_install=self.auto_install,
            export_date=date.today().year,
            data_files=self.__data_files,
        )

    @api.model
    def generate_module_init_file_details(self):
        """Wrapper to generate the __init__.py file of the module."""
        return self.generate_file_details(
            '__init__.py',
            '__init__.py.template',
            # no import models if no work of fields in
            # the prototype
            models=bool(self.field_ids)
        )

    @api.model
    def generate_models_details(self):
        """Finds the models from the list of fields and generates
        the __init__ file and each models files (one by class).
        """
        files = []
        # TODO: doesn't work as need to find the module to import
        # and it is not necessary the name of the model the fields
        # belongs to.
        # ie. field.cell_phone is defined in a model inheriting from
        # res.partern.
        # How do we find the module the field was defined in?
        # dependencies = set([dep.id for dep in self.dependencies])

        relations = {}
        for field in self.field_ids:
            model = field.model_id
            relations.setdefault(model, []).append(field)
            # dependencies.add(model.id)

        # blind update of dependencies.
        # self.write({
        #     'dependencies': [(6, 0, [id_ for id_ in dependencies])]
        # })

        files.append(self.generate_models_init_details(relations.keys()))
        for model, fields in relations.iteritems():
            files.append(self.generate_model_details(model, fields))

        return files

    @api.model
    def generate_models_init_details(self, ir_models):
        """Wrapper to generate the __init__.py file in models folder."""
        return self.generate_file_details(
            'models/__init__.py',
            'models/__init__.py.template',
            models=[
                self.friendly_name(ir_model.model)
                for ir_model in ir_models
            ]
        )

    @api.model
    def generate_views_details(self):
        """Wrapper to generate the views files."""
        relations = {}
        for view in self.view_ids:
            relations.setdefault(view.model, []).append(view)

        views_details = []
        for model, views in relations.iteritems():
            filepath = 'views/{}_view.xml'.format(
                self.friendly_name(model)
            )
            views_details.append(
                self.generate_file_details(
                    filepath,
                    'views/model_view.xml.template',
                    views=views
                )
            )
            self.__data_files.append(filepath)

        return views_details

    @api.model
    def generate_model_details(self, model, field_ids):
        """Wrapper to generate the python file for the model.

        :param model: ir.model record.
        :param field_ids: list of ir.model.fields records.
        :return: FileDetails instance.
        """
        python_friendly_name = self.friendly_name(model.model)
        return self.generate_file_details(
            'models/{}.py'.format(python_friendly_name),
            'models/model_name.py.template',
            name=python_friendly_name,
            inherit=model.model,
            fields=field_ids
        )

    @staticmethod
    def friendly_name(name):
        return name.replace('.', '_')

    @api.model
    def generate_file_details(self, filename, template, **kwargs):
        """ generate file details from jinja2 template.
        :param filename: name of the file the content is related to
        :param template: path to the file to render the content
        :param kwargs: arguments of the template
        :return: File_details instance
        """
        template = self._env.get_template(template)
        return self.File_details(filename, template.render(kwargs))
