import base64, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Tuple, Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]


def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def search_messages(service, query: str, max_results: int = 200) -> List[str]:
    resp = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    return [m["id"] for m in resp.get("messages", [])]


def fetch_png_attachments(service, msg_id: str) -> List[Tuple[str, bytes, int]]:
    """
    Fetch PNG attachments from a Gmail message.
    Returns list of tuples: (filename, data, internal_date_timestamp)
    internal_date is Unix timestamp in milliseconds of when email was received.
    """
    msg = service.users().messages().get(userId="me", id=msg_id).execute()
    internal_date = msg.get("internalDate", "0")  # Unix timestamp in milliseconds (as string from API)
    attachments = []
    stack = (msg.get("payload", {}) or {}).get("parts", []) or []
    while stack:
        part = stack.pop()
        if part.get("parts"):
            stack.extend(part["parts"])
            continue
        filename = (part.get("filename") or "").lower()
        if not filename.endswith(".png"):
            continue
        body = part.get("body", {})
        att_id = body.get("attachmentId")
        if att_id:
            att = service.users().messages().attachments().get(
                userId="me", messageId=msg_id, id=att_id
            ).execute()
            data = base64.urlsafe_b64decode(att.get("data", b""))
            attachments.append((part.get("filename") or "attachment.png", data, internal_date))
    return attachments


def send_email(
    service,
    to: str,
    subject: str,
    body: str,
    attachment_path: Optional[str] = None
) -> bool:
    """
    Send an email using Gmail API.
    
    Args:
        service: Gmail service object from get_gmail_service()
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text or markdown)
        attachment_path: Optional path to file to attach
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create message
        if attachment_path and os.path.exists(attachment_path):
            message = MIMEMultipart()
            message["to"] = to
            message["subject"] = subject
            
            # Add body
            message.attach(MIMEText(body, "plain"))
            
            # Add attachment
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename= "{os.path.basename(attachment_path)}"'
                )
                message.attach(part)
        else:
            # Simple text email without attachment
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        
        # Send message
        service.users().messages().send(
            userId="me",
            body={"raw": raw_message}
        ).execute()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

