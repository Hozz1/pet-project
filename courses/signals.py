from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Course

def purge_course_detail(course_id: int):
    cache.delete(f"v1:courses:detail:{course_id}")

def purge_top_lists():
    cache.delete_pattern("v1:courses:top:*")

@receiver(post_save, sender=Course)
def on_course_save(sender, instance: Course, **kwargs):
    purge_course_detail(instance.pk)
    purge_top_lists()

@receiver(post_delete, sender=Course)
def on_course_delete(sender, instance: Course, **kwargs):
    purge_course_detail(instance.pk)
    purge_top_lists()
