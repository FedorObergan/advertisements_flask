from pydantic import BaseModel, field_validator


class AdvBase(BaseModel):
    title: str | None = None
    description: str | None = None
    creator_email: str | None = None

    @field_validator("creator_email")
    @classmethod
    def check_password(cls, value):
        if '@mail.ru' not in value and '@yandex.ru' not in value:
            raise ValueError("incorrect email address")
        return value


class UpdateAdv(AdvBase):
    title: str | None = None
    description: str | None = None
    creator_email: str | None = None


class CreateAdv(AdvBase):
    title: str
    description: str
    creator_email: str
