from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .question import Question
from .dafi_question import DAFI_Question

class Profile(models.Model):

    USER_TYPE = [
        ('A', 'Admin'),
        ('I', 'Instructor'),
        ('S', 'Student')
    ]

    user_profile = models.OneToOneField(User, on_delete=models.CASCADE)

    user_group = models.CharField(max_length=1, choices=USER_TYPE)
    user_question = models.ManyToManyField(Question, blank=True)
    user_dafi_question = models.ManyToManyField(DAFI_Question, blank=True)
    user_instructor = models.ForeignKey('self', on_delete=models.PROTECT, default=1)

    
    '''
    This updates default user model with our profile extention
    '''
    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user_profile=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

    '''
    Displays info in admin page
    '''
    def __str__(self) -> str:
        return '{user_profile} - {user_group}'.format(user_profile=self.user_profile, user_group=self.user_group)