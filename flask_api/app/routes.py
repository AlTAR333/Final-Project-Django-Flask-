from flask import Blueprint, jsonify, request, abort
from app.models import Story, Page, Choice
from app import db

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
    print("Story class id:", id(Story))
    status = request.args.get("status")
    owner = request.args.get("owner")
    query = Story.query
    if status:
        query = query.filter_by(status=status)
    if owner:
        query = query.filter_by(owner_username=owner)
    stories = query.all()

    for s in stories:
        print("Returning story:", s.id, s.status)

    import os
    print("DB path:", os.path.abspath("app.db"))

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

@api.route("/stories/<int:story_id>/endings", methods=["GET"])
def get_story_endings(story_id):
    pages = Page.query.filter_by(story_id=story_id, is_ending=True).all()
    
    return jsonify([{"id": p.id, "label": p.ending_label} for p in pages])

@api.route("/pages/<int:page_id>", methods=["GET"])
def get_page(page_id):
    page = Page.query.get_or_404(page_id)
    return _serialize_page(page)

@api.route("/stories/<int:story_id>/status", methods=["PATCH"])
def update_story_status(story_id):
    print("Story class id:", id(Story))
    data = request.get_json()
    new_status = data.get("status")
    username = data.get("username")

    if new_status not in ["draft", "published"]:
        return jsonify({"error": "Invalid status"}), 400

    story = Story.query.get_or_404(story_id)

    if story.owner_username != username:
        return jsonify({"error": "Unauthorized"}), 403

    print("Before change:", story.status)
    story.status = new_status
    print("Assigned:", story.status)
    db.session.commit()
    print("After commit:", story.status)

    print("Story owner:", story.owner_username)
    print("Username from request:", username)

    import os
    print("DB path:", os.path.abspath("app.db"))


    return jsonify({"message": "Status updated"})


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