from pydantic import BaseModel, Field

class SignUp(BaseModel):
    username: str = Field(max_length=24, min_length=4)
    password: str = Field(max_length=128, min_length=8)