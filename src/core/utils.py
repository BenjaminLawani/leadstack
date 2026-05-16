import httpx
from slowapi import Limiter
from slowapi.util import get_ipaddr

from .config import settings


class EmailService:
    def __init__(self):
        self.api_key = settings.MAIL_PASSWORD
        self.from_email = settings.MAIL_FROM
        self.from_name = settings.MAIL_FROM_NAME

    async def send_email(
        self,
        subject: str,
        recipients: list[str],
        body: str,
    ):
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": f"{self.from_name} <{self.from_email}>",
                    "to": recipients,
                    "subject": subject,
                    "html": body,
                },
            )

            response.raise_for_status()
            return response.json()


fm = EmailService()

limiter = Limiter(key_func=get_ipaddr)