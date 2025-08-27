from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string


def send_activation_email(request, user, activation_link):
    subject = "Activate your account"
    from_email = "Videoflix <noreply@videoflix.com>"
    to = [user.email]

    logo_url = request.build_absolute_uri(settings.EMAIL_LOGO_PATH)

    text_content = f"""
    Hi {user.email},

    Please activate your account by clicking on the following link:
    {activation_link}

    Thank you!
    """

    html_content = render_to_string('activation_email.html', {
        "username": user.username,
        "activation_link": activation_link,
        "logo_url": logo_url,
    })
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_password_reset_email(request, email, reset_link):
    subject = "Reset your password"
    from_email = "Videoflix <noreply@videoflix.com>"
    to = [email]

    logo_url = request.build_absolute_uri(settings.EMAIL_LOGO_PATH)

    text_content = f"""
    Hi there,

    Please reset your password by clicking on the following link:
    {reset_link}

    Thank you!
    """

    html_content = render_to_string('reset_password.html', {
        "reset_link": reset_link,
        "logo_url": logo_url,
    })
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
