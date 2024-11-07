import base64
import logging
import os
from typing import List, Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, To, Content, Attachment, FileContent, 
    FileName, FileType, Disposition
)
from pydantic import BaseModel
from llama_index.core.tools import FunctionTool
import requests

logger = logging.getLogger("uvicorn")


class EmailResult(BaseModel):
    success: bool
    error_message: Optional[str] = None


class SendGridEmailTool:
    def __init__(self, api_key: Optional[str] = None, sender_email: Optional[str] = None):
        if api_key is None:
            api_key = os.getenv("SENDGRID_API_KEY")
        if sender_email is None:
            sender_email = os.getenv("SENDER_EMAIL")
            
        if not api_key:
            raise ValueError(
                "SENDGRID_API_KEY is required to send emails. Get it here: https://signup.sendgrid.com/"
            )
        if not sender_email:
            raise ValueError(
                "SENDER_EMAIL is required. This must be a verified sender in your SendGrid account."
            )

        try:
            # Verify SendGrid is installed
            import sendgrid
        except ImportError:
            raise ImportError(
                "SendGrid package is not installed. Please install it with: pip install sendgrid"
            )

        self.FILESERVER_URL_PREFIX = os.getenv("FILESERVER_URL_PREFIX")
        self.sg = SendGridAPIClient(api_key=api_key)
        self.from_email = Email(sender_email)

    def send_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        pdf_path: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> EmailResult:
        """
        Send an email using SendGrid API with optional PDF attachment.

        Parameters:
            to_email (str): Recipient email address
            subject (str): Email subject line
            content (str): Email body (HTML supported)
            pdf_path (str, optional): Path to PDF file to attach
            cc (List[str], optional): List of CC recipients
            bcc (List[str], optional): List of BCC recipients

        Returns:
            EmailResult: Object containing success status and any error message
        """
        try:
            logger.info(f"Sending email to {to_email} with subject: {subject}")
            
            to_email = To(to_email)
            content = Content("text/html", content)
            mail = Mail(self.from_email, to_email, subject, content)

            # Add PDF attachment if provided
            if pdf_path:
                # Check if pdf_path is a URL (starts with http:// or https://)
                if pdf_path.startswith(('http://', 'https://')):
                    try:
                        response = requests.get(pdf_path)
                        response.raise_for_status()  # Raise exception for bad status codes
                        file_content = response.content
                    except Exception as e:
                        error_msg = f"Failed to download PDF from URL: {str(e)}"
                        logger.error(error_msg)
                        return EmailResult(success=False, error_message=error_msg)
                else:
                    # Handle local file path
                    if not os.path.exists(pdf_path):
                        logger.error(f"PDF file not found at path: {pdf_path}")
                        return EmailResult(
                            success=False,
                            error_message=f"PDF file not found at path: {pdf_path}"
                        )
                    
                    with open(pdf_path, 'rb') as f:
                        file_content = f.read()
                
                encoded_file = base64.b64encode(file_content).decode()
                
                attachedFile = Attachment(
                    FileContent(encoded_file),
                    FileName(os.path.basename(pdf_path)),
                    FileType('application/pdf'),
                    Disposition('attachment')
                )
                mail.attachment = attachedFile

            # Add CC recipients if provided
            if cc:
                for cc_address in cc:
                    mail.add_cc(Email(cc_address))

            # Add BCC recipients if provided
            if bcc:
                for bcc_address in bcc:
                    mail.add_bcc(Email(bcc_address))

            logger.info(f"Sending email with request body: {mail.get()}")
            # Send email
            response = self.sg.client.mail.send.post(request_body=mail.get())
            
            if response.status_code not in [200, 201, 202]:
                logger.error(f"SendGrid API returned status code: {response.status_code}")
                return EmailResult(
                    success=False,
                    error_message=f"SendGrid API returned status code: {response.status_code}"
                )

            logger.info(f"Successfully sent email to {to_email}")
            return EmailResult(success=True)

        except Exception as e:
            error_message = f"Error sending email: {str(e)}"
            logger.error(error_message)
            return EmailResult(success=False, error_message=error_message)


def get_tools(**kwargs):
    return [FunctionTool.from_defaults(SendGridEmailTool(**kwargs).send_email)]
