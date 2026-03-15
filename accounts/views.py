"""
Views for user authentication (signup, login, logout).
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.views import View

from .forms import SignupForm


class SignupView(View):
    """Handle user registration."""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("library:home")
        form = SignupForm()
        return render(request, "accounts/signup.html", {"form": form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("library:home")
            
        form = SignupForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, f"Welcome to Bayt al-Hikmah Online, {user.username}! Your account has been created.")
                return redirect("library:home")
            except Exception as e:
                messages.error(request, "An error occurred during registration. Please try again.")
                return render(request, "accounts/signup.html", {"form": form})
        
        # If form is not valid, the template will display individual field errors
        return render(request, "accounts/signup.html", {"form": form})
