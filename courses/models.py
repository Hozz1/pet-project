from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.CharField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='courses')


class Module(models.Model):
    title = models.CharField(max_length=255)
    description = models.CharField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name='modules')

    def __str__(self):
        return self.title

class Lesson(models.Model):
    title = models.CharField(max_length=255)
    description = models.CharField(blank=True)
    beginning = models.TextField()
    middle = models.TextField()
    ending = models.TextField()
    module = models.ForeignKey(Module, on_delete=models.PROTECT, related_name='lessons')

    def __str__(self):
        return self.title