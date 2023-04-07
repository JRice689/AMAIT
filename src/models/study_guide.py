from django.db import models

class Study_Guide(models.Model):

    course = models.CharField(max_length=50)
    block = models.CharField(max_length=255)
    page = models.IntegerField()
    text = models.TextField()
    embeddings = models.BinaryField()

    def __str__(self) -> str:
        return '{course} | Block {block}'.format(course=self.course, block=self.block, unit=self.unit)