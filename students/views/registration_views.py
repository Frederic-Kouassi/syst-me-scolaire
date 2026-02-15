from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


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
        accepted_terms = request.POST.get('accepted_terms')

        if not accepted_terms:
            messages.error(request, "You must accept the Terms & Conditions.")
            return render(request, 'Auth/register.html')


        # Vérification des mots de passe identiques
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'Auth/register.html')

        # ✅ Validation sécurité mot de passe
        try:
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
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
            accepted_terms=True,
        )

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
    
    
############################################################################

"""""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.conf import settings
from blog.models import User
from global_data.email_util import EmailUtil
from global_data.enum import UserStatus
import logging

logger = logging.getLogger(__name__)

class RegisterView(View):
    def get(self, request):
        return render(request, 'auth/registration.html')

    def post(self, request):
        data = request.POST
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password') # Frontend check should handle match, but good to have here too
        account_type = data.get('account_type', 'reader')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'auth/registration.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return render(request, 'auth/registration.html')
        
        # Create inactive user
        username = email.split('@')[0] # Simple username generation
        # Ensure unique username
        if User.objects.filter(username=username).exists():
            username = f"{username}_{get_random_string(4)}"

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=account_type, # Ensure mapping is correct or direct string if choices match
            account_status=UserStatus.INACTIVE, # Wait for verification
            is_active=False
        )

        # Generate Verification Code
        code = get_random_string(length=6, allowed_chars='0123456789')
        user.meta['verification_code'] = code
        user.save()

        # Send Email
        email_util = EmailUtil(prod=True) # Assuming prod=True for now to actually send/log
        subject = "Verify your email - Insightful Blog"
        
        verification_url = f"{request.build_absolute_uri(reverse('verify_email'))}?code={code}&email={email}"
        context = {
            'user': user, 
            'code': code,
            'verification_url': verification_url
        }
        
        email_util.send_email_with_template(
            template='email/account_verification.html',
            context=context,
            receivers=[email],
            subject=subject
        )

        # Store email in session to pre-fill verification page
        request.session['verification_email'] = email
        return redirect('verify_email')

class LoginView(View):
    def get(self, request):
        return render(request, 'auth/login.html')

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Allow login with email. Django authenticate usually expects username.
        # We might need a custom backend or find user by email first.
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            user_obj = None

        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.first_name}!")
                    return redirect('user_dashboard') # Redirect to dashboard
                else:
                    messages.error(request, "Account is inactive. Please verify your email.")
                    request.session['verification_email'] = email
                    return redirect('verify_email')
            else:
                 messages.error(request, "Invalid credentials.")
        else:
            messages.error(request, "Invalid credentials.")

        return render(request, 'auth/login.html')

class VerifyEmailView(View):
    def get(self, request):
        email = request.GET.get('email', request.session.get('verification_email'))
        code = request.GET.get('code')
        
        if email and code:
            # Auto verify if link clicked
            return self.verify(request, email, code)

        return render(request, 'auth/verify_email.html', {'email': email})

    def post(self, request):
        email = request.POST.get('email')
        code = request.POST.get('code')
        return self.verify(request, email, code)

    def verify(self, request, email, code):
        try:
            user = User.objects.get(email=email)
            saved_code = user.meta.get('verification_code')
            
            if saved_code and saved_code == code:
                user.is_active = True
                user.account_status = UserStatus.ACTIVE
                user.meta['verification_code'] = None # Clear code
                user.save()
                
                # Auto login? Or redirect to login
                login(request, user)
                messages.success(request, "Email verified successfully!")
                return redirect('user_dashboard')
            else:
                messages.error(request, "Invalid verification code.")
                return render(request, 'auth/verify_email.html', {'email': email})
                
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('register')

"""