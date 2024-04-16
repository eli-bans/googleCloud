from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AccountRegistrationView, AccountLoginView, UserAccountView, AccountLogoutView,
    UpdateUserAccountView, AddUserProfileView, UpdateUserProfileView, RetrieveUserProfileView,
    ListUserProfilesView, RetrieveUserProfileDetailsView, RemoveUserInterestView,

    RetrieveUserNotificationsView, MarkNotificationAsOrUnreadReadView, DeleteNotificationView
)

urlpatterns = [
    path("register/", AccountRegistrationView.as_view(), name="register"),
    path("login/", AccountLoginView.as_view(), name="login"),
    path("user/", UserAccountView.as_view(), name="user"),
    path("logout/", AccountLogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("update/", UpdateUserAccountView.as_view(), name="update"),

    path("profile/add/", AddUserProfileView.as_view(), name="add_profile"),
    path("profile/update/", UpdateUserProfileView.as_view(), name="update_profile"),
    path("user/profile/", RetrieveUserProfileView.as_view(), name="retrieve_profile"),
    path("profiles/", ListUserProfilesView.as_view(), name="list_profiles"),
    path("profile/<int:user_id>/", RetrieveUserProfileDetailsView.as_view(), name="retrieve_profile_details"),
    path("interests/remove/<int:interest_id>/", RemoveUserInterestView.as_view(), name="remove_interest"),

    path("notifications/", RetrieveUserNotificationsView.as_view(), name="notifications"),
    path("notifications/mark/read/<int:notification_id>/", MarkNotificationAsOrUnreadReadView.as_view(), name="mark_notification_read"),
    path("notifications/mark/unread/<int:notification_id>/", MarkNotificationAsOrUnreadReadView.as_view(), name="mark_notification_unread"),
    path("notifications/delete/<int:notification_id>/", DeleteNotificationView.as_view(), name="delete_notification"),
]