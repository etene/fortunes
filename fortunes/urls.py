"""
URL configuration for fortunes project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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

from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from fortunes.app import views

urlpatterns = [
    path(
        route="",
        view=RedirectView.as_view(pattern_name="random-fortune"),
    ),
    path(
        route="admin/",
        view=admin.site.urls,
    ),
    path(
        route="random/",
        view=views.random_fortune,
        name="random-fortune",
    ),
    path(
        route="random_image/<int:fortune_id>/",
        view=views.random_image,
        name="random-image",
    ),
    path(
        route="browse/",
        view=views.fortune_list,
        name="fortune-list",
    ),
    path(
        route="trashcan/",
        view=views.fortune_trashcan,
        name="fortune-trashcan",
    ),
    path(
        route="new/",
        view=views.new_fortune,
        name="new-fortune",
    ),
    path(
        route="<int:fortune_id>/",
        view=views.single_fortune,
        name="fortune-detail",
    ),
    path(
        route="<int:fortune_id>/edit/",
        view=views.edit_fortune,
        name="fortune-edit",
    ),
    path(
        route="<int:fortune_id>/delete/",
        view=views.delete_fortune,
        name="fortune-delete",
    ),
]
