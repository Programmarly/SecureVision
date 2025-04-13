from pydantic import BaseModel, field_validator, HttpUrl
from typing import List, Dict

class PayloadForRegister(BaseModel):
    email: str
    cctv_names: List[str] # List of {"name": "cctv1", "rtsp_url": "rtsp://..."}

    @field_validator("email")
    @classmethod
    def email_validator(cls, email):
        if "@" not in email or "." not in email.split("@")[-1]:  # Basic email validation
            raise ValueError("Invalid email format")
        return email


