from accounts.models import Profile
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from .models import *
import uuid
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

@login_required(login_url='/login/')
def home(request):
    return render(request, 'home.html')

def login_attempt(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user_obj = User.objects.filter(username=username).first()
        if user_obj is None:
            messages.success(request, 'User not found.')
            return redirect('login_attempt')
        
        profile_obj = Profile.objects.filter(user=user_obj).first()
        if not profile_obj.is_verified:
            messages.success(request, 'Profile is not verified check your mail.')
            return redirect('login_attempt')

        user = authenticate(username=username, password=password)
        if user is None:
            messages.success(request, 'Wrong password.')
            return redirect('login_attempt')
        
        login(request, user)
        return redirect('/')

    return render(request, 'login.html')

def register_attempt(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        print(password)

        try:
            if User.objects.filter(username=username).first():
                messages.success(request, 'Username is taken.')
                return redirect('/register')

            if User.objects.filter(email=email).first():
                messages.success(request, 'Email is taken.')
                return redirect('/register')
            
            user_obj = User(username=username, email=email)
            user_obj.set_password(password)
            user_obj.save()
            auth_token = str(uuid.uuid4())
            profile_obj = Profile.objects.create(user=user_obj, auth_token=auth_token)
            profile_obj.save()
            send_mail_after_registration(email, auth_token)
            return redirect('/token')

        except Exception as e:
            print(e)

    return render(request, 'register.html')

def success(request):
    return render(request, 'success.html')

def token_send(request):
    return render(request, 'token_send.html')

def verify(request, auth_token):
    try:
        profile_obj = Profile.objects.filter(auth_token=auth_token).first()
        if profile_obj:
            if profile_obj.is_verified:
                messages.success(request, 'Your account is already verified.')
                return redirect('login_attempy')
            profile_obj.is_verified = True
            profile_obj.save()
            messages.success(request, 'Your account has been verified.')
            return redirect('login_attempt')
        else:
            return redirect('/error')
    except Exception as e:
        print(e)
        return redirect('/')

def error_page(request):
    return render(request, 'error.html')

def Logout(request):
    logout(request)
    return redirect('login_attempt')

def forgotPassword(request):
    try:
        if request.method == "POST":
            username = request.POST.get('username')
            if not User.objects.filter(username=username).first():
                messages.success(request, 'No such user Found')
                return redirect('/forgot-password')
            
            user_obj = User.objects.get(username=username)
            token = str(uuid.uuid4())
            profile_obj = Profile.objects.get(user=user_obj)
            profile_obj.forgot_pass_token = token
            profile_obj.save()
            send_mail_forgot_password(user_obj.email, token)
            print(user_obj.email)
            messages.success(request, "An Email was sent")
            return redirect('/forgot-password/')
        
    except Exception as e:
        print(e)
    
    return render(request, 'forgot-password.html')

def changePassword(request, token):
    context = {}
    try:
        profile_obj = Profile.objects.filter(forgot_pass_token=token).first()
        # print(profile_obj)
        if request.method == "POST":
            new_pass = request.POST.get('new_password')
            confirm_pass = request.POST.get('confirm_password')
            user_id = request.POST.get('user_id')
            
            if user_id is None:
                messages.success(request, '')
                return redirect(f'/change-password/{token}/')
            
            if new_pass != confirm_pass:
                messages.success(request, 'The passwords did not match')
                return redirect(f'/change-password/{token}/')
        
            user_obj = User.objects.get(id=user_id)
            user_obj.set_password(new_pass)
            user_obj.save()
            return redirect('login_attempt')
        
        context = {'user_id': profile_obj.user.id}
        print(context)
    except Exception as e:
        print(e)
    
    return render(request, 'change-password.html', context)

def send_mail_forgot_password(email, token):
    subject = 'Forgot Password'
    message = f'Click this link to reset your password: http://127.0.0.1:8000/change-password/{token}/'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)
    return True

def send_mail_after_registration(email, token):
    subject = 'Your account needs to be verified'
    message = f'Hi, paste the link to verify your account: http://127.0.0.1:8000/verify/{token}/'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)
