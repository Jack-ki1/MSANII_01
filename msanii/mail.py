import os, smtplib, ssl, logging
from email.message import EmailMessage

log = logging.getLogger("msanii.mail")
TARGET_ADMIN_EMAIL = os.getenv("MSANII_NOTIFICATION_EMAIL", "kimothojackson1125@gmail.com")

def configured():
    return bool(os.getenv("MSANII_SMTP_HOST"))

def _dispatch_email(to_email, subject, body_text):
    if not configured():
        log.info(f"[MOCK EMAIL - SMTP Not Configured]\nTo: {to_email}\nSubject: {subject}\n{body_text}\n" + "="*50)
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
    """
    Sends notification to kimothojackson1125@gmail.com when a new user requests access.
    Includes one-click approval and reject links.
    """
    base = os.getenv("MSANII_BASE_URL", "http://localhost:5000").rstrip("/")
    token = req_dict["token"]
    approve_url = f"{base}/api/auth/approve-access?token={token}&action=approve"
    reject_url = f"{base}/api/auth/approve-access?token={token}&action=reject"
    admin_url = f"{base}/?tab=settings"

    subject = f"[MSANII Access Request] {req_dict['full_name']} from {req_dict.get('organization') or 'Independent'}"
    body = (
        f"Hello Jackson,\n\n"
        f"A new user has submitted an access request for MSANII A&R Intelligence Platform:\n\n"
        f"---------------------------------------------------\n"
        f"Applicant Name:   {req_dict['full_name']}\n"
        f"Work Email:       {req_dict['email']}\n"
        f"Organization:     {req_dict.get('organization') or 'Not specified'}\n"
        f"Role / Title:     {req_dict.get('role_title') or 'A&R Scout'}\n"
        f"Territory:        {req_dict.get('region') or 'East Africa'}\n"
        f"Purpose / Notes:  {req_dict.get('notes') or 'None provided'}\n"
        f"---------------------------------------------------\n\n"
        f"ONE-CLICK APPROVE LINK:\n"
        f"{approve_url}\n\n"
        f"ONE-CLICK REJECT LINK:\n"
        f"{reject_url}\n\n"
        f"Or review inside your MSANII Admin Settings:\n"
        f"{admin_url}\n\n"
        f"When approved, the applicant will automatically receive their temporary password "
        f"and onboarding guidelines.\n\n"
        f"— MSANII Gatekeeper Engine"
    )
    return _dispatch_email(TARGET_ADMIN_EMAIL, subject, body)

def send_access_approved(to_email, full_name, temp_password, guidelines_text=""):
    """
    Sends the approved user their password and access guidelines.
    """
    base = os.getenv("MSANII_BASE_URL", "http://localhost:5000").rstrip("/")
    subject = "MSANII Access Approved: Your Credentials and Guidelines"
    body = (
        f"Hello {full_name},\n\n"
        f"Your request for access to MSANII has been approved by Jackson Kimotho.\n\n"
        f"ACCESS CREDENTIALS:\n"
        f"Login Portal:   {base}/\n"
        f"Email:          {to_email}\n"
        f"Password:       {temp_password}\n\n"
        f"Please sign in and change your password upon first entry.\n\n"
        f"===================================================\n"
        f"MSANII OPERATIONAL GUIDELINES & A&R PROTOCOL\n"
        f"===================================================\n"
        f"1. SCOPE MANDATE:\n"
        f"   MSANII is strictly dedicated to UPCOMING ARTISTS (active <= 5 years).\n"
        f"   Established catalog acts and legacy artists are outside platform scope.\n\n"
        f"2. EVALUATION PILLARS (AVM):\n"
        f"   - Vocal Holding & Intonation (CREPE f0 cent deviation)\n"
        f"   - Multilingual Writing Arc (Sheng, Kiswahili, English code-switching)\n"
        f"   - Song Dynamics & Waveform Lift (RMS step dynamics)\n"
        f"   - Compositional & Harmonic Tessitura\n\n"
        f"3. FRAUD & BOT INTEGRITY:\n"
        f"   All audience spikes are audited against stream-to-follower ratios (Safe Zone: 1.5x - 4.2x).\n"
        f"   Do not pursue unverified spikes without checking UGC creator diversity.\n\n"
        f"4. DATA GOVERNANCE:\n"
        f"   Song Lab analysis is restricted to rights-cleared audio materials.\n"
        f"   Exported intelligence dossiers are confidential.\n\n"
        f"{guidelines_text}\n"
        f"Welcome aboard.\n\n"
        f"— Jackson Kimotho & The MSANII Team\n"
    )
    return _dispatch_email(to_email, subject, body)
