from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from global_data.email_util import EmailUtil
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
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        accepted_terms = request.POST.get('accepted_terms')

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

        # Création utilisateur INACTIF
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            accepted_terms=True,
            is_active=False
        )

        # Génération code
        code = get_random_string(length=6, allowed_chars='0123456789')
        user.verification_code = code
        user.save()

        # Lien de vérification
        verification_url = f"{request.build_absolute_uri(reverse('verify_email'))}?code={code}&email={email}"

        context = {
            'user': user,
            'code': code,
            'verification_url': verification_url
        }

        email_util = EmailUtil(prod=True)
        email_util.send_email_with_template(
            template='email/account_verification.html',
            context=context,
            receivers=[email],
            subject="Verify your email"
        )

        request.session['verification_email'] = email

        messages.success(request, "Account created. Please verify your email.")
        return redirect('verify_email')


# ==========================
# LOGIN
# ==========================
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
            if not user.is_active:
                messages.error(request, "Account inactive. Please verify your email.")
                request.session['verification_email'] = email
                return redirect('verify_email')

            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('texte')

        messages.error(request, "Invalid credentials.")
        return render(request, 'Auth/login.html')


# ==========================
# VERIFY EMAIL
# ==========================
class VerifyEmailView(View):

    def get(self, request):
        email = request.GET.get('email', request.session.get('verification_email'))
        code = request.GET.get('code')

        if email and code:
            return self.verify(request, email, code)

        return render(request, 'Auth/verify_email.html', {'email': email})

    def post(self, request):
        email = request.POST.get('email')
        code = request.POST.get('code')
        return self.verify(request, email, code)

    def verify(self, request, email, code):
        try:
            user = User.objects.get(email=email)
            saved_code = user.verification_code  # ✅ CORRECTION ICI

            if saved_code and saved_code == code:
                user.is_active = True
                user.verification_code = None  # ✅ Nettoyage
                user.save()

                login(request, user)
                messages.success(request, "Email verified successfully!")
                return redirect('login')
            else:
                messages.error(request, "Invalid verification code.")
                return render(request, 'Auth/verify_email.html', {'email': email})

        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('register')


# ==========================
# LOGOUT
# ==========================
class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "You have been logged out successfully.")
        return redirect('login')
