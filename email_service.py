"""
email_service.py
Secure Email Dispatcher for InvestPro Password Reset & Verification Codes
Supports SMTP (Gmail, Outlook, AWS SES, Brevo, custom SMTP)
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("EmailService")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "noreply@investpro.in"))


def send_password_reset_email(to_email: str, user_name: str, otp_code: str) -> bool:
    """
    Send HTML email with 6-digit password reset OTP.
    Returns True if sent successfully, False otherwise.
    """
    if not to_email or "@" not in to_email:
        logger.warning(f"Invalid recipient email: {to_email}")
        return False

    # If no SMTP configured, log cleanly and return
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
        logger.info(f"📧 [EmailService] Password reset OTP generated for {to_email} (SMTP not configured in environment).")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"InvestPro - Password Reset Verification Code: {otp_code}"
        msg["From"] = f"InvestPro Security <{SMTP_FROM}>"
        msg["To"] = to_email

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #080912; color: #ffffff; padding: 20px; }}
                .container {{ max-width: 500px; margin: 0 auto; background: #101328; border: 1px solid #2d3160; border-radius: 16px; padding: 32px; box-shadow: 0 10px 40px rgba(0,0,0,0.5); }}
                .logo {{ font-size: 24px; font-weight: 800; color: #ffffff; margin-bottom: 20px; text-align: center; }}
                .otp-box {{ background: rgba(59, 130, 246, 0.12); border: 1.5px solid #3b82f6; border-radius: 12px; padding: 18px; text-align: center; font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #60a5fa; margin: 24px 0; }}
                .footer {{ font-size: 11px; color: #64748b; margin-top: 24px; text-align: center; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 16px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">📈 Invest<span style="color: #60a5fa;">Pro</span></div>
                <h2 style="margin: 0 0 12px 0; font-size: 18px; color: #ffffff;">Password Reset Verification</h2>
                <p style="font-size: 13.5px; color: #cbd5e1; line-height: 1.5;">Hello <strong>{user_name}</strong>,</p>
                <p style="font-size: 13px; color: #94a3b8; line-height: 1.5;">We received a request to reset your password. Use the 6-digit verification code below to set a new password:</p>
                
                <div class="otp-box">{otp_code}</div>
                
                <p style="font-size: 12px; color: #94a3b8;">This code is valid for <strong>15 minutes</strong>. If you did not request a password reset, please ignore this email.</p>
                
                <div class="footer">
                    © 2026 InvestPro Terminal. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, [to_email], msg.as_string())

        logger.info(f"✅ [EmailService] Password reset email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"❌ [EmailService] Failed to send email to {to_email}: {e}")
        return False
