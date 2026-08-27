"""
email_service.py
Universal Multi-Provider Email Dispatcher for InvestPro Account Credentials
Supports Port 465 (SSL), Port 587 (TLS), Resend API, and Brevo API
"""

import os
import smtplib
import logging
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("EmailService")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_USER = os.getenv("SMTP_USER", "deadshot11276@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "fcaedecpeiugywyd")
SMTP_FROM = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "deadshot11276@gmail.com"))


def send_credentials_email(to_email: str, user_name: str, mobile: str, temp_password: str) -> tuple[bool, str]:
    """
    Send HTML email with account login credentials directly to the registered email.
    Returns (success: bool, detail_message: str).
    """
    to_email_clean = (to_email or "").strip().lower()
    if not to_email_clean or "@" not in to_email_clean:
        logger.warning(f"Invalid recipient email: {to_email}")
        return False, f"Invalid recipient email: {to_email}"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #080912; color: #ffffff; padding: 24px; }}
        .container {{ max-width: 500px; margin: 0 auto; background: #101328; border: 1px solid #2d3160; border-radius: 16px; padding: 32px; box-shadow: 0 10px 40px rgba(0,0,0,0.5); }}
        .logo {{ font-size: 24px; font-weight: 800; color: #ffffff; margin-bottom: 20px; text-align: center; }}
        .cred-box {{ background: rgba(59, 130, 246, 0.1); border: 1.5px solid #3b82f6; border-radius: 12px; padding: 20px; margin: 20px 0; }}
        .cred-item {{ margin-bottom: 12px; }}
        .cred-label {{ font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: 700; letter-spacing: 0.5px; }}
        .cred-val {{ font-size: 16px; font-weight: 700; color: #60a5fa; margin-top: 2px; font-family: monospace; }}
        .btn {{ display: block; background: linear-gradient(135deg, #3b82f6, #6366f1); color: #ffffff !important; text-decoration: none; padding: 13px 24px; border-radius: 8px; font-weight: 700; font-size: 14px; margin-top: 18px; text-align: center; }}
        .footer {{ font-size: 11px; color: #64748b; margin-top: 24px; text-align: center; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 16px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">📈 Invest<span style="color: #60a5fa;">Pro</span></div>
        <h2 style="margin: 0 0 12px 0; font-size: 18px; color: #ffffff;">Your Account Login Credentials</h2>
        <p style="font-size: 13.5px; color: #cbd5e1; line-height: 1.5;">Hello <strong>{user_name}</strong>,</p>
        <p style="font-size: 13px; color: #94a3b8; line-height: 1.5;">Here are your InvestPro account login credentials:</p>
        
        <div class="cred-box">
            <div class="cred-item">
                <div class="cred-label">Mobile Number</div>
                <div class="cred-val">+91 {mobile}</div>
            </div>
            <div class="cred-item">
                <div class="cred-label">Registered Email</div>
                <div class="cred-val">{to_email_clean}</div>
            </div>
            <div class="cred-item" style="margin-bottom: 0;">
                <div class="cred-label">Password</div>
                <div class="cred-val" style="color: #34d399; font-size: 18px;">{temp_password}</div>
            </div>
        </div>
        
        <p style="font-size: 12px; color: #94a3b8;">You can now sign in to your terminal using either your Mobile Number or Email ID.</p>
        
        <a href="https://investpro-6jp.pages.dev" class="btn">Sign In to InvestPro Terminal &rarr;</a>
        
        <div class="footer">
            © 2026 InvestPro AI Market Terminal. All rights reserved.
        </div>
    </div>
</body>
</html>"""

    sender_addr = (SMTP_USER or "").strip()
    sender_pass = (SMTP_PASS or "").strip().replace(" ", "")

    errors = []

    # 1. Try SSL direct on Port 465
    if SMTP_HOST and sender_addr and sender_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Your InvestPro Account Login Credentials"
            msg["From"] = f"InvestPro Security <{sender_addr}>"
            msg["To"] = to_email_clean
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP_SSL(SMTP_HOST, 465, timeout=10) as server:
                server.login(sender_addr, sender_pass)
                server.sendmail(sender_addr, [to_email_clean], msg.as_string())

            logger.info(f"✅ [EmailService] Credentials email sent via SSL (465) to {to_email_clean}")
            return True, f"Sent via SSL 465 to {to_email_clean}"
        except Exception as e_ssl:
            errors.append(f"SSL_465_ERROR: {str(e_ssl)}")
            logger.warning(f"⚠️ [EmailService] SSL 465 attempt failed: {e_ssl}")

    # 2. Try TLS on Port 587
    if SMTP_HOST and sender_addr and sender_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Your InvestPro Account Login Credentials"
            msg["From"] = f"InvestPro Security <{sender_addr}>"
            msg["To"] = to_email_clean
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(SMTP_HOST, 587, timeout=10) as server:
                server.starttls()
                server.login(sender_addr, sender_pass)
                server.sendmail(sender_addr, [to_email_clean], msg.as_string())

            logger.info(f"✅ [EmailService] Credentials email sent via TLS (587) to {to_email_clean}")
            return True, f"Sent via TLS 587 to {to_email_clean}"
        except Exception as e_tls:
            errors.append(f"TLS_587_ERROR: {str(e_tls)}")
            logger.error(f"❌ [EmailService] TLS 587 attempt failed: {e_tls}")

    # 3. Try Resend API (HTTPS)
    if RESEND_API_KEY:
        try:
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
                json={
                    "from": "InvestPro <onboarding@resend.dev>",
                    "to": [to_email_clean],
                    "subject": "Your InvestPro Account Login Credentials",
                    "html": html_content
                },
                timeout=10
            )
            if resp.status_code in (200, 201):
                logger.info(f"✅ [EmailService] Email sent via Resend API to {to_email_clean}")
                return True, f"Sent via Resend API to {to_email_clean}"
            else:
                errors.append(f"RESEND_ERROR_{resp.status_code}: {resp.text}")
        except Exception as e:
            errors.append(f"RESEND_EXC: {str(e)}")

    logger.error(f"❌ [EmailService] All email dispatch methods failed: {errors}")
    return False, f"Failed: {'; '.join(errors)}"
