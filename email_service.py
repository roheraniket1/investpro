"""
email_service.py
Email Dispatcher for InvestPro Login Credentials & Account Recovery
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
SMTP_FROM = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "support@investpro.in"))


def send_credentials_email(to_email: str, user_name: str, mobile: str, temp_password: str) -> bool:
    """
    Send HTML email with account login credentials directly to the registered email.
    """
    if not to_email or "@" not in to_email:
        logger.warning(f"Invalid recipient email: {to_email}")
        return False

    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
        logger.info(f"📧 [EmailService] Credentials email prepared for {to_email} (Mobile: {mobile}, TempPass: {temp_password}).")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your InvestPro Account Login Credentials"
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
                .cred-box {{ background: rgba(59, 130, 246, 0.1); border: 1.5px solid #3b82f6; border-radius: 12px; padding: 20px; margin: 20px 0; }}
                .cred-item {{ margin-bottom: 12px; }}
                .cred-label {{ font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: 700; letter-spacing: 0.5px; }}
                .cred-val {{ font-size: 16px; font-weight: 700; color: #60a5fa; margin-top: 2px; font-family: monospace; }}
                .btn {{ display: inline-block; background: linear-gradient(135deg, #3b82f6, #6366f1); color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 14px; margin-top: 15px; text-align: center; }}
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
                        <div class="cred-val">{to_email}</div>
                    </div>
                    <div class="cred-item" style="margin-bottom: 0;">
                        <div class="cred-label">Password</div>
                        <div class="cred-val" style="color: #34d399; font-size: 18px;">{temp_password}</div>
                    </div>
                </div>
                
                <p style="font-size: 12px; color: #94a3b8;">You can now sign in to your terminal using either your Mobile Number or Email ID.</p>
                
                <div style="text-align: center;">
                    <a href="https://investpro-6jp.pages.dev" class="btn">Sign In to InvestPro Terminal</a>
                </div>
                
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

        logger.info(f"✅ [EmailService] Login credentials email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"❌ [EmailService] Failed to send credentials email to {to_email}: {e}")
        return False
