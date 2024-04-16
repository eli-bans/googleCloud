from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone

from .models import UserAccount, UserProfile, UserInterest, Notification, AccessBlacklist, Interest
from .serializers import (
    AccountRegistrationSerializer, AccountLoginSerializer, UserAccountSerializer, 
    UpdateUserAccountSerializer, UserProfileSerializer, UserInterestSerializer, 
    NotificationSerializer)
from .permissions import AccessBlacklisted


class AccountRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AccountRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserAccountSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountLoginView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = AccountLoginSerializer(data=request.data)
        response = super().post(request, *args, **kwargs)

        if serializer.is_valid():
            user = UserAccount.objects.get(email=request.data["email"])

            # set cookies
            response.set_cookie("refresh_token", response.data["refresh"], httponly=True, samesite="None", secure=True)
            response.set_cookie("access_token", response.data["access"], httponly=True, samesite="None", secure=True)

            # update last login
            user.last_login = timezone.now()
            user.save()

            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UserAccountView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def get(self, request):
        user = request.user
        serializer = AccountRegistrationSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class AccountLogoutView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        access_token = request.COOKIES.get("access_token")

        try:
            refresh_token = RefreshToken(refresh_token)
            refresh_token.blacklist()
        except:
            return Response({"message": "Already logged out!"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            access_token = AccessBlacklist.objects.create(
                user=request.user,
                token=access_token
            )
            access_token.save()
        except:
            return Response({"message": "Already logged out!"}, status=status.HTTP_400_BAD_REQUEST)
        
        response = Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        response.delete_cookie("refresh_token")
        response.delete_cookie("access_token")
        return response
    

class UpdateUserAccountView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def patch(self, request):
        user = request.user
        serializer = UpdateUserAccountSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserAccountSerializer(user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class AddUserProfileView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def post(self, request):
        serializer = UserProfileSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            user_profile = serializer.save()

            # if interests in request data, create user interests
            if "interests" in request.data:
                for interest in request.data["interests"]:
                    if interest in Interest and not UserInterest.objects.filter(user=user_profile.user, interest=interest).exists():
                        user_interest = UserInterest.objects.create(user=user_profile.user, interest=interest)
                        user_interest.save()
            return Response(UserProfileSerializer(user_profile).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class RetrieveUserProfileView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def get(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(user_profile, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ListUserProfilesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    

class RetrieveUserProfileDetailsView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = "user_id"
    

class UpdateUserProfileView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def patch(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(user_profile, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save(instance=user_profile)

            # if interests in request data, create user interests
            if "interests" in request.data:
                for interest in request.data["interests"]:
                    if interest in Interest and not UserInterest.objects.filter(user=user_profile.user, interest=interest).exists():
                        user_interest = UserInterest.objects.create(user=user_profile.user, interest=interest)
                        user_interest.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class RemoveUserInterestView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def delete(self, request, interest_id):
        try:
            interest = UserInterest.objects.get(id=interest_id)
        except UserInterest.DoesNotExist:
            return Response({"message": "Interest not found"}, status=status.HTTP_404_NOT_FOUND)
        
        interest.delete()
        user_profile = UserProfile.objects.get(user=request.user)
        return Response(UserProfileSerializer(user_profile, context={"request": request}).data, status=status.HTTP_200_OK)


class RetrieveUserNotificationsView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class MarkNotificationAsOrUnreadReadView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def post(self, request, notification_id):
        notification = Notification.objects.get(id=notification_id)
        
        if notification.is_read:
            notification.is_read = False
        else:
            notification.is_read = True

        notification.save()
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)
    

class DeleteNotificationView(APIView):
    permission_classes = [IsAuthenticated, AccessBlacklisted]

    def delete(self, request, notification_id):
        notification = Notification.objects.get(id=notification_id)
        notification.is_deleted = True
        notification.save()
        return Response({"message": "Notification deleted"}, status=status.HTTP_200_OK)