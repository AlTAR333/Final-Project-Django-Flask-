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
        "start_page_id": story.start_page_id,
        "owner_username": story.owner_username
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

@api.route("/stories/<int:story_id>/pages", methods=["GET"])
def get_story_pages(story_id):
    pages = Page.query.filter_by(story_id=story_id).order_by(Page.id).all()

    result = []

    page_number_map = {p.id: i+1 for i, p in enumerate(pages)}

    for index, p in enumerate(pages, start=1):
        result.append({
            "id": p.id,
            "number": index,
            "text": p.text,
            "is_ending": p.is_ending,
            "ending_label": p.ending_label,
            "choices": [
                {
                    "id": c.id,
                    "text": c.text,
                    "next_page_id": c.next_page_id,
                    "next_page_number": page_number_map.get(c.next_page_id)
                }
                for c in p.choices
            ]
        })

    return jsonify(result)

@api.route("/stories/<int:story_id>/pages", methods=["POST"])
def create_page(story_id):
    data = request.get_json()

    page = Page(
        story_id=story_id,
        text=data.get("text"),
        is_ending=data.get("is_ending", False),
        ending_label=data.get("ending_label")
    )

    db.session.add(page)
    db.session.commit()

    return jsonify({"message": "Page created", "id": page.id}), 201

@api.route("/pages/<int:page_id>", methods=["PATCH"])
def update_page(page_id):
    data = request.get_json()
    page = Page.query.get_or_404(page_id)

    if "text" in data:
        page.text = data["text"]

    if "is_ending" in data:
        page.is_ending = data["is_ending"]

        if page.is_ending:
            for choice in page.choices:
                db.session.delete(choice)

    if "ending_label" in data:
        page.ending_label = data["ending_label"]

    db.session.commit()
    return jsonify({"message": "Page updated"})


@api.route("/pages/<int:page_id>/choices", methods=["POST"])
def create_choice(page_id):
    data = request.get_json()
    page = Page.query.get_or_404(page_id)

    if page.is_ending:
        return jsonify({"error": "Cannot add choices to an ending page"}), 400

    choice = Choice(
        page_id=page_id,
        text=data.get("text", ""),
        next_page_id=data.get("next_page_id")
    )

    db.session.add(choice)
    db.session.commit()

    return jsonify({"message": "Choice added", "choice_id": choice.id})

@api.route("/choices/<int:choice_id>", methods=["PATCH"])
def update_choice(choice_id):
    data = request.get_json()

    choice = Choice.query.get_or_404(choice_id)

    choice.text = data.get("text", choice.text)
    choice.next_page_id = data.get("next_page_id", choice.next_page_id)

    db.session.commit()

    return jsonify({"message": "Choice updated"})

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

@api.route("/choices/<int:choice_id>", methods=["DELETE"])
def delete_choice(choice_id):
    choice = Choice.query.get_or_404(choice_id)

    db.session.delete(choice)
    db.session.commit()

    return jsonify({"message": "Choice deleted"})

@api.route("/pages/<int:page_id>", methods=["DELETE"])
def delete_page(page_id):
    page = Page.query.get_or_404(page_id)

    incoming_choices = Choice.query.filter_by(next_page_id=page_id).all()
    for choice in incoming_choices:
        db.session.delete(choice)

    for choice in page.choices:
        db.session.delete(choice)

    db.session.delete(page)
    db.session.commit()

    return jsonify({"message": "Page deleted"})

@api.route("/stories", methods=["POST"])
def create_story():
    data = request.get_json() or {}

    title = data.get("title", "Untitled Story")
    author = data.get("author")

    if not author:
        return jsonify({"error": "Author is required"}), 400

    new_story = Story(title=title, owner_username=author, status="draft")

    db.session.add(new_story)
    db.session.commit()

    first_page = Page(story_id=new_story.id, text="Start writing your story here...", is_ending=False)

    db.session.add(first_page)
    db.session.commit()
    new_story.start_page_id = first_page.id
    db.session.commit()

    return jsonify({
        "message": "Story created",
        "story_id": new_story.id
    }), 201

@api.route("/stories/<int:story_id>", methods=["DELETE"])
def delete_story(story_id):
    story = Story.query.get_or_404(story_id)
    for page in story.pages:
        page_choices = Choice.query.filter_by(page_id=page.id).all()
        for choice in page_choices:
            db.session.delete(choice)
        incoming_choices = Choice.query.filter_by(next_page_id=page.id).all()
        for choice in incoming_choices:
            db.session.delete(choice)
        db.session.delete(page)

    db.session.delete(story)
    db.session.commit()

    return jsonify({"message": "Story deleted"}), 200

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
