"""
Forms for user authentication.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


class SignupForm(UserCreationForm):
    """
    Custom signup form with email field and TailwindCSS styling.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "w-full px-4 py-3 rounded-xl border border-gray-200 "
                     "focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 "
                     "transition-all duration-200 bg-white",
            "placeholder": "your@email.com",
        })
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_class = (
            "w-full px-4 py-3 rounded-xl border border-gray-200 "
            "focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 "
            "transition-all duration-200 bg-white"
        )
        self.fields["username"].widget.attrs.update({
            "class": input_class,
            "placeholder": "Choose a username",
        })
        self.fields["password1"].widget.attrs.update({
            "class": input_class,
            "placeholder": "Create a password",
        })
        self.fields["password2"].widget.attrs.update({
            "class": input_class,
            "placeholder": "Confirm your password",
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """
    Custom login form with TailwindCSS styling.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_class = (
            "w-full px-4 py-3 rounded-xl border border-gray-200 "
            "focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 "
            "transition-all duration-200 bg-white"
        )
        self.fields["username"].widget.attrs.update({
            "class": input_class,
            "placeholder": "Your username",
        })
        self.fields["password"].widget.attrs.update({
            "class": input_class,
            "placeholder": "Your password",
        })
