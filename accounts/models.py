from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if email is None:
            raise ValueError("The Email field must be set")

        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)

        email = self.normalize_email(email)
        user = self.model(email=email, password = password, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self.create_user(email, password, **extra_fields)
    

class UserAccount(AbstractBaseUser, PermissionsMixin):
    firstname = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(max_length=20, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    last_login = models.DateTimeField(default=timezone.now)
    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["firstname", "lastname", "mobile_number", "password"]

    def _str_(self):
        return self.firstname 
    

class Major(models.TextChoices):
    MIS = "Management Information Systems"
    CS = "Computer Science"
    BA = "Business Administration"
    EE = "Electrical Engineering"
    ME = "Mechanical Engineering"
    CE = "Computer Engineering"


class Interest(models.TextChoices):
    AI = "Artificial Intelligence"
    ML = "Machine Learning"
    DS = "Data Science"
    SE = "Software Engineering"
    DB = "Database Management"
    NW = "Networks"
    WEB = "Web Development"
    MOB = "Mobile Development"
    SEC = "Cyber Security"
    IOT = "Internet of Things"
    AR = "Augmented Reality"
    VR = "Virtual Reality"
    BC = "Blockchain"
    CC = "Cloud Computing"
    ROB = "Robotics"
    BL = "Business Law"
    MK = "Marketing"
    FN = "Finance"
    AC = "Accounting"
    EC = "Economics"
    PM = "Project Management"
    HR = "Human Resources"


class AccessBlacklist(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    token = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    @classmethod
    def is_blacklisted(cls, token):
        return cls.objects.filter(token=token).exists()
    
    @classmethod
    def blacklist(cls, token):
        cls.objects.create(token=token)

    @classmethod
    def cleanup(cls):
        cls.objects.filter(date__lte=timezone.now() - timezone.timedelta(days=1)).delete()


class UserProfile(models.Model):
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    major = models.CharField(max_length=50, choices=Major.choices)
    profile_picture = models.ImageField(upload_to="profile_pictures/", null=True, blank=True)
    date_of_birth = models.DateField()


class UserInterest(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    interest = models.CharField(max_length=50, choices=Interest.choices)


class Notification(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def _str_(self):
        return self.message