from django.db import models

class Play(models.Model):
    story_id = models.IntegerField()
    ending_page_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Play story {self.story_id} -> ending {self.ending_page_id}"

class PlaySession(models.Model):
    story_id = models.IntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)  # set when story ends

    def is_finished(self):
        return self.ended_at is not None