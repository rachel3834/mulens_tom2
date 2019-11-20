from django import forms
from django.forms import ValidationError, inlineformset_factory
from django.conf import settings
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm, get_groups_with_perms, remove_perm
from collections import OrderedDict
from crispy_forms.layout import Layout, Div

from tom_targets.models import ( Target, TargetExtra, TargetName )
from tom_targets.forms import extra_field_to_form_field, TargetForm
from tom_observations.facilities.lco import LCOBaseObservationForm
from .lco_facility import LCOInstruments

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


def get_targets():
    qs = Target.objects.all()
    targets = []
    for entry in qs:
        targets.append( (entry.pk, entry.name) )
    return tuple(targets)
    
class CustomImagingObservationForm(forms.Form):

    lcoinstruments = LCOInstruments()

    target_id = forms.ChoiceField(required=True, choices=get_targets())
    instrument = forms.ChoiceField(required=True, choices=lcoinstruments.get_imagers_tuple())

    exp1_filter = forms.ChoiceField(required=True, choices=lcoinstruments.get_filter_choices(),label='exp1_filter')
    exp1_nexp = forms.IntegerField(required=True, min_value=1,label='exp1_nexp')
    exp1_exptime = forms.IntegerField(required=True,label='exp1_exptime',min_value=0.0,max_value=1500.0)

    exp2_filter = forms.ChoiceField(choices=lcoinstruments.get_filter_choices(),label='exp2_filter')
    exp2_nexp = forms.IntegerField(min_value=1,label='exp2_nexp')
    exp2_exptime = forms.IntegerField(label='exp2_exptime',min_value=0.0,max_value=1500.0)

    exp3_filter = forms.ChoiceField(choices=lcoinstruments.get_filter_choices(),label='exp3_filter')
    exp3_nexp = forms.IntegerField(min_value=1,label='exp3_nexp')
    exp3_exptime = forms.IntegerField(label='exp3_exptime',min_value=0.0,max_value=1500.0)

    start_date = forms.DateTimeField(label='start_date',input_formats=["%Y-%m-%dT%H:%M:%S"])
    end_date = forms.DateTimeField(label='end_date',input_formats=["%Y-%m-%dT%H:%M:%S"])
    cadence = forms.FloatField(label='cadence')
    jitter = forms.FloatField(label='jitter')

    airmass = forms.FloatField(label='airmass')
    lunar_sep = forms.FloatField(label='lunar_sep')
    ipp = forms.FloatField(label='ipp')
