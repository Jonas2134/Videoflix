from django.core.mail import send_mail


def send_activation_email(email, activation_link):
    subject = "Activate your account"
    message = f"Hi there,\n\nPlease activate your account by clicking on the following link:\n{activation_link}\n\nThank you!"
    send_mail(
        subject=subject,
        message=message,
        from_email='noreply@videoflix.com',
        recipient_list=[email],
        fail_silently=False,
    )
