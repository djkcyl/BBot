from pydantic import BaseModel


class OpenAI(BaseModel):
    error: bool = False
    message: str = ""
    response: str = ""
    raw: dict = {}
