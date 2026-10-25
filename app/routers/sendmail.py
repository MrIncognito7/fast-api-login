"""
OTP email delivery — NOT IMPLEMENTED.

This stub does not send real email. It prints the OTP to the console and
also keeps the most recent OTP per address in memory (`_sent_otps`), so
tests and local development can retrieve it without scraping stdout or
wiring up a real mailbox.

To make this real, plug a provider in here, e.g.:
    - SMTP (smtplib)
    - SendGrid / Mailgun / Postmark / SES API
and raise an exception on failure so /register and /resend-otp can roll
back the OTP row.
"""

# email -> most recently generated OTP. In-memory only, cleared on restart.
# Not meant for production use — real deployments should actually email
# the code instead of relying on this.
_sent_otps: dict[str, str] = {}


def send_email(email: str, otp: str) -> None:
    _sent_otps[email] = otp
    print(f"[sendmail stub] Would send OTP {otp} to {email} (no email provider configured)")


def get_last_otp(email: str) -> str | None:
    """Dev/test helper — NOT available in a real deployment. Returns the
    most recently generated OTP for an address, or None."""
    return _sent_otps.get(email)
