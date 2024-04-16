from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    StudyGroup, GroupInterests, GroupMembers, GroupScheduledTime, GroupMembershipRequest
)
from accounts.models import Interest, Notification, UserInterest, UserProfile
from .serializers import (
    StudyGroupSerializer, GroupMembersSerializer, GroupScheduledTimeSerializer,
    GroupMembershipRequestSerializer
)
from accounts.permissions import AccessBlacklisted


class CreateStudyGroupView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def post(self, request):
        serializer = StudyGroupSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            study_group = serializer.save()

            # add group interests
            if "interests" in request.data:
                for interest in request.data["interests"]:
                    if interest in Interest:
                        GroupInterests.objects.create(group=study_group, interest=interest)

            # add creator as group member
            GroupMembers.objects.create(group=study_group, member=request.user, is_admin=True)

            # create notification
            Notification.objects.create(
                user=study_group.creator,
                message=f"You created the group {study_group.name} on {study_group.date_created}",

            )

            return Response(StudyGroupSerializer(study_group, context={"request": request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class RetrieveStudyGroupView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def get(self, request, group_id):
        try:
            study_group = StudyGroup.objects.get(id=group_id)
        except StudyGroup.DoesNotExist:
            return Response({"message": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = StudyGroupSerializer(study_group, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ListStudyGroupsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]
    queryset = StudyGroup.objects.all()
    serializer_class = StudyGroupSerializer

    def get_queryset(self):
        # retrieve groups the user is part of
        user_groups = GroupMembers.objects.filter(member=self.request.user)
        return [group.group for group in user_groups]


class UpdateStudyGroupView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def patch(self, request, group_id):
        try:
            study_group = StudyGroup.objects.get(id=group_id)
        except StudyGroup.DoesNotExist:
            return Response({"message": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = StudyGroupSerializer(study_group, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # update profile image if provided
            if "group_image" in request.data:
                # delete old image from storage
                study_group.group_image.delete(save=False)
                study_group.group_image = request.data["group_image"]
                study_group.save()

            # update group interests
            if "interests" in request.data:
                for interest in request.data["interests"]:
                    if interest in Interest and not GroupInterests.objects.filter(group=study_group, interest=interest).exists():
                        GroupInterests.objects.create(group=study_group, interest=interest)

            return Response(StudyGroupSerializer(study_group, context={"request": request}).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class RemoveGroupInterestView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def delete(self, request, interest_id):
        try:
            group_interest = GroupInterests.objects.get(id=interest_id)
        except GroupInterests.DoesNotExist:
            return Response({"message": "Interest not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # ensure user is the creator of the group
        if group_interest.group.creator != request.user:
            return Response({"message": "You do not have permission to remove this interest"}, status=status.HTTP_403_FORBIDDEN)
        
        group_interest.delete()
        return Response({"message": "Interest removed"}, status=status.HTTP_200_OK)
    

class DeleteStudyGroupView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def delete(self, request, group_id):
        try:
            study_group = StudyGroup.objects.get(id=group_id)
        except StudyGroup.DoesNotExist:
            return Response({"message": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # ensure user is the creator of the group
        if study_group.creator != request.user:
            return Response({"message": "You do not have permission to delete this group"}, status=status.HTTP_403_FORBIDDEN)
        
        # ensure no members are in the group aside the creator
        if GroupMembers.objects.filter(group=study_group).count() > 1:
            return Response({"message": "You cannot delete a group with members"}, status=status.HTTP_400_BAD_REQUEST)
        
        # create notification
        Notification.objects.create(
            user=study_group.creator,
            message=f"You deleted the group {study_group.name}!",
        )

        study_group.delete()
        return Response({"message": "Group deleted"}, status=status.HTTP_200_OK)


class RecommendGroupView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def get(self, request):
        # get groups the user is not part of
        possible_groups = StudyGroup.objects.exclude(groupmembers__member=request.user)
        
        recommended_groups = []
        groups_to_remove = []

        # get groups with the same major as the user
        for index, group in enumerate(possible_groups):
            if group.major == UserProfile.objects.filter(user=request.user).first().major:
                recommended_groups.append(group)

                # remove group from possible groups
                groups_to_remove.append(group)

        # remove recommended groups from possible groups before checking for similar interests
        possible_groups = possible_groups.exclude(pk__in=[group.pk for group in groups_to_remove])

        # get groups with similar interests as the user
        user_interests = UserInterest.objects.filter(user=request.user)
        for interest in user_interests:
            for group in possible_groups:
                if GroupInterests.objects.filter(group=group, interest=interest.interest).exists():
                    recommended_groups.append(group)
                    possible_groups.pop(possible_groups.index(group))

        serializer = StudyGroupSerializer(recommended_groups, context={"request": request}, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class LeaveStudyGroupView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def delete(self, request, group_id):
        try:
            group = StudyGroup.objects.get(id=group_id)
        except StudyGroup.DoesNotExist:
            return Response({"message": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            group_member = GroupMembers.objects.get(group=group, member=request.user)
        except GroupMembers.DoesNotExist:
            return Response({"message": "You are not a member of this group"}, status=status.HTTP_404_NOT_FOUND)
        
        group_member.delete()

        # create notification for user
        Notification.objects.create(
            user=request.user,
            message=f"You left the group {group.name}",
        )

        # notify all admin members of the group
        group_members = GroupMembers.objects.filter(group=group, is_admin=True)
        for member in group_members:
            Notification.objects.create(
                user=member.member,
                message=f"{request.user.firstname} {request.user.lastname} left the group {group.name}",

            )

        return Response({"message": "You have left the group"}, status=status.HTTP_200_OK)
    

class CreateGroupScheduledTimeView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def post(self, request, group_id):
        serializer = GroupScheduledTimeSerializer(data=request.data)
        if serializer.is_valid():
            # ensure user is an admin of the group
            if not GroupMembers.objects.filter(group_id=group_id, member=request.user, is_admin=True).exists():
                return Response({"message": "You do not have permission to create a scheduled time"}, status=status.HTTP_403_FORBIDDEN)
            
            group_scheduled_time = serializer.save(group_id=group_id)

            # notify all admin members of the group
            group_members = GroupMembers.objects.filter(group_id=group_id, is_admin=True)
            for member in group_members:
                Notification.objects.create(
                    user=member.member,
                    message=f"{request.user.firstname} {request.user.lastname} created a scheduled time for the group {group_scheduled_time.group.name}",
    
                )

            return Response(GroupScheduledTimeSerializer(group_scheduled_time).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListGroupScheduledTimesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]
    queryset = GroupScheduledTime.objects.all()
    serializer_class = GroupScheduledTimeSerializer


class UpdateGroupScheduledTimeView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def patch(self, request, time_id):
        try:
            group_scheduled_time = GroupScheduledTime.objects.get(id=time_id)
        except GroupScheduledTime.DoesNotExist:
            return Response({"message": "Scheduled time not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = GroupScheduledTimeSerializer(group_scheduled_time, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # notify all admin members of the group
            group_members = GroupMembers.objects.filter(group=group_scheduled_time.group, is_admin=True)
            for member in group_members:
                Notification.objects.create(
                    user=member.member,
                    message=f"{request.user.firstname} {request.user.lastname} updated a scheduled time for the group {group_scheduled_time.group.name}",
    
                )

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteGroupScheduledTimeView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def delete(self, request, time_id):
        try:
            group_scheduled_time = GroupScheduledTime.objects.get(id=time_id)
        except GroupScheduledTime.DoesNotExist:
            return Response({"message": "Scheduled time not found"}, status=status.HTTP_404_NOT_FOUND)
        
        group_scheduled_time.delete()

        # notify all admin members of the group
        group_members = GroupMembers.objects.filter(group=group_scheduled_time.group, is_admin=True)
        for member in group_members:
            Notification.objects.create(
                user=member.member,
                message=f"{request.user.firstname} {request.user.lastname} deleted a scheduled time for the group {group_scheduled_time.group.name}",

            )

        return Response({"message": "Scheduled time deleted"}, status=status.HTTP_200_OK)


class RequestGroupMembershipView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def post(self, request, group_id):
        try:
            group = StudyGroup.objects.get(id=group_id)
        except StudyGroup.DoesNotExist:
            return Response({"message": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
        
        GroupMembershipRequest.objects.create(group=group, user=request.user)

        # notify all admin members of the group
        group_members = GroupMembers.objects.filter(group=group, is_admin=True)
        for member in group_members:
            Notification.objects.create(
                user=member.member,
                message=f"{request.user.firstname} {request.user.lastname} requested to join the group {group.name}",

            )

        return Response({"message": "Membership request sent"}, status=status.HTTP_201_CREATED)
    

class ListYourMembershipRequestsView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def get(self, request):
        membership_requests = GroupMembershipRequest.objects.filter(user=request.user)
        serializer = GroupMembershipRequestSerializer(membership_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeleteGroupMembershipRequestView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def delete(self, request, request_id):
        try:
            membership_request = GroupMembershipRequest.objects.get(id=request_id)
        except GroupMembershipRequest.DoesNotExist:
            return Response({"message": "Membership request not found"}, status=status.HTTP_404_NOT_FOUND)
        
        membership_request.delete()
        return Response({"message": "Membership request deleted"}, status=status.HTTP_200_OK)


class ListGroupMembershipRequestsView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def get(self, request, group_id):
        try:
            group = StudyGroup.objects.get(id=group_id)
        except StudyGroup.DoesNotExist:
            return Response({"message": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # ensure user is an admin of the group
        if not GroupMembers.objects.filter(group=group, member=request.user, is_admin=True).exists():
            return Response({"message": "You do not have permission to view membership requests"}, status=status.HTTP_403_FORBIDDEN)
        
        membership_requests = GroupMembershipRequest.objects.filter(group=group)
        serializer = GroupMembershipRequestSerializer(membership_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class AcceptGroupMembershipRequestView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def post(self, request, request_id):
                
        try:
            membership_request = GroupMembershipRequest.objects.get(id=request_id)
        except GroupMembershipRequest.DoesNotExist:
            return Response({"message": "Membership request not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # ensure user is an admin of the group
        if not GroupMembers.objects.filter(group=membership_request.group, member=request.user, is_admin=True).exists():
            return Response({"message": "You do not have permission to accept membership requests"}, status=status.HTTP_403_FORBIDDEN)
        
        # create group member
        GroupMembers.objects.create(group=membership_request.group, member=membership_request.user)
        membership_request.delete()

        # create notification for user
        Notification.objects.create(
            user=membership_request.user,
            message=f"Your request to join the group {membership_request.group.name} was accepted",
        )

        # notify all admin members of the group
        group_members = GroupMembers.objects.filter(group=membership_request.group, is_admin=True)
        for member in group_members:
            Notification.objects.create(
                user=member.member,
                message=f"{request.user.firstname} {request.user.lastname} accepted {membership_request.user.firstname} {membership_request.user.lastname}'s request to join the group {membership_request.group.name}",

            )

        return Response({"message": "Membership request accepted"}, status=status.HTTP_200_OK)
    

class RejectGroupMembershipRequestView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def delete(self, request, request_id):
        try:
            membership_request = GroupMembershipRequest.objects.get(id=request_id)
        except GroupMembershipRequest.DoesNotExist:
            return Response({"message": "Membership request not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # ensure user is an admin of the group
        if not GroupMembers.objects.filter(group=membership_request.group, member=request.user, is_admin=True).exists():
            return Response({"message": "You do not have permission to reject membership requests"}, status=status.HTTP_403_FORBIDDEN)
        
        membership_request.delete()

        # create notification for user
        Notification.objects.create(
            user=membership_request.user,
            message=f"Your request to join the group {membership_request.group.name} was rejected",
        )

        # notify all admin members of the group
        group_members = GroupMembers.objects.filter(group=membership_request.group, is_admin=True)
        for member in group_members:
            Notification.objects.create(
                user=member.member,
                message=f"{request.user.firstname} {request.user.lastname} rejected {membership_request.user.firstname} {membership_request.user.lastname}'s request to join the group {membership_request.group.name}",

            )
        return Response({"message": "Membership request rejected"}, status=status.HTTP_200_OK)
    

class ListGroupMembersView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def get(self, request, group_id):
        try:
            group = StudyGroup.objects.get(id=group_id)
        except StudyGroup.DoesNotExist:
            return Response({"message": "Group not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # ensure user is a member of the group
        if not GroupMembers.objects.filter(group=group, member=request.user).exists():
            return Response({"message": "You are not a member of this group"}, status=status.HTTP_403_FORBIDDEN)
        
        group_members = GroupMembers.objects.filter(group=group)
        serializer = GroupMembersSerializer(group_members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class MakeGroupMemberAdminView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def post(self, request, group_member_id):
        try:
            group_member = GroupMembers.objects.get(id=group_member_id)
        except GroupMembers.DoesNotExist:
            return Response({"message": "Group member not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # ensure user is the creator of the group
        if group_member.group.creator != request.user:
            return Response({"message": "You do not have permission to make this user an admin"}, status=status.HTTP_403_FORBIDDEN)
                
        group_member.is_admin = True
        group_member.save()

        # create notification for user
        Notification.objects.create(
            user=group_member.member,
            message=f"You are now an admin of the group {group_member.group.name}",
        )

        # notify all admin members of the group
        group_members = GroupMembers.objects.filter(group=group_member.group, is_admin=True)
        for member in group_members:
            Notification.objects.create(
                user=member.member,
                message=f"{request.user.firstname} {request.user.lastname} made {group_member.member.firstname} {group_member.member.lastname} an admin of the group {group_member.group.name}",

            )

        return Response({"message": "Group member is now an admin"}, status=status.HTTP_200_OK)
    

class RemoveGroupMemberAdminView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def delete(self, request, group_member_id):
        try:
            group_member = GroupMembers.objects.get(id=group_member_id)
        except GroupMembers.DoesNotExist:
            return Response({"message": "Group member not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # ensure user is the creator of the group
        if group_member.group.creator != request.user:
            return Response({"message": "You do not have permission to remove this user as an admin"}, status=status.HTTP_403_FORBIDDEN)
                
        group_member.is_admin = False
        group_member.save()

        # create notification for user
        Notification.objects.create(
            user=group_member.member,
            message=f"You are no longer an admin of the group {group_member.group.name}",
        )

        # notify all admin members of the group
        group_members = GroupMembers.objects.filter(group=group_member.group, is_admin=True)
        for member in group_members:
            Notification.objects.create(
                user=member.member,
                message=f"{request.user.firstname} {request.user.lastname} removed {group_member.member.firstname} {group_member.member.lastname} as an admin of the group {group_member.group.name}",

            )

        return Response({"message": "Group member is no longer an admin"}, status=status.HTTP_200_OK)


class RemoveGroupMemberView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def delete(self, request, group_member_id):
        try:
            group_member = GroupMembers.objects.get(id=group_member_id)
        except GroupMembers.DoesNotExist:
            return Response({"message": "Group member not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # ensure user is the creator of the group
        if group_member.group.creator != request.user:
            return Response({"message": "You do not have permission to remove this user from the group"}, status=status.HTTP_403_FORBIDDEN)
                
        group_member.delete()

        # create notification for user
        Notification.objects.create(
            user=group_member.member,
            message=f"You were removed from the group {group_member.group.name}",
        )

        # notify all admin members of the group
        group_members = GroupMembers.objects.filter(group=group_member.group, is_admin=True)
        for member in group_members:
            Notification.objects.create(
                user=member.member,
                message=f"{request.user.firstname} {request.user.lastname} removed {group_member.member.firstname} {group_member.member.lastname} from the group {group_member.group.name}",

            )

        return Response({"message": "Group member removed"}, status=status.HTTP_200_OK)