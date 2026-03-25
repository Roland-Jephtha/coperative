from django.urls import path
from .views import (
    MemberLoanRepaymentCreateView, ApproveLoanRepaymentView, RejectLoanRepaymentView
)

app_name = 'repayments'

urlpatterns = [
    path('loan/<int:loan_pk>/record/', MemberLoanRepaymentCreateView.as_view(), name='record'),
    path('<int:pk>/approve/', ApproveLoanRepaymentView.as_view(), name='approve'),
    path('<int:pk>/reject/', RejectLoanRepaymentView.as_view(), name='reject'),
]
