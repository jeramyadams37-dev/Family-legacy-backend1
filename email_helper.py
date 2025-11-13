# Email helper for sending family invites using Replit Mail integration
# References: blueprint:replitmail

import os
import requests
import logging

logger = logging.getLogger(__name__)


def get_auth_token():
    """Get authentication token for Replit services"""
    repl_identity = os.environ.get('REPL_IDENTITY')
    web_repl_renewal = os.environ.get('WEB_REPL_RENEWAL')
    
    if repl_identity:
        return f"repl {repl_identity}"
    elif web_repl_renewal:
        return f"depl {web_repl_renewal}"
    else:
        raise Exception("No authentication token found. Please ensure you're running in Replit environment.")


def send_family_invite_email(recipient_email, family_name, invite_code, inviter_name, app_url):
    """
    Send a family invite email using Replit Mail
    
    Args:
        recipient_email: Email address of the person being invited
        family_name: Name of the family (surname)
        invite_code: The 8-character invite code
        inviter_name: Name of the person sending the invite
        app_url: Base URL of the application
    
    Returns:
        dict: Response from the email service
    """
    try:
        auth_token = get_auth_token()
        
        # Create beautiful HTML email
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .invite-code {{ background: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; border: 2px solid #667eea; }}
                .code {{ font-size: 32px; font-weight: bold; letter-spacing: 4px; color: #667eea; font-family: monospace; }}
                .button {{ display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: bold; }}
                .footer {{ text-align: center; color: #666; margin-top: 30px; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💝 You're Invited to Family Hub!</h1>
                </div>
                <div class="content">
                    <p>Hi there!</p>
                    <p><strong>{inviter_name}</strong> has invited you to join the <strong>{family_name} family</strong> on Family Hub - where families create golden legacies together!</p>
                    
                    <div class="invite-code">
                        <p style="margin: 0 0 10px 0; font-size: 14px; color: #666;">Your Invite Code:</p>
                        <div class="code">{invite_code}</div>
                    </div>
                    
                    <p><strong>How to join:</strong></p>
                    <ol>
                        <li>Click the button below to go to Family Hub</li>
                        <li>Sign in with your preferred account</li>
                        <li>Enter the invite code above when prompted</li>
                    </ol>
                    
                    <div style="text-align: center;">
                        <a href="{app_url}/family/setup" class="button">Join {family_name} Family</a>
                    </div>
                    
                    <p style="margin-top: 30px;"><strong>What is Family Hub?</strong></p>
                    <p>Family Hub helps families stay connected with:</p>
                    <ul>
                        <li>📅 Shared family calendar for events and celebrations</li>
                        <li>💬 Family messaging and video calls</li>
                        <li>📸 Photo galleries to preserve precious moments</li>
                        <li>🕊️ Remembrance pages to honor loved ones</li>
                        <li>🤖 AI-powered family helper for genealogy and planning</li>
                    </ul>
                    
                    <div class="footer">
                        <p>Turning Dynasties Into Golden Legacies 💝</p>
                        <p style="font-size: 12px; color: #999;">This invitation was sent by {inviter_name} via Family Hub</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
You're Invited to Family Hub!

{inviter_name} has invited you to join the {family_name} family on Family Hub!

Your Invite Code: {invite_code}

How to join:
1. Go to {app_url}/family/setup
2. Sign in with your preferred account
3. Enter the invite code: {invite_code}

What is Family Hub?
Family Hub helps families stay connected with shared calendars, messaging, photo galleries, remembrance pages, and more!

Turning Dynasties Into Golden Legacies 💝
        """
        
        # Send email via Replit Mail API
        response = requests.post(
            "https://connectors.replit.com/api/v2/mailer/send",
            headers={
                "Content-Type": "application/json",
                "X_REPLIT_TOKEN": auth_token,
            },
            json={
                "to": recipient_email,
                "subject": f"💝 You're invited to join the {family_name} family!",
                "html": html_content,
                "text": text_content,
            },
            timeout=30
        )
        
        if not response.ok:
            try:
                error_data = response.json()
                error_message = error_data.get('message', f'HTTP {response.status_code}')
            except Exception:
                error_message = f'HTTP {response.status_code}'
            raise Exception(f"Failed to send email: {error_message}")
        
        result = response.json()
        logger.info(f"Email invite sent to {recipient_email} for {family_name} family")
        return result
        
    except Exception as e:
        logger.error(f"Error sending invite email: {str(e)}")
        raise
