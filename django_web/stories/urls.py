from django.urls import path
from . import views

urlpatterns = [
    path("api-test/", views.api_test),

    path("stories/", views.story_list, name="story_list"),
    path("play/<int:story_id>/", views.play_story, name="play_story"),
    path("play/<int:story_id>/<int:page_id>/", views.play_story, name="play_story"),
    
    path("stats/", views.stats, name="stats"),
    
    path("author/", views.author_stories, name="author_stories"),
    path("author/story/<int:story_id>/preview/", views.preview_story, name="preview_story"),
    path("author/story/<int:story_id>/delete/", views.delete_story, name="delete_story"),
    
    path("register/", views.register, name="register"),

    path("stories/<int:story_id>/status/", views.toggle_story_status, name="toggle_story_status"),
]
