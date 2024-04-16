from django.urls import path
from .views import (
    CreateStudyGroupView, ListStudyGroupsView, RetrieveStudyGroupView, UpdateStudyGroupView, DeleteStudyGroupView,
    RemoveGroupInterestView, RecommendGroupView, LeaveStudyGroupView,
    CreateGroupScheduledTimeView, ListGroupScheduledTimesView, UpdateGroupScheduledTimeView, DeleteGroupScheduledTimeView,
    RequestGroupMembershipView, ListYourMembershipRequestsView, DeleteGroupMembershipRequestView, 
    ListGroupMembershipRequestsView, AcceptGroupMembershipRequestView, RejectGroupMembershipRequestView,
    ListGroupMembersView, MakeGroupMemberAdminView, RemoveGroupMemberAdminView, RemoveGroupMemberView
)

urlpatterns = [
    path("create/", CreateStudyGroupView.as_view(), name="create_group"),
    path("list/", ListStudyGroupsView.as_view(), name="list_groups"),
    path("<int:group_id>/", RetrieveStudyGroupView.as_view(), name="retrieve_group"),
    path("update/<int:group_id>/", UpdateStudyGroupView.as_view(), name="update_group"),
    path("delete/<int:group_id>/", DeleteStudyGroupView.as_view(), name="delete_group"),
    path("interests/remove/<int:interest_id>/", RemoveGroupInterestView.as_view(), name="remove_interest"),
    path("leave/<int:group_id>/", LeaveStudyGroupView.as_view(), name="leave_group"),
    path("recommend/", RecommendGroupView.as_view(), name="recommend_group"),

    path("scheduled_time/create/<int:group_id>/", CreateGroupScheduledTimeView.as_view(), name="create_scheduled_time"),
    path("scheduled_time/list/", ListGroupScheduledTimesView.as_view(), name="list_scheduled_times"),
    path("scheduled_time/update/<int:time_id>/", UpdateGroupScheduledTimeView.as_view(), name="update_scheduled_time"),
    path("scheduled_time/delete/<int:time_id>/", DeleteGroupScheduledTimeView.as_view(), name="delete_scheduled_time"),

    path("membership/request/<int:group_id>/", RequestGroupMembershipView.as_view(), name="request_membership"),
    path("membership/requests/list/", ListYourMembershipRequestsView.as_view(), name="list_your_membership_requests"),
    path("membership/request/delete/<int:request_id>/", DeleteGroupMembershipRequestView.as_view(), name="delete_membership_request"),

    path("membership/requests/list/<int:group_id>/", ListGroupMembershipRequestsView.as_view(), name="list_membership_requests"),
    path("membership/request/accept/<int:request_id>/", AcceptGroupMembershipRequestView.as_view(), name="accept_membership_request"),
    path("membership/request/reject/<int:request_id>/", RejectGroupMembershipRequestView.as_view(), name="reject_membership_request"),

    path("members/list/<int:group_id>/", ListGroupMembersView.as_view(), name="list_members"),
    path("members/admin/make/<int:group_member_id>/", MakeGroupMemberAdminView.as_view(), name="make_admin"),
    path("members/admin/remove/<int:group_member_id>/", RemoveGroupMemberAdminView.as_view(), name="remove_admin"),
    path("members/remove/<int:group_member_id>/", RemoveGroupMemberView.as_view(), name="remove_member"),
]