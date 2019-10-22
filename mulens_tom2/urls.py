"""django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include

from .views import TargetGroupsView, MulensTargetCreateView, MulensTargetListView

app_name = 'mulens_tom2'

urlpatterns = [
    path('', include('tom_common.urls')),
    path('', TargetGroupsView.as_view(template_name='mulens_tom2/target_groups.html'), name='target_groups'),
    path('create/', MulensTargetCreateView.as_view(template_name='tom_targets/target_form.html'), name='create_mulens'),
    path('targetlist/', MulensTargetListView.as_view(template_name='tom_targets/target_list.html'), name='targetlist'),
]
