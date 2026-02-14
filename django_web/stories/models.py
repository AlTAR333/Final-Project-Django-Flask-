from django.db import models
from django.contrib.auth.models import User

class Play(models.Model):
    story_id = models.IntegerField()
    ending_page_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Play story {self.story_id} -> ending {self.ending_page_id} (User: {self.user.username})"


class PlaySession(models.Model):
    story_id = models.IntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)  # set when story ends
    current_page_id = models.IntegerField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def is_finished(self):
        return self.ended_at is not None
    
class Story(models.Model):
    title = models.CharField(max_length=200)
    tags = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=[("draft", "Draft"), ("published", "Published")], default="DRAFT")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stories")
