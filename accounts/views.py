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
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to the Islamic Digital Library, {user.username}!")
            return redirect("library:home")
        return render(request, "accounts/signup.html", {"form": form})
