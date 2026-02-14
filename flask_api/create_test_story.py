# Generated with Chat-GPT

from app import create_app, db
from app.models import Story, Page, Choice

app = create_app()
app.app_context().push()

# Delete old test story if exists
Story.query.filter_by(title="Test Story").delete()
db.session.commit()

# Create story
story = Story(title="Test Story", description="A simple test story with multiple branches", status="published")
db.session.add(story)
db.session.commit()

# Start page
start_page = Page(story_id=story.id, text="You wake up in a dark forest. Two paths lie ahead.", is_ending=False)
db.session.add(start_page)
db.session.commit()
story.start_page_id = start_page.id
db.session.commit()

# Left path
left_page = Page(story_id=story.id, text="You took the left path and find a treasure chest.", is_ending=True, ending_label="Treasure")
db.session.add(left_page)

# Right path
right_page = Page(story_id=story.id, text="You took the right path and encounter a sleeping dragon.", is_ending=False)
db.session.add(right_page)
db.session.commit()

# Right path -> sneak past dragon
sneak_page = Page(story_id=story.id, text="You sneak past the dragon and escape the forest safely.", is_ending=True, ending_label="Escape")
db.session.add(sneak_page)

# Right path -> wake dragon
wake_page = Page(story_id=story.id, text="You accidentally wake the dragon. It chases you away!", is_ending=True, ending_label="Dragon Attack")
db.session.add(wake_page)
db.session.commit()

# Start page choices
c1 = Choice(page_id=start_page.id, text="Take the left path", next_page_id=left_page.id)
c2 = Choice(page_id=start_page.id, text="Take the right path", next_page_id=right_page.id)
db.session.add_all([c1, c2])

# Right path choices
c3 = Choice(page_id=right_page.id, text="Sneak past the dragon", next_page_id=sneak_page.id)
c4 = Choice(page_id=right_page.id, text="Wake the dragon", next_page_id=wake_page.id)
db.session.add_all([c3, c4])

db.session.commit()

print("Test Story created with multiple branches!")
