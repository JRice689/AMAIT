from django.contrib import admin

from src.models.profile import Profile
from src.models.question import Question
from src.models.study_guide import Study_Guide

admin.site.register(Profile)
admin.site.register(Question)
admin.site.register(Study_Guide)
