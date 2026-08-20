from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ParentProfile, StudentProfile, TeacherProfile, User


@receiver(post_save, sender=User)
def create_role_profile(sender, instance, created, **kwargs):
    if not created:
        return
    profile_map = {
        User.Role.TEACHER: TeacherProfile,
        User.Role.STUDENT: StudentProfile,
        User.Role.PARENT: ParentProfile,
    }
    profile_model = profile_map.get(instance.role)
    if profile_model:
        profile_model.objects.create(user=instance)
