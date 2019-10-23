from django import forms
from django.forms import ValidationError, inlineformset_factory
from django.conf import settings
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm, get_groups_with_perms, remove_perm
from collections import OrderedDict

from tom_targets.models import ( Target, TargetExtra, TargetName )
from tom_targets.forms import extra_field_to_form_field, TargetForm

class MulensTargetForm(TargetForm):

    def __init__(self, *args, **kwargs):
        super(TargetForm,self).__init__(*args, **kwargs)
        use_keys = [ 'name', 'ra', 'dec', 't0', 'u0', 'tE', 'rho', 'Ibase', 'Ilatest', 'last_updated', 'groups']
        field_list = self.fields.copy()

        for field in field_list:
            if field not in use_keys:
                self.fields.pop(field)

        self.extra_fields = {}
        for extra_field in settings.EXTRA_FIELDS:
            if extra_field['name'] in use_keys:
                # Add extra fields to the form
                field_name = extra_field['name']
                self.extra_fields[field_name] = extra_field_to_form_field(extra_field['type'])
                # Populate them with initial values if this is an update
                if kwargs['instance']:
                    te = TargetExtra.objects.filter(target=kwargs['instance'], key=field_name)
                    if te.exists():
                        self.extra_fields[field_name].initial = te.first().typed_value(extra_field['type'])

        self.fields.update(self.extra_fields)
        
