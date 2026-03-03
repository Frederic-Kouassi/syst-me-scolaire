from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from students.models import User
import logging

logger = logging.getLogger(__name__)


# ==========================
# REGISTER
# ==========================
class RegisterView(View):

    def get(self, request):
        return render(request, 'Auth/register.html')

    def post(self, request):
        first_name       = request.POST.get('first_name')
        last_name        = request.POST.get('last_name')
        email            = request.POST.get('email')
        password         = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        accepted_terms   = request.POST.get('accepted_terms')

        if not accepted_terms:
            messages.error(request, "You must accept the Terms & Conditions.")
            return render(request, 'Auth/register.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'Auth/register.html')

        try:
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'Auth/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return render(request, 'Auth/register.html')

        username = email.split('@')[0]
        if User.objects.filter(username=username).exists():
            username = f"{username}_{User.objects.count()}"

        # Création utilisateur ACTIF directement
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            accepted_terms=True,
            is_active=True
        )

        messages.success(request, "Compte créé avec succès. Vous pouvez vous connecter.")
        return redirect('login')


# ==========================
# LOGIN
# ==========================
class LoginView(View):

    def get(self, request):
        return render(request, 'Auth/login.html')

    def post(self, request):
        email    = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user_obj = User.objects.get(email=email)
            user     = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            messages.success(request, f"Bienvenue, {user.first_name} !")
            return redirect('texte')

        messages.error(request, "Email ou mot de passe incorrect.")
        return render(request, 'Auth/login.html')


# ==========================
# LOGOUT
# ==========================
class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "Vous avez été déconnecté avec succès.")
        return redirect('login')