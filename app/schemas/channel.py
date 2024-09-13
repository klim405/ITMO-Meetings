from pydantic import BaseModel, Field


class ChannelBase(BaseModel):
    name: str = Field(max_lenfgth=100, pattern=r'^[\w\s\d]+$', examples=['My super channel name'])
    description: str | None = Field(default=None, examples=['Here plain text'])
    is_public: bool = False


class CreateChannel(ChannelBase):
    pass


class UpdateChannel(ChannelBase):
    pass


class RecoveryChannel(BaseModel):
    is_active: bool


class ReadChannel(ChannelBase):
    id: int
    members_cnt: int = 0
    rating: int | None = None
    is_personal: bool = False
    is_public: bool = False
    is_active: bool = True
