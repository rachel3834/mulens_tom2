from django import forms
from django.forms import ValidationError, inlineformset_factory
from django.conf import settings
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm, get_groups_with_perms, remove_perm

from tom_targets.models import ( Target, TargetExtra, TargetName )
from tom_targets.forms import extra_field_to_form_field

class MulensTargetForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(Group.objects.none(), required=False, widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_fields = {}
        use_fields = []
        for extra_field in settings.EXTRA_FIELDS:
            if extra_field['name'] in ['t0', 'u0', 'tE', 'rho', 'Ibase', 'Ilatest', 'last_updated']:
                use_fields.append( extra_field )

        for extra_field in use_fields:
            # Add extra fields to the form
            field_name = extra_field['name']
            self.extra_fields[field_name] = extra_field_to_form_field(extra_field['type'])
            # Populate them with initial values if this is an update
            if kwargs['instance']:
                te = TargetExtra.objects.filter(target=kwargs['instance'], key=field_name)
                if te.exists():
                    self.extra_fields[field_name].initial = te.first().typed_value(extra_field['type'])

            self.fields.update(self.extra_fields)

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            for field in settings.EXTRA_FIELDS:
                if self.cleaned_data.get(field['name']) is not None:

                    TargetExtra.objects.update_or_create(
                            target=instance,
                            key=field['name'],
                            defaults={'value': self.cleaned_data[field['name']]}
                    )
            # Save groups for this target
            for group in self.cleaned_data['groups']:
                assign_perm('tom_targets.view_target', group, instance)
                assign_perm('tom_targets.change_target', group, instance)
                assign_perm('tom_targets.delete_target', group, instance)
            for group in get_groups_with_perms(instance):
                if group not in self.cleaned_data['groups']:
                    remove_perm('tom_targets.view_target', group, instance)
                    remove_perm('tom_targets.change_target', group, instance)
                    remove_perm('tom_targets.delete_target', group, instance)

        return instance

    class Meta:
        abstract = True
        model = Target
        fields = [ 'name', 'type', 'ra', 'dec' ]
        widgets = {'type': forms.HiddenInput()}

TargetNamesFormset = inlineformset_factory(Target, TargetName, fields=('name',), validate_min=False, can_delete=True,
                                           extra=3)
