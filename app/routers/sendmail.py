"""
OTP email delivery — NOT IMPLEMENTED.

This stub does not send real email. It just prints the OTP to the console
so you can test the /register -> /verify-otp flow locally without an email
provider wired up.

To make this real, plug in a provider here, e.g.:
    - SMTP (smtplib)
    - SendGrid / Mailgun / Postmark / SES API
and raise an exception on failure so /register can roll back the OTP row.
"""


def send_email(email: str, otp: str) -> None:
    print(f"[sendmail stub] Would send OTP {otp} to {email} (no email provider configured)")
