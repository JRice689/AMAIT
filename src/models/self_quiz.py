from django.db import models
from django.contrib.auth.models import User
from .study_guide import Study_Guide

class Self_Quiz(models.Model):

    question = models.TextField()
    choices = models.TextField()
    answer = models.TextField()
    reason = models.TextField()
    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT, default=None)
    instructor = models.CharField(max_length=50)
    date_created = models.DateTimeField(auto_now_add=True)
    is_flagged = models.BooleanField(default=False)
    from_study_guide = models.TextField()
    token_prompt = models.IntegerField()
    token_completion = models.IntegerField()
    token_total = models.IntegerField()

    

    def __str__(self) -> str:
        return 'Question: {question}'.format(question=self.question)