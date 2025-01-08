from pydantic import BaseModel, Field


class FeedbackBase(BaseModel):
    rate: int = Field(ge=0, le=5)


class ReadFeedback(FeedbackBase):
    user_id: int
    meeting_id: int
    rate: int = Field(ge=0, le=5)

    class Config:
        from_attributes = True
