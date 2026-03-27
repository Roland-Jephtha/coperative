from django.urls import path
from .views import CooperativeContributionsView, MemberContributionsView, ContributionCreateView, MemberContributionCreateView, ApproveContributionView, RejectContributionView, ExportContributionCSVView

app_name = 'contributions'

urlpatterns = [
    path('management/', CooperativeContributionsView.as_view(), name='coop_list'),
    path('management/add/', ContributionCreateView.as_view(), name='coop_add'),
    path('management/<int:pk>/approve/', ApproveContributionView.as_view(), name='approve'),
    path('management/<int:pk>/reject/', RejectContributionView.as_view(), name='reject'),
    path('my-savings/', MemberContributionsView.as_view(), name='member_list'),
    path('deposit/', MemberContributionCreateView.as_view(), name='deposit'),
    path('export/csv/', ExportContributionCSVView.as_view(), name='export_csv'),
]
