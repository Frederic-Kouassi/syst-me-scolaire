from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse

from students.models import User


import logging

logger = logging.getLogger(__name__)

class RegisterView(View):

    def get(self, request):
    
        return render(request, 'Auth/register.html')

    def post(self, request):
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Vérification des mots de passe
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'Auth/register.html')

        # Vérification email existant
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return render(request, 'Auth/register.html')

        # Génération username unique
        username = email.split('@')[0]
        if User.objects.filter(username=username).exists():
            username = f"{username}_{User.objects.count()}"

        # Création utilisateur
        user = User.objects.create_user(
            username=username,   
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        user.save()

        messages.success(request, "Account created successfully.")
        return redirect('login')


class LoginView(View):

    def get(self, request):
        return render(request, 'Auth/login.html')

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('texte')

        messages.error(request, "Invalid credentials.")
        return render(request, 'Auth/login.html')
    
    
class LogoutView(View):
    def get(self, request):
        logout(request)  # Déconnecte l'utilisateur
        messages.success(request, "You have been logged out successfully.")
        return redirect('login') 