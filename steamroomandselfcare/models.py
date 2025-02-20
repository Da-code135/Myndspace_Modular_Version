from django.db import models
from users.models import User
from textblob import TextBlob  

class ThoughtLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='thought_logs')
    content = models.TextField(help_text="Enter your thought log here.")
    sentiment = models.FloatField(blank=True, null=True, help_text="Sentiment polarity score.")
    created_at = models.DateTimeField(auto_now_add=True)

    def analyze_sentiment(self):
        """
        Analyze the content and return a sentiment polarity score.
        Range is typically -1 (negative) to +1 (positive).
        """
        blob = TextBlob(self.content)
        return blob.sentiment.polarity

    def save(self, *args, **kwargs):
        # Automatically calculate sentiment before saving
        self.sentiment = self.analyze_sentiment()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"ThoughtLog by {self.user.username} on {self.created_at.strftime('%Y-%m-%d')}"
