from pydantic import BaseModel, field_validator
from typing import List, Dict
from pydantic import BaseModel, field_validator, ValidationError

class PayloadForRegister(BaseModel):
    email: str
    cctv_names: List[str]

    @field_validator("email")
    @classmethod
    def email_validator(cls, email):
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError("Invalid email format")
        return email
