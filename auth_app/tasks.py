import logging
import smtplib
from django_rq import job
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


@job
def send_activation_email(request, user, activation_link):
    logger.info(f"🚀 Starte Email-Versand für User: {user.email}")
    try:
        subject = "Activate your account"
        from_email = f"Videoflix <{settings.DEFAULT_FROM_EMAIL}>"
        to = [user.email]

        logger.debug(f"From: {from_email}")
        logger.debug(f"To: {to}")
        logger.debug(f"Subject: {subject}")

        logo_url = request.build_absolute_uri(settings.EMAIL_LOGO_PATH)
        logger.debug(f"Logo URL: {logo_url}")

        text_content = f"""
        Hi {user.email},

        Please activate your account by clicking on the following link:
        {activation_link}

        Thank you!
        """

        logger.debug("📧 Lade HTML-Template...")
        html_content = render_to_string('activation_email.html', {
            "username": user.username,
            "activation_link": activation_link,
            "logo_url": logo_url,
        })
        logger.debug("✅ HTML-Template erfolgreich geladen")

        logger.debug("📨 Erstelle Email-Message...")
        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")

        logger.info(f"📤 Sende Email über SMTP Server: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")

        msg.send()

        logger.info(f"✅ Email erfolgreich versendet an: {user.email}")

        return True
    except Exception as e:
        logger.error(f"❌ Fehler beim Email-Versand an {user.email}: {str(e)}")
        logger.exception("📋 Vollständiger Stacktrace:")
        return False





def send_password_reset_email(request, email, reset_link):
    subject = "Reset your password"
    from_email = settings.DEFAULT_FROM_EMAIL
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





import socket

def check_internet():
    try:
        socket.create_connection(("www.google.com", 80))
        print("Internet connection is available.")
    except OSError:
        print("No Internet connection.")
