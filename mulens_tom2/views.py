from django.shortcuts import render
from django import template
from tom_observations.models import ObservationRecord
from tom_targets.models import TargetList
from datetime import datetime

from django.conf import settings
from django_filters.views import FilterView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormView
from guardian.mixins import PermissionRequiredMixin, PermissionListMixin
from guardian.shortcuts import get_objects_for_user, get_groups_with_perms, assign_perm
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from tom_targets.forms import (
    SiderealTargetCreateForm, NonSiderealTargetCreateForm, TargetExtraFormset, TargetNamesFormset
)
from tom_targets.models import Target, TargetList
from tom_targets.filters import TargetFilter
from tom_targets.views import TargetCreateView
from tom_targets.forms import TargetExtraFormset, TargetNamesFormset
from tom_observations.views import ManualObservationCreateView
from .forms import MulensTargetForm, CustomImagingObservationForm

from .lco_facility import LCOInstruments

register = template.Library()

class UserProjectDashboard(LoginRequiredMixin, FilterView):
    template_name = 'mulens_tom2/project_dashboard.html'
    permission_required = 'tom_targets.view_target'
    model = TargetList

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        if self.request.user.is_authenticated:
            context['groupings'] = TargetList.objects.all()
            context['message'] = ''
            for tl in context['groupings']:
                tl.image_path = 'img/'+tl.name+'_targetlist_img.png'
        else:
            context['groupings'] = []
            context['message'] = 'Please login to see your Projects'
        return context

class TargetGroupsView(LoginRequiredMixin, FilterView):
    template_name = 'tom_targets/target_groups.html'
    permission_required = 'tom_targets.view_target'
    model = TargetList

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # hide target grouping list if user not logged in
        if self.request.user.is_authenticated:
            context['groupings'] = TargetList.objects.all()
            context['message'] = 'Got targetlists'
        else:
            context['groupings'] = TargetList.objects.none()
            context['message'] = 'Please login to see your Projects'

        return context

class MulensTargetListView(PermissionListMixin, FilterView):
    template_name = 'tom_targets/target_list.html'
    paginate_by = 25
    strict = False
    model = Target
    filterset_class = TargetFilter
    permission_required = 'tom_targets.view_target'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['target_count'] = context['paginator'].count
        # hide target grouping list if user not logged in
        context['groupings'] = (TargetList.objects.all()
                                if self.request.user.is_authenticated
                                else TargetList.objects.none())
        context['query_string'] = self.request.META['QUERY_STRING']
        return context

class MulensTargetCreateView(TargetCreateView):
    """
    View for creating a Target
    """

    model = Target

    def get_context_data(self, **kwargs):
        """
        Inserts certain form data into the context dict.

        :returns: Dictionary with the following keys:

                  `type_choices`: ``tuple``: Tuple of 2-tuples of strings containing available target types in the TOM

                  `extra_form`: ``FormSet``: Django formset with fields for arbitrary key/value pairs
        """
        context = super(MulensTargetCreateView, self).get_context_data(**kwargs)
        context['type_choices'] = Target.TARGET_TYPES
        context['names_form'] = TargetNamesFormset(initial=[{'name': new_name}
                                                            for new_name
                                                            in self.request.GET.get('names', '').split(',')])
        context['extra_form'] = TargetExtraFormset()
        return context

class MulensTargetUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = 'tom_targets.change_target'
    model = Target
    fields = '__all__'

    def get_context_data(self, **kwargs):
        extra_field_names = [extra['name'] for extra in settings.EXTRA_FIELDS]
        context = super().get_context_data(**kwargs)
        context['names_form'] = TargetNamesFormset(instance=self.object)
        context['extra_form'] = TargetExtraFormset(
            instance=self.object,
            queryset=self.object.targetextra_set.exclude(key__in=extra_field_names)
        )
        return context

    def form_valid(self, form):
        super().form_valid(form)
        extra = TargetExtraFormset(self.request.POST, instance=self.object)
        names = TargetNamesFormset(self.request.POST, instance=self.object)
        if extra.is_valid() and names.is_valid():
            extra.save()
            names.save()
        else:
            form.add_error(None, extra.errors)
            form.add_error(None, extra.non_form_errors())
            form.add_error(None, names.errors)
            form.add_error(None, names.non_form_errors())
            return super().form_invalid(form)
        return redirect(self.get_success_url())

    def get_queryset(self, *args, **kwargs):
        return get_objects_for_user(self.request.user, 'tom_targets.change_target')

    def get_form_class(self):
        if self.object.type == Target.SIDEREAL:
            return SiderealTargetCreateForm
        elif self.object.type == Target.NON_SIDEREAL:
            return NonSiderealTargetCreateForm

    def get_initial(self):
        initial = super().get_initial()
        initial['groups'] = get_groups_with_perms(self.get_object())
        return initial

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        if self.request.user.is_superuser:
            form.fields['groups'].queryset = Group.objects.all()
        else:
            form.fields['groups'].queryset = self.request.user.groups.all()
        return form

class ImagingObservationRequestView(LoginRequiredMixin, FormView):
    template_name = 'tom_observations/imaging_observation_request.html'
    form_class = CustomImagingObservationForm

    def get_target(self, form):
        print(form.cleaned_data)
        return Target.objects.filter(id=form.cleaned_data['target_id'])

    def form_valid(self, form):
        """
        Runs after form validation. Creates a new ``ObservationRecord`` associated with the specified target and
        facility.
        """
        ObservationRecord.objects.create(
            target=self.get_target(form),
            facility=form.cleaned_data['facility'],
            parameters={},
            observation_id=form.cleaned_data['observation_id']
        )
        return redirect(reverse(
            'tom_targets:detail', kwargs={'pk': self.get_target(form).id})
        )

    def get_context_data(self):
        context = {}

        qs = Target.objects.all()
        targets = []
        for entry in qs:
            targets.append( (entry.pk, entry.name) )
        context['target_list'] = tuple(targets)

        lcoinstruments = LCOInstruments()
        context['instrument_list'] = lcoinstruments.get_imagers_tuple()
        context['filter_list'] = lcoinstruments.get_filter_choices()

        return context
