from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(max_length=20, pattern=r"^[А-ЯA-Z][а-яa-z]+$", examples=["Sport"])


class Category(CategoryBase):
    id: int
