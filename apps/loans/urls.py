from django.urls import path
from .views import (
    CooperativeLoansView, MemberLoansView, LoanCreateView, MemberLoanCreateView, 
    LoanScheduleView, ApproveLoanView, RejectLoanView, DisburseLoanView, ExportLoanCSVView
)

app_name = 'loans'
urlpatterns = [
    path('management/', CooperativeLoansView.as_view(), name='coop_list'),
    path('management/add/', LoanCreateView.as_view(), name='add'),
    path('my-loans/', MemberLoansView.as_view(), name='member_list'),
    path('apply/', MemberLoanCreateView.as_view(), name='apply'),
    path('<int:loan_id>/schedule/', LoanScheduleView.as_view(), name='schedule'),
    path('<int:loan_id>/approve/', ApproveLoanView.as_view(), name='approve'),
    path('<int:loan_id>/disburse/', DisburseLoanView.as_view(), name='disburse'),
    path('<int:loan_id>/reject/', RejectLoanView.as_view(), name='reject'),
    path('export/csv/', ExportLoanCSVView.as_view(), name='export_csv'),
]
