from django.urls import path
from . import views

urlpatterns = [
    path("api-test/", views.api_test),
    path("", views.story_list, name="story_list"),
    path("play/<int:story_id>/", views.play_story, name="play_story"),
    path("play/<int:story_id>/<int:page_id>/", views.play_story, name="play_story"),
    path("stats/", views.stats, name="stats"),
]
