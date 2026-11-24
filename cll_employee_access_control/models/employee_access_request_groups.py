# -*- coding: utf-8 -*-

from collections import defaultdict
from lxml import etree
from lxml.builder import E
import itertools

from odoo import models, fields, api, _,Command
from odoo.exceptions import UserError
from odoo.tools import  partition
from itertools import chain, repeat


def is_boolean_group(name):
    return name.startswith('in_group_')

def is_selection_groups(name):
    return name.startswith('sel_groups_')

def is_reified_group(name):
    return is_boolean_group(name) or is_selection_groups(name)

def get_boolean_group(name):
    return int(name[9:])

def get_selection_groups(name):
    return [int(v) for v in name[11:].split('_')]

def parse_m2m(commands):
    "return a list of ids corresponding to a many2many value"
    ids = []
    for command in commands:
        if isinstance(command, (tuple, list)):
            if command[0] in (Command.UPDATE, Command.LINK):
                ids.append(command[1])
            elif command[0] == Command.CLEAR:
                ids = []
            elif command[0] == Command.SET:
                ids = list(command[2])
        else:
            ids.append(command)
    return ids

class EmployeeAccessControl(models.Model):
    _inherit = 'employee.access.control'

    @api.model_create_multi
    def create(self, vals_list):
        new_vals_list = []
        for values in vals_list:
            new_vals_list.append(self._remove_reified_groups(values))
        requests = super(EmployeeAccessControl, self).create(new_vals_list)
        return requests

    def write(self, values):
        values = self._remove_reified_groups(values)
        res = super(EmployeeAccessControl, self).write(values)
        return res

    @api.model
    def new(self, values=None, origin=None, ref=None):
        if values is None:
            values = {}
        values = self._remove_reified_groups(values)
        request = super().new(values=values, origin=origin, ref=ref)
        return request

    @api.model
    def default_get(self, fields):
        group_fields, fields = partition(is_reified_group, fields)
        fields1 = (fields + ['group_ids']) if group_fields else fields
        values = super(EmployeeAccessControl, self).default_get(fields1)
        self._add_reified_groups(group_fields, values)
        return values

    def _determine_fields_to_fetch(self, field_names, ignore_when_in_cache=False):
        valid_fields = partition(is_reified_group, field_names)[1]
        return super()._determine_fields_to_fetch(valid_fields, ignore_when_in_cache)

    def _read_format(self, fnames, load='_classic_read'):
        valid_fields = partition(is_reified_group, fnames)[1]
        return super()._read_format(valid_fields, load)

    @api.model
    def _update_user_request_view(self):
        """Modify the view with xmlid 'your_module.cll_roles_view'"""
        # remove the language to avoid translations
        self = self.with_context(lang=None)

        # Get the placeholder view
        view = self.env.ref('cll_employee_access_control.cll_roles_view', raise_if_not_found=False)
        # Get roles organized by application and type
        roles_by_app = self._get_roles_by_application_and_type()

        xml0, xml1, xml2 = [], [], []  # xml0: invisible, xml1: selections, xml2: checkboxes

        for app, role_types in sorted(roles_by_app.items(),
                                      key=lambda x: x[0].sequence if x[0] else 1000):
            app_name = app.name if app else "Privileged Access"
            # readonly_state = f"state not in {self.get_editable_states()} or not can_edit"
            readonly_state = "not can_edit"
            # 1. SELECTION ROLES (Application roles)
            if role_types['selection']:
                role_ids = [r.id for r in role_types['selection']]
                field_name = self._name_selection_roles(role_ids)

                # Add selection field
                xml1.append(E.field(
                    name=field_name,
                    readonly=readonly_state,
                    string=f"{app_name}",
                    on_change='1',
                    help=f"Select {app_name} role for this request",
                    invisible =f" system_id != {app.system_id.id}"
                ))
                xml1.append(E.newline())

                # Add duplicate invisible field so default values are saved on create
                xml0.append(E.field(
                    name=field_name,
                    invisible="1"
                ))

            # 2. CHECKBOX ROLES (Extra access)
            if role_types['checkbox']:
                xml2.append(E.separator(
                    string=f"{app_name}",
                    colspan="2",

                ))

                left_group, right_group = [], []

                for index, role in enumerate(role_types['checkbox']):
                    field_name = self._name_boolean_role(role.id)

                    dest_group = left_group if index % 2 == 0 else right_group
                    dest_group.append(E.field(
                        name=field_name,
                        string=role.name,
                        help=role.description or f"Enable {role.name} access",
                        invisible=f" system_id != {role.system_id.id}",
                        readonly=readonly_state,
                        widget='boolean_toggle'
                    ))

                    # Add duplicate invisible field so default values are saved on create
                    xml0.append(E.field(
                        name=field_name,
                        invisible="1"
                    ))

                xml2.append(E.group(*left_group))
                xml2.append(E.group(*right_group))
                xml2.append(E.newline())

        # Create the final XML structure - this replaces the placeholder
        xml = E.field(
            *(xml0),  # Invisible fields first
            E.group(*(xml1), string="Application Access"),
            E.group(*(xml2), invisible="not is_privileged_required",),
            name="group_ids",
            position="replace"
        )
        xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY CLL ROLES"))

        # Serialize and update the view
        xml_content = etree.tostring(xml, pretty_print=True, encoding="unicode")


        if xml_content != view.arch:  # avoid useless xml validation if no change
            new_context = dict(view._context)
            new_context['lang'] = None
            view.with_context(new_context).write({'arch': xml_content})

    @api.model
    def _get_roles_by_application_and_type(self):
        """Return roles classified by application and display type."""
        Role = self.env['cll.system.role']
        roles = Role.search([('active', '=', True)], order='application_sequence, sequence')
        # Organize by application and display type
        result = defaultdict(lambda: {'selection': [], 'checkbox': []})

        for role in roles:
            if role.display_type == 'selection':
                result[role.application_id]['selection'].append(role)
            elif role.display_type == 'checkbox':
                result[role.application_id]['checkbox'].append(role)

        return result

    @api.model
    def _name_selection_roles(self, role_ids):
        """Generate field name for selection roles."""
        return 'sel_groups_' + '_'.join(str(rid) for rid in sorted(role_ids))

    @api.model
    def _name_boolean_role(self, role_id):
        """Generate field name for boolean role field."""
        return f'in_group_{role_id}'

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Add dynamic fields to fields_get."""
        res = super().fields_get(allfields, attributes)

        # Add dynamic selection fields
        roles_by_app = self._get_roles_by_application_and_type()

        for app, role_types in roles_by_app.items():
            if role_types['selection']:
                role_ids = [r.id for r in role_types['selection']]
                field_name = self._name_selection_roles(role_ids)

                # Create selection options
                selection = []
                for role in role_types['selection']:
                    selection.append((str(role.id), role.name))

                res[field_name] = {
                    'type': 'selection',
                    'string': f"{app.name if app else 'Other'} Role",
                    'selection': selection,
                    'help': f"Select {app.name if app else 'Other'} role",
                    'store': False,
                    'searchable': False,
                }

            # Add boolean fields for checkboxes
            for role in role_types['checkbox']:
                field_name = self._name_boolean_role(role.id)
                res[field_name] = {
                    'type': 'boolean',
                    'string': role.name,
                    'help': role.description or f"Enable {role.name}",
                    'store': False,
                    'searchable': False,
                }

        return res



    def read(self, fields=None, load='_classic_read'):
        # determine whether reified groups fields are required, and which ones
        fields1 = fields or list(self.fields_get())
        group_fields, other_fields = partition(is_reified_group, fields1)

        # read regular fields (other_fields); add 'groups_id' if necessary
        drop_groups_id = False
        if group_fields and fields:
            if 'group_ids' not in other_fields:
                other_fields.append('group_ids')
                drop_groups_id = True
        else:
            other_fields = fields

        res = super(EmployeeAccessControl, self).read(other_fields, load=load)

        # post-process result to add reified group fields
        if group_fields:
            for values in res:
                self._add_reified_groups(group_fields, values)
                if drop_groups_id:
                    values.pop('group_ids', None)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if fields:
            # ignore reified fields
            fields = [fname for fname in fields if not is_reified_group(fname)]
        return super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    def _add_reified_groups(self, fields, values):
        """ add the given reified group fields into `values` """
        gids = set(parse_m2m(values.get('group_ids') or []))

        for f in fields:
            if is_boolean_group(f):
                values[f] = get_boolean_group(f) in gids
            elif is_selection_groups(f):
                # determine selection groups, in order
                sel_groups = self.env['cll.system.role'].sudo().browse(get_selection_groups(f))
                selected = [gid for gid in sel_groups.ids if gid in gids]

                values[f] = selected and str(selected[-1]) or False

    def _remove_reified_groups(self, values):
        """ return `values` without reified group fields """
        add, rem = [], []
        values1 = {}

        for key, val in values.items():
            if is_boolean_group(key):
                (add if val else rem).append(get_boolean_group(key))
            elif is_selection_groups(key):
                rem += get_selection_groups(key)
                if val:
                    add.append(int(val))
            else:
                values1[key] = val

        if 'group_ids' not in values and (add or rem):
            added = self.env['cll.system.role'].sudo().browse(add)
            added_ids = added._ids
            # remove group ids in `rem` and add group ids in `add`
            # do not remove groups that are added by implied
            values1['group_ids'] = list(itertools.chain(
                zip(repeat(3), [gid for gid in rem if gid not in added_ids]),
                zip(repeat(4), add)
            ))

        return values1

    def onchange(self, values, field_names, fields_spec):
        reified_fnames = [fname for fname in fields_spec if is_reified_group(fname)]
        if reified_fnames:
            values = {key: val for key, val in values.items() if key != 'group_ids'}
            values = self._remove_reified_groups(values)

            if any(is_reified_group(fname) for fname in field_names):
                field_names = [fname for fname in field_names if not is_reified_group(fname)]
                field_names.append('group_ids')

            fields_spec = {
                field_name: field_spec
                for field_name, field_spec in fields_spec.items()
                if not is_reified_group(field_name)
            }
            fields_spec['group_ids'] = {}

        result = super().onchange(values, field_names, fields_spec)

        if reified_fnames and 'group_ids' in result.get('value', {}):
            self._add_reified_groups(reified_fnames, result['value'])
            result['value'].pop('group_ids', None)

        return result