from flask import Blueprint, jsonify, request, abort
from app.models import Story, Page, Choice

api = Blueprint("api", __name__)

API_KEY = "SECRET_KEY"

def require_api_key(func):
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-KEY")
        if key != API_KEY:
            abort(401, description="Invalid API Key")
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@api.route("/ping")
def ping():
    return jsonify({"status": "ok", "service": "flask_api"})

@api.route("/stories", methods=["GET"])
def list_stories():
    status = request.args.get("status")
    owner = request.args.get("owner")
    query = Story.query
    if status:
        query = query.filter_by(status=status)
    if owner:
        query = query.filter_by(owner_username=owner)
    stories = query.all()

    return jsonify([{
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "status": s.status,
            "owner_username": s.owner_username
        }
        for s in stories
    ])

@api.route("/stories/<int:story_id>", methods=["GET"])
def get_story(story_id):
    story = Story.query.get_or_404(story_id)

    return jsonify({
        "id": story.id,
        "title": story.title,
        "description": story.description,
        "status": story.status,
        "start_page_id": story.start_page_id
    })


@api.route("/stories/<int:story_id>/start", methods=["GET"])
def get_story_start(story_id):
    story = Story.query.get_or_404(story_id)

    if not story.start_page_id:
        abort(404, description="Story has no start page")

    page = Page.query.get_or_404(story.start_page_id)
    return _serialize_page(page)


@api.route("/pages/<int:page_id>", methods=["GET"])
def get_page(page_id):
    page = Page.query.get_or_404(page_id)
    return _serialize_page(page)


def _serialize_page(page):
    return jsonify({
        "id": page.id,
        "story_id": page.story_id,
        "text": page.text,
        "is_ending": page.is_ending,
        "ending_label": page.ending_label,
        "choices": [{
                "id": c.id,
                "text": c.text,
                "next_page_id": c.next_page_id
            }
            for c in page.choices
    ]})