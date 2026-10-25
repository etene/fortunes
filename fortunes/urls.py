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
import fortunes.app.views.fortune
import fortunes.app.views.author

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
        view=fortunes.app.views.fortune.random_fortune,
        name="random-fortune",
    ),
    path(
        route="random_image/<int:fortune_id>/",
        view=fortunes.app.views.fortune.random_image,
        name="random-image",
    ),
    path(
        route="browse/",
        view=fortunes.app.views.fortune.FortuneListView.as_view(),
        name="fortune-list",
    ),
    path(
        route="trashcan/",
        view=fortunes.app.views.fortune.FortuneTrashcanView.as_view(),
        name="fortune-trashcan",
    ),
    path(
        route="new/",
        view=fortunes.app.views.fortune.FortuneCreateFormView.as_view(),
        name="new-fortune",
    ),
    path(
        route="<int:fortune_id>/",
        view=fortunes.app.views.fortune.single_fortune,
        name="fortune-detail",
    ),
    path(
        route="<int:pk>/edit/",
        view=fortunes.app.views.fortune.FortuneEditFormView.as_view(),
        name="fortune-edit",
    ),
    path(
        route="<int:fortune_id>/delete/",
        view=fortunes.app.views.fortune.delete_fortune,
        name="fortune-delete",
    ),
    path(
        route="export/",
        view=fortunes.app.views.fortune.fortune_export,
        name="fortune-export",
    ),
    path(
        route="author/<int:pk>/edit/",
        view=fortunes.app.views.author.AuthorEditFormView.as_view(),
        name="author-edit",
    ),
    path(
        route="author/new/",
        view=fortunes.app.views.author.AuthorCreateFormView.as_view(),
        name="author-create",
    ),
    path(
        route="author/<int:pk>/thumbnail/",
        view=fortunes.app.views.author.author_thumbnail,
        name="author-thumbnail",
    ),
    path(
        route="author/<int:pk>/delete/",
        view=fortunes.app.views.author.AuthorDeleteView.as_view(),
        name="author-delete",
    ),
    path(
        route="<int:fortune_id>/toggle_hidden/",
        view=fortunes.app.views.fortune.ToggleHiddenFortuneView.as_view(),
        name="fortune-toggle-hidden",
    ),
]
