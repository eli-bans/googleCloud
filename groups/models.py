from django.db import models
from accounts.models import UserAccount, Interest, Major


class StudyGroup(models.Model):
    name = models.CharField(max_length=100)
    major = models.CharField(max_length=100, choices=Major.choices)
    creator = models.ForeignKey(UserAccount, on_delete=models.CASCADE, blank=True)
    whatsAppLink = models.CharField(max_length=100)
    group_image = models.ImageField(upload_to="group_images/", blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)


class GroupInterests(models.Model):
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)
    interest = models.CharField(max_length=50, choices=Interest.choices)


class GroupMembers(models.Model):
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)
    member = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)


class GroupScheduledTime(models.Model):
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, blank=True)
    day = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()


class GroupMembershipRequest(models.Model):
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)