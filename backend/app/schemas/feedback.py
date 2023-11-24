from pydantic import BaseModel, Field


class FeedbackBase(BaseModel):
    rate: int = Field(ge=0, le=5)


class CreateFeedback(FeedbackBase):
    pass


class Feedback(FeedbackBase):
    user_id: int
    meeting_id: int
    rate: int = Field(ge=0, le=5)

    class Config:
        orm_model = True
