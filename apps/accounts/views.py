from django.contrib.auth import views as auth_views, logout
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.views.generic import TemplateView
from django.contrib import messages
from .models import UserRole

class CustomLoginView(auth_views.LoginView):
    template_name = 'auth/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if hasattr(user, 'is_suspended') and user.is_suspended:
            form.add_error(None, "Your account has been suspended. Please contact the cooperative administrator.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        user = self.request.user
        if user.must_change_password:
            messages.info(self.request, "This is your first login. Please change your password to continue.")
            return reverse_lazy('accounts:password_change')
        
        if user.role == UserRole.SUPER_ADMIN:
            return reverse_lazy('cooperatives:super_dashboard')
        elif user.role == UserRole.COOP_ADMIN:
            return reverse_lazy('cooperatives:admin_dashboard')
        else:
            return reverse_lazy('members:dashboard')


class CustomPasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    template_name = 'auth/password_change.html'
    success_url = reverse_lazy('accounts:password_change_done')
    
    def form_valid(self, form):
        user = self.request.user
        user.must_change_password = False
        user.save()
        return super().form_valid(form)


class CustomPasswordChangeDoneView(LoginRequiredMixin, auth_views.PasswordChangeDoneView):
    template_name = 'auth/password_change_done.html'


class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'accounts/profile.html'
    fields = ['first_name', 'last_name', 'email', 'phone', 'address']
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user
