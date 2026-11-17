import os, smtplib, ssl, logging
from email.message import EmailMessage

log = logging.getLogger("msanii.mail")
def admin_email(): return os.getenv("MSANII_NOTIFICATION_EMAIL") or os.getenv("MSANII_ADMIN_EMAIL") or ""   # recipient of access-request notices; no hard-coded default

def configured():
    return bool(os.getenv("MSANII_SMTP_HOST"))

def _dispatch_email(to_email, subject, body_text):
    if not to_email: return False
    if not configured():
        log.info("e-mail not sent (SMTP not configured): to=%s subject=%s", to_email, subject)   # body deliberately not logged: it may contain links
        return False
    try:
        m = EmailMessage()
        m["Subject"] = subject
        m["From"] = os.getenv("MSANII_SMTP_FROM", "msanii@soundscout.ai")
        m["To"] = to_email
        m.set_content(body_text)
        with smtplib.SMTP(os.getenv("MSANII_SMTP_HOST"), int(os.getenv("MSANII_SMTP_PORT", "587")), timeout=15) as s:
            s.starttls(context=ssl.create_default_context())
            if os.getenv("MSANII_SMTP_USER"):
                s.login(os.getenv("MSANII_SMTP_USER"), os.getenv("MSANII_SMTP_PASSWORD", ""))
            s.send_message(m)
        return True
    except Exception as e:
        log.warning(f"Failed to dispatch email to {to_email}: {e}")
        return False

def send_invite(to, token, role):
    base = os.getenv("MSANII_BASE_URL", "http://localhost:5000").rstrip("/")
    subject = "You are invited to MSANII A&R Intelligence"
    body = (
        f"Hello,\n\n"
        f"You have been invited to join the MSANII platform as a {role}.\n\n"
        f"Accept your invitation and set up your secure password within 72 hours:\n"
        f"{base}/?invite={token}\n\n"
        f"— MSANII Operations Team"
    )
    return _dispatch_email(to, subject, body)

def send_access_request_notification(req_dict):
    """Tells the administrator that someone asked for access. Approval itself happens inside the app (admin session + CSRF),
    never through a link in this e-mail, so a forwarded or pre-fetched message cannot grant access."""
    base = os.getenv("MSANII_BASE_URL", "http://localhost:5000").rstrip("/")
    subject = f"[MSANII Access Request] {req_dict['full_name']} from {req_dict.get('organization') or 'Independent'}"
    body = (
        f"Hello,\n\n"
        f"A new access request was submitted for the MSANII A&R platform:\n\n"
        f"Applicant:     {req_dict['full_name']}\n"
        f"Work e-mail:   {req_dict['email']}\n"
        f"Organization:  {req_dict.get('organization') or 'Not specified'}\n"
        f"Role / title:  {req_dict.get('role_title') or 'Not specified'}\n"
        f"Territory:     {req_dict.get('region') or 'Not specified'}\n"
        f"Notes:         {req_dict.get('notes') or 'None'}\n\n"
        f"Review and approve it after signing in as an administrator (Settings > Team & Access):\n"
        f"{base}/\n\n"
        f"— MSANII"
    )
    return _dispatch_email(admin_email(), subject, body)

def send_access_approved(to_email, full_name, invite_token, hours=72):
    """Sends the approved applicant a single-use invite link; they choose their own password. No password is ever e-mailed."""
    base = os.getenv("MSANII_BASE_URL", "http://localhost:5000").rstrip("/")
    subject = "Your MSANII access has been approved"
    body = (
        f"Hello {full_name},\n\n"
        f"Your request for access to MSANII has been approved.\n\n"
        f"Set your password and sign in within {hours} hours (single-use link):\n"
        f"{base}/?invite={invite_token}\n\n"
        f"Guidelines\n"
        f"- Scope: upcoming artists (active about five years or less).\n"
        f"- Every figure shows its source, date and method. Where data is missing the platform says so instead of estimating.\n"
        f"- Audience anomalies are signals to investigate, never accusations.\n"
        f"- Upload only audio you are licensed to analyse. Exported dossiers are confidential.\n\n"
        f"— The MSANII team\n"
    )
    return _dispatch_email(to_email, subject, body)
