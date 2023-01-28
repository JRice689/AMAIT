from django.db import models

class Study_Guide(models.Model):

    course = models.CharField(max_length=50)
    block = models.IntegerField()
    unit = models.IntegerField()
    title = models.CharField(max_length=50)
    prompt = models.TextField()

    def __str__(self) -> str:
        return '{course} | Block {block} Unit {unit}'.format(course=self.course, block=self.block, unit=self.unit)