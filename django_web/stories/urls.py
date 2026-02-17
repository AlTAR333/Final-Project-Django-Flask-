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

    path("author/story/<int:story_id>/edit/", views.edit_story, name="edit_story"),

    path("author/story/<int:story_id>/create_page/", views.create_page, name="create_page"),
    path("author/story/<int:story_id>/page/<int:page_id>/update/", views.update_page, name="update_page"),
    path("author/story/<int:story_id>/page/<int:page_id>/delete/", views.delete_page, name="delete_page"),

    path("author/story/<int:story_id>/page/<int:page_id>/create_choice/", views.create_choice, name="create_choice"),
    path("author/story/<int:story_id>/choice/<int:choice_id>/delete/", views.delete_choice, name="delete_choice"),
    
    path("author/story/<int:story_id>/page/<int:page_id>/toggle-ending/", views.toggle_ending, name="toggle_ending"),
]
