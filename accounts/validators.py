import phonenumbers
from django.core.exceptions import ValidationError

def validate_phone_number(value):
    try:
        z = phonenumbers.parse(value, None)
        if not phonenumbers.is_valid_number(z):
            raise ValidationError("Invalid Phone Number.")
    except phonenumbers.NumberParseException:
        raise ValidationError("Invalid phone number format.")