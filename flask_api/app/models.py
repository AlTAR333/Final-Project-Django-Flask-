from . import db


class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="draft")  # draft/published/suspended
    start_page_id = db.Column(db.Integer, nullable=True)
    owner_username = db.Column(db.String(150))  # store Django username

    pages = db.relationship("Page", backref="story", lazy=True)

    def __repr__(self):
        return f"<Story {self.title}>"


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey("story.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_ending = db.Column(db.Boolean, default=False)
    ending_label = db.Column(db.String(100), nullable=True)

    choices = db.relationship("Choice", backref="page", lazy=True, foreign_keys="Choice.page_id")

    def __repr__(self):
        return f"<Page {self.id} (Story {self.story_id})>"

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey("page.id"), nullable=False)
    text = db.Column(db.String(200), nullable=False)
    next_page_id = db.Column(db.Integer, db.ForeignKey("page.id"), nullable=False)

    def __repr__(self):
        return f"<Choice {self.text}>"
