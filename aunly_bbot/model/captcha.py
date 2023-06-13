from typing import Optional
from pydantic import BaseModel


class CaptchaData(BaseModel):
    points: list[list[int]]
    rectangles: list[list[int]]
    yolo_data: list[list[int]]
    time: int


class CaptchaResponse(BaseModel):
    code: int
    message: str
    data: Optional[CaptchaData]
