import re
from rest_framework import serializers
from django.core.validators import validate_email
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (
    UserAccount, UserProfile, UserInterest, Notification, Major, Interest
)

NAME_REGEX = "^[a-zA-Z\- ]+$"
EMAIL_REGEX = "^[a-zA-Z0-9_.+-]+@ashesi.edu.gh$"
PASSWORD_REGEX = "^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[@$!%?&])[A-Za-z\d@$!%?&]{8,}$"


class AccountRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required = True)
    confirm_password = serializers.CharField(write_only=True, required = True)

    class Meta:
        model = UserAccount
        fields = ["id", "firstname", "lastname", "email", "mobile_number", 
                  "password", "confirm_password", "date_joined"]

    def validate_firstname(self, value):
        if not re.match(NAME_REGEX, value):
            raise serializers.ValidationError("Firstname should contain only alphabets")
        
        return value

    def validate_lastname(self, value):
        if not re.match(NAME_REGEX, value):
            raise serializers.ValidationError("Lastname should contain only alphabets")
        
        return value

    def validate_email(self, value):
        if not re.match(EMAIL_REGEX, value):
            raise serializers.ValidationError("Invalid email address")
        
        if UserAccount.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists!")
        
        return value

    def validate_password(self, value):
        if not re.match(PASSWORD_REGEX, value):
            raise serializers.ValidationError("Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one number and one special character")

        return value

    def validate_confirm_password(self, value):
        if not re.match(PASSWORD_REGEX, value):
            raise serializers.ValidationError("Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one number and one special character")

        return value

    def validate_mobile_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Mobile number must contain only numbers")

        if UserAccount.objects.filter(mobile_number=value).exists():
            raise serializers.ValidationError("An account with this mobile number already exists!")

        return value

    def create(self, **validated_data):
        return UserAccount.objects.create(**validated_data)

    def save(self, **kwargs):
        user = UserAccount(
            firstname = self.validated_data["firstname"],
            lastname = self.validated_data["lastname"],
            email = self.validated_data["email"],
            mobile_number = self.validated_data["mobile_number"]
        )

        password = self.validated_data["password"]
        confirm_password = self.validated_data["confirm_password"]

        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match!")
        
        user.set_password(self.validated_data["password"])
        user.save()
        return user


class UserAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ["id", "firstname", "lastname", "email", "mobile_number", "date_joined"]


class UpdateUserAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ["firstname", "lastname", "email", "mobile_number"]

    def update(self, instance, validated_data):
        instance.firstname = validated_data.get("firstname", instance.firstname)
        instance.lastname = validated_data.get("lastname", instance.lastname)
        instance.email = validated_data.get("email", instance.email)
        instance.mobile_number = validated_data.get("mobile_number", instance.mobile_number)
        instance.save()
        return instance


class AccountLoginSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField(required=True, validators=[validate_email])
    password = serializers.CharField(
        write_only=True,
        required=True,
        trim_whitespace=False,
        label="Password",
        style={"input_type": "password"},
        validators=[]
    )

    token = serializers.SerializerMethodField("get_token")

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["firstname"] = user.firstname
        token["lastname"] = user.lastname
        token["email"] = user.email
        token["mobile_number"] = user.mobile_number

        return token

    class Meta:
        model = UserAccount
        fields = ["email", "password", "token"]

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required")
        return value

    def validate_password(self, value):
        if not re.match(PASSWORD_REGEX, value):
            raise serializers.ValidationError("Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one number and one special character")

        return value


    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = UserAccount.objects.filter(email=email).first()
        if user is None:
            raise serializers.ValidationError("User does not exist")

        if not user.check_password(password):
            raise serializers.ValidationError("Incorrect password!")

        if not user.is_active:
            raise serializers.ValidationError("Account is not active!")

        token = self.get_token(user)
        user_data = UserAccountSerializer(user).data
        user_data["refresh_token"] = str(token)
        user_data["access_token"] = str(token.access_token)
        return user_data

    
class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField("get_user")
    class Meta:
        model = UserProfile
        fields = ["user", "major", "profile_picture", "date_of_birth"]

    def get_user(self, obj):
        return self.context["request"].user

    def validate_major(self, value):
        if value not in Major:
            raise serializers.ValidationError("Invalid major")
        
        return value

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return UserProfile.objects.create(**validated_data)
        
    def update(self, instance, validated_data):
        instance.major = validated_data.get("major", instance.major)
        instance.profile_picture = validated_data.get("profile_picture", instance.profile_picture)
        instance.date_of_birth = validated_data.get("date_of_birth", instance.date_of_birth)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        user_profile = super().to_representation(instance)
        user_profile["user"] = instance.user.id
        user_profile["firstname"] = instance.user.firstname
        user_profile["lastname"] = instance.user.lastname
        user_profile["email"] = instance.user.email
        user_profile["mobile_number"] = instance.user.mobile_number
        user_profile["date_joined"] = instance.user.date_joined

        # retrieve user interests
        user_interests = UserInterest.objects.filter(user=instance.user)
        user_profile["interests"] = []
        for interest in user_interests:
            user_profile["interests"].append(UserInterestSerializer(interest).data)
        return user_profile


class UserInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInterest
        fields = ["id", "user", "interest"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return UserInterest.objects.create(**validated_data)
        
    def update(self, instance, validated_data):
        instance.interests = validated_data.get("interest", instance.interests)
        instance.save()
        return instance
    

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "user", "message", "date", "is_read"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return Notification.objects.create(**validated_data)