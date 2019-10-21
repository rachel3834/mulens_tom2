from django.shortcuts import render
from django import template
from tom_observations.models import ObservationRecord
from tom_targets.models import TargetList
from datetime import datetime
from django_filters.views import FilterView

from guardian.mixins import PermissionRequiredMixin, PermissionListMixin
from django.contrib.auth.mixins import LoginRequiredMixin

register = template.Library()

class UserGroupsView(LoginRequiredMixin):
    template_name = 'mulens_tom/user_groups.html'

class TargetGroupsView(LoginRequiredMixin, FilterView):
    template_name = 'mulens_tom/target_groups.html'
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
