from django import template
from django.conf import settings
from dateutil.parser import parse
from plotly import offline
import plotly.graph_objs as go
from astropy import units as u
from astropy.coordinates import Angle

from tom_targets.models import Target, TargetExtra, TargetList
from tom_targets.forms import TargetVisibilityForm
from tom_observations.utils import get_sidereal_visibility

register = template.Library()

@register.inclusion_tag('tom_targets/partials/target_data.html')
def target_parameters(target):
    """
    Displays the data of a target.
    """
    return {
        'target': target,
        'display_extras': [ex['name'] for ex in settings.EXTRA_FIELDS if not ex.get('hidden')]
    }
