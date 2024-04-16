from rest_framework import serializers

from .models import (
    StudyGroup, GroupInterests, GroupMembers, GroupScheduledTime, GroupMembershipRequest
)
from accounts.models import UserAccount, Major


class StudyGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyGroup
        fields = ["id", "name", "major", "creator", "group_image", "whatsAppLink", "date_created"]

    def get_creator(self, obj):
        return self.context["request"].user
    
    def validate_major(self, value):
        if value not in Major:
            raise serializers.ValidationError("Invalid major")
        
        return value
    
    def validate_whatsAppLink(self, value):
        if not value.startswith("https://chat.whatsapp.com/"):
            raise serializers.ValidationError("Invalid WhatsApp link")
        
        return value
    
    def create(self, validated_data):
        validated_data["creator"] = self.context["request"].user
        return StudyGroup.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.major = validated_data.get("major", instance.major)
        instance.group_image = validated_data.get("group_image", instance.group_image)
        instance.whatsAppLink = validated_data.get("whatsAppLink", instance.whatsAppLink)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        study_group = super().to_representation(instance)
        study_group["creator"] = instance.creator.firstname + " " + instance.creator.lastname

        # retrieve group interests
        group_interests = GroupInterests.objects.filter(group=instance)
        study_group["interests"] = []
        for interest in group_interests:
            study_group["interests"].append(GroupInterestsSerializer(interest).data)
        
        # retrieve group members
        group_members = GroupMembers.objects.filter(group=instance)
        study_group["members"] = []
        for member in group_members:
            study_group["members"].append(GroupMembersSerializer(member).data)

        # if admin, retrieve membership requests
        if GroupMembers.objects.filter(group=instance, member=self.context["request"].user, is_admin=True).exists():
            group_membership_requests = GroupMembershipRequest.objects.filter(group=instance)
            study_group["membership_requests"] = []
            for request in group_membership_requests:
                study_group["membership_requests"].append(GroupMembershipRequestSerializer(request).data)

        # retrieve group scheduled times
        group_scheduled_times = GroupScheduledTime.objects.filter(group=instance)
        study_group["scheduled_times"] = []
        for time in group_scheduled_times:
            study_group["scheduled_times"].append(GroupScheduledTimeSerializer(time).data)

        return study_group
    

class GroupInterestsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupInterests
        fields = ["id", "group", "interest"]
    
    def create(self, validated_data):
        return GroupInterests.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.interest = validated_data.get("interest", instance.interest)
        instance.save()
        return instance
    

class GroupMembersSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMembers
        fields = ["id", "group", "member", "date_joined", "is_admin"]

    def validate_member(self, value):
        if not UserAccount.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid member!")
        
        return value
    
    def create(self, validated_data):
        return GroupMembers.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.is_admin = validated_data.get("is_admin", instance.is_admin)
        instance.save()
        return instance
    

class GroupScheduledTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupScheduledTime
        fields = ["id", "group", "day", "start_time", "end_time"]

    def validate_group(self, value):
        if not StudyGroup.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid group!")
        
        return value
    
    def validate(self, attrs):
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError("Start time must be less than end time")
        
        return attrs
    
    def create(self, validated_data):
        return GroupScheduledTime.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.day = validated_data.get("day", instance.day)
        instance.start_time = validated_data.get("start_time", instance.start_time)
        instance.end_time = validated_data.get("end_time", instance.end_time)
        instance.save()
        return instance


class GroupMembershipRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMembershipRequest
        fields = ["id", "group", "user"]

    def validate_group(self, value):
        if not StudyGroup.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid group!")
        
        return value
    
    def validate_user(self, value):
        if not UserAccount.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid user!")
        
        return value
    
    def create(self, validated_data):
        return GroupMembershipRequest.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.group = validated_data.get("group", instance.group)
        instance.user = validated_data.get("user", instance.user)
        instance.save()
        return instance