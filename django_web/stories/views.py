from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
import requests
from .models import Play, PlaySession
from django.db.models import Count
from django.utils import timezone

FLASK_API_URL = "http://127.0.0.1:5000"

def home(request):
    return HttpResponse("NAHB – Django Web App OK")

def api_test(request):
    r = requests.get(f"{FLASK_API_URL}/ping")
    return JsonResponse(r.json())

def story_list(request):
    response = requests.get(f"{FLASK_API_URL}/stories?status=published")
    stories = response.json()
    return render(request, "gameplay/story_list.html", {"stories": stories})

def play_story(request, story_id, page_id=None):
    if page_id is None:
        response = requests.get(f"{FLASK_API_URL}/stories/{story_id}/start")
    else:
        response = requests.get(f"{FLASK_API_URL}/pages/{page_id}")

    page = response.json()

    # track session
    session_id = request.session.get(f"play_{story_id}")
    if not session_id:
        # start a new session
        ps = PlaySession.objects.create(story_id=story_id)
        request.session[f"play_{story_id}"] = ps.id
    else:
        ps = PlaySession.objects.get(id=session_id)

    if page["is_ending"]:
        # mark when session finished
        ps.ended_at = timezone.now()
        ps.save()

        # save Play
        Play.objects.create(story_id=story_id, ending_page_id=page["id"])

        # clears session
        del request.session[f"play_{story_id}"]

    return render(request, "gameplay/play_page.html", {"page": page})

def stats(request):
    # count all number of starts
    starts = PlaySession.objects.values("story_id").annotate(count=Count("id"))
    starts_dict = {s["story_id"]: s["count"] for s in starts}

    # count all number of finishes
    finishes = Play.objects.values("story_id").annotate(count=Count("id"))
    finishes_dict = {f["story_id"]: f["count"] for f in finishes}

    # combine both
    story_ids = set(list(starts_dict.keys()) + list(finishes_dict.keys()))
    stats_dict = {}
    for sid in story_ids:
        stats_dict[sid] = {
            "started": starts_dict.get(sid, 0),
            "finished": finishes_dict.get(sid, 0)
        }

    return render(request, "gameplay/stats.html", {"stats": stats_dict})