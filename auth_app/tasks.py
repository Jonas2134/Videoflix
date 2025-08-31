from django_rq import job
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


@job
def send_email(user, subject, template_name, context, from_email=None):
    """
    Send an email to a user with both text and HTML content.

    :param user: User object (muss .email und .username haben)
    :param subject: Betreff der E-Mail
    :param template_name: HTML Template-Datei (z. B. 'activation_email.html')
    :param context: dict mit Variablen fürs Template
    :param from_email: Optional, falls kein Standard-From genutzt werden soll
    """
    from_email = from_email or f"Videoflix <{settings.DEFAULT_FROM_EMAIL}>"
    to = [user.email]

    text_content = f"Hi {user.username},\n\n"
    if "activation_link" in context:
        text_content += f"Please activate your account by clicking on the following link:\n{context['activation_link']}\n\nThank you!"
    elif "reset_link" in context:
        text_content += f"Please reset your password by clicking on the following link:\n{context['reset_link']}\n\nThank you!"
    else:
        text_content += "Please check your account.\n\nThank you!"

    html_content = render_to_string(template_name, context)

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
