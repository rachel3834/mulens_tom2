from django.shortcuts import render
from django import template
from tom_observations.models import ObservationRecord
from tom_targets.models import TargetList
from datetime import datetime

from django.conf import settings
from django_filters.views import FilterView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from guardian.mixins import PermissionRequiredMixin, PermissionListMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group

from tom_targets.models import Target, TargetList
from tom_targets.filters import TargetFilter
from .forms import MulensTargetForm
from tom_targets.forms import (
    SiderealTargetCreateForm, TargetExtraFormset, TargetNamesFormset
)

register = template.Library()

class UserGroupsView(LoginRequiredMixin):
    template_name = 'mulens_tom2/user_groups.html'

class TargetGroupsView(LoginRequiredMixin, FilterView):
    template_name = 'tom_targets/target_groups.html'
    permission_required = 'tom_targets.view_target'
    model = TargetList

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # hide target grouping list if user not logged in
        if self.request.user.is_authenticated:
            context['groupings'] = TargetList.objects.all()
        else:
            context['groupings'] = TargetList.objects.none()

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

class MulensTargetCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating a Target
    """

    model = Target
    fields = ['name', 'type', 'ra', 'dec']

    def get_default_target_type(self):
        """
        Returns the user-configured target type specified in settings.py, if it exists, otherwise returns sidereal

        :returns: User-configured target type or global default
        :rtype: str
        """
        return Target.SIDEREAL

    def get_target_type(self):
        obj = self.request.GET or self.request.POST
        target_type = obj.get('type')
        # If None or some invalid value, use default target type
        if target_type not in (Target.SIDEREAL, Target.NON_SIDEREAL):
            target_type = self.get_default_target_type()
        return target_type

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.

        :returns: Dictionary with the following keys:

                  `type`: ``str``: Type of the target to be created

                  `groups`: ``QuerySet<Group>`` Groups available to the current user

        :rtype: dict
        """
        return {
            'type': self.get_target_type(),
            'groups': self.request.user.groups.all(),
            **dict(self.request.GET.items())
        }

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

    def get_form_class(self):
        """
        Return the form class to use in this view.
        """
        target_type = self.get_target_type()
        self.initial['type'] = target_type
        return MulensTargetForm

    def form_valid(self, form):
        super().form_valid(form)
        extra = TargetExtraFormset(self.request.POST)
        names = TargetNamesFormset(self.request.POST)
        if extra.is_valid() and names.is_valid():
            extra.instance = self.object
            extra.save()
            names.instance = self.object
            names.save()
        else:
            form.add_error(None, extra.errors)
            form.add_error(None, extra.non_form_errors())
            form.add_error(None, names.errors)
            form.add_error(None, names.non_form_errors())
            return super().form_invalid(form)
        return redirect(self.get_success_url())

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        if self.request.user.is_superuser:
            form.fields['groups'].queryset = Group.objects.all()
        else:
            form.fields['groups'].queryset = self.request.user.groups.all()
        return form
