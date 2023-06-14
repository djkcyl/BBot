from typing import Optional
from pydantic import BaseModel


class CaptchaData(BaseModel):
    captcha_id: str
    points: list[list[int]]
    rectangles: list[list[int]]
    yolo_data: list[list[int]]
    time: int


class CaptchaResponse(BaseModel):
    code: int
    message: str
    data: Optional[CaptchaData]
