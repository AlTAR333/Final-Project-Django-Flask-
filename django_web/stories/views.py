from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import requests
from .models import Play, PlaySession, Story
from django.db.models import Count, F
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

FLASK_API_URL = "http://127.0.0.1:5000"

def api_test(request):
    """
    Test api status
    """
    r = requests.get(f"{FLASK_API_URL}/ping")
    return JsonResponse(r.json())

def is_author(user):
    """
    Check if user is author
    """
    return user.groups.filter(name="Author").exists() or user.is_staff

@login_required
def author_stories(request):
    """
    List stories per author
    """
    response = requests.get(f"{FLASK_API_URL}/stories",params={"owner": request.user.username})
    return render(
        request,
        "gameplay/author_stories.html",
        {"stories": response.json()}
    )

@login_required
def delete_story(request, story_id):
    """
    Delete a story (if user is owner)
    """
    story = requests.get(f"{FLASK_API_URL}/stories/{story_id}").json()
    
    # check ownership (DONE)
    if story.get("owner_username") != str(request.user) and not request.user.is_staff:
        messages.error(request, "You are not allowed to delete this story")
        return redirect("author_stories")

    if request.method == "POST":
        requests.delete(f"{FLASK_API_URL}/stories/{story_id}")
        messages.success(request, "Story deleted")
        return redirect("author_stories")
    
    return render(request, "gameplay/confirm_delete.html", {"story": story})

@login_required
def story_list(request):
    """
    List all the published stories
    """
    query = request.GET.get("q", "")
    response = requests.get(f"{FLASK_API_URL}/stories", params={"status": "published"})
    stories = response.json()
    if query:
        stories = [s for s in stories if query.lower() in s["title"].lower()]

    return render(request, "gameplay/story_list.html", {"stories": stories, "query": query})

@login_required
def play_story(request, story_id, page_id=None):
    """
    Play a story.
    - Creates a PlaySession if none exists
    - Calls Flask API to get page + choices
    """
    # Get / create the session
    ps, created = PlaySession.objects.get_or_create(
        user=request.user, story_id=story_id, ended_at__isnull=True,
        defaults={"started_at": timezone.now()}
    )

    # Determine current page
    if page_id is None and ps.current_page_id:
        page_id = ps.current_page_id
    elif page_id is None:
        resp = requests.get(f"{FLASK_API_URL}/stories/{story_id}/start")
        if resp.status_code != 200:
            return render(request, "gameplay/error.html", {"message": "Story has no start page"})
        page = resp.json()
        page_id = page["id"]

    # Call the Flask API for current page
    resp = requests.get(f"{FLASK_API_URL}/pages/{page_id}")
    if resp.status_code != 200:
        return render(request, "gameplay/error.html", {"message": "Page not found"})
    page = resp.json()

    # PlaySession upadte
    ps.current_page_id = page["id"]
    if page["is_ending"]:
        ps.ended_at = timezone.now()
        Play.objects.create(user=request.user, story_id=story_id, ending_page_id=page["id"])
    ps.save()

    return render(request, "gameplay/play_page.html", {"page": page})

@login_required
def stats(request):
    """
    Return the stats per Story
    """
    user = request.user
    story_ids = (PlaySession.objects.filter(user=user).values_list("story_id", flat=True).distinct())

    stats_data = {}

    for story_id in story_ids:
        # Fetch ending labels from Flask
        endings_response = requests.get(f"{FLASK_API_URL}/stories/{story_id}/endings")
        ending_labels = {e["id"]: e["label"] for e in endings_response.json()}
        started_count = PlaySession.objects.filter(user=user, story_id=story_id).count()
        finished_count = Play.objects.filter(user=user, story_id=story_id).count()

        endings_qs = (Play.objects.filter(user=user, story_id=story_id).values("ending_page_id").annotate(count=Count("id")))
        endings = {}

        for e in endings_qs:
            percentage = round((e["count"] / finished_count) * 100, 1) if finished_count else 0
            endings[e["ending_page_id"]] = {"label": ending_labels.get(e["ending_page_id"], f"Ending {e['ending_page_id']}"), "count": e["count"], "percentage": percentage,}

        stats_data[story_id] = {"started": started_count, "finished": finished_count, "endings": endings,}

    if story_ids:
        response = requests.get(f"{FLASK_API_URL}/stories")
        flask_stories = response.json()
        for s in flask_stories:
            if s["id"] in stats_data:
                stats_data[s["id"]]["title"] = s["title"]

    return render(request, "gameplay/stats.html", {"stats": stats_data})

@login_required
def preview_story(request, story_id):
    """
    Play a draft story without saving stats
    """
    response = requests.get(f"{FLASK_API_URL}/stories/{story_id}/start")
    page = response.json()

    request.session[f"preview_{story_id}"] = page["id"]

    return render(request, "gameplay/play_page.html", {"page": page, "preview": True})

def register(request):
    """
    Register a new user
    """
    if request.user.is_authenticated:
        return redirect("story_list")

    if request.method == "POST":
        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            User.objects.create_user(username=username, password=password1)
            messages.success(request, "Account created. You can now log in.")
            return redirect("login")

    return render(request, "gameplay/register.html")

def login_view(request):
    """
    Login
    """
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("story_list")
    else:
        form = AuthenticationForm()
    return render(request, "gameplay/login.html", {"form": form})

def logout_view(request):
    """
    Logout (Django)
    """
    logout(request)
    return redirect("story_list")

@login_required
def toggle_story_status(request, story_id):
    if request.method == "POST":
        new_status = request.POST.get("status")

        response = requests.patch(
            f"{FLASK_API_URL}/stories/{story_id}/status",
            json={"status": new_status, "username": request.user.username}
            )

        print("Flask response:", response.status_code, response.text)

    return redirect("author_stories")

@login_required
def edit_story(request, story_id):
    story = requests.get(f"{FLASK_API_URL}/stories/{story_id}").json()
    pages = requests.get(f"{FLASK_API_URL}/stories/{story_id}/pages").json()

    return render(request, "gameplay/edit_story.html", {"story": story, "pages": pages})

@login_required
def create_page(request, story_id):
    if request.method == "POST":
        text = request.POST.get("text")

        requests.post(f"{FLASK_API_URL}/stories/{story_id}/pages", json={"text": text})

    return redirect("edit_story", story_id=story_id)

@login_required
def update_page(request, page_id, story_id):
    if request.method == "POST":
        text = request.POST.get("text")

        requests.patch(f"{FLASK_API_URL}/pages/{page_id}", json={"text": text})

    return redirect("edit_story", story_id=story_id)

@login_required
def create_choice(request, story_id, page_id):
    if request.method == "POST":
        text = request.POST.get("text")
        next_page_id = request.POST.get("next_page_id")

        requests.post(f"{FLASK_API_URL}/pages/{page_id}/choices", json={"text": text, "next_page_id": int(next_page_id)})

    return redirect("edit_story", story_id=story_id)

@login_required
def toggle_ending(request, page_id, story_id):
    if request.method == "POST":
        is_ending = request.POST.get("is_ending") == "true"
        ending_label = request.POST.get("ending_label", "")

        requests.patch(
            f"{FLASK_API_URL}/pages/{page_id}",
            json={"is_ending": is_ending, "ending_label": ending_label}
        )

    return redirect("edit_story", story_id=story_id)

@login_required
def delete_choice(request, story_id, choice_id):
    if request.method == "POST":
        requests.delete(f"{FLASK_API_URL}/choices/{choice_id}")

    return redirect("edit_story", story_id=story_id)

@login_required
def delete_page(request, story_id, page_id):
    if request.method == "POST":
        requests.delete(f"{FLASK_API_URL}/pages/{page_id}")

    return redirect("edit_story", story_id=story_id)

@login_required
def create_story(request):
    if request.method == "POST":
        title = request.POST.get("title")
        response = requests.post(f"{FLASK_API_URL}/stories", json={"title": title, "author": request.user.username})
        story_id = response.json()["story_id"]
        return redirect("edit_story", story_id=story_id)

    return redirect("author_stories")

@login_required
def confirm_delete(request, story_id):
    if request.method == "POST":
        requests.delete(f"{FLASK_API_URL}/stories/{story_id}")
        return redirect("author_stories")

    return render(request, "stories/confirm_delete.html")
