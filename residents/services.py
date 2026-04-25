from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client


def send_access_code(request_obj):
    """Send the access code to the resident via email and SMS."""
    resident = request_obj.resident
    code = request_obj.access_code
    visitor_name = request_obj.visitor_name
    subject = f"Access code for {visitor_name}"
    message = (
        f"Hello {resident.name},\n\n"
        f"{visitor_name} (phone: {request_obj.visitor_phone}) is requesting access.\n"
        f"Their unique code is: {code}\n\n"
        f"This code expires in 24 hours and can be used only once.\n"
        f"Share it with your visitor if you approve."
    )
    # Email
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [resident.email])

    # SMS via Twilio
    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        sms_body = f"Access code for {visitor_name}: {code} (valid 24h, one use)"
        try:
            client.messages.create(
                body=sms_body, from_=settings.TWILIO_PHONE_NUMBER, to=resident.phone
            )
        except Exception as e:
            print(f"Twilio error: {e}")


def send_gate_confirmation(request_obj):
    """Send confirmation email to resident when code is used at gate."""
    resident = request_obj.resident
    subject = f"Gate access used - {request_obj.access_code}"
    message = (
        f"Hello {resident.name},\n\n"
        f"The access code for {request_obj.visitor_name} was successfully used at the gate on {request_obj.used_at}.\n"
        f"Thank you."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [resident.email])
