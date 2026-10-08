from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SessionActionName = Literal[
    "end_external",
    "toggle_testing",
    "move_to_position",
    "execute",
    "advance",
]


class ApiResult(BaseModel):
    ok: bool
    status: int
    body: Any = None
    error: str | None = None


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    first_name: str | None = None
    last_name: str | None = None
    affiliation: str | None = None


class RunUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = None
    description: str | None = None
    footer_text: str | None = None
    public_blurb: str | None = None
    privacy: str | None = None
    tos: str | None = None
    header_image_path: str | None = None
    custom_css: str | None = None
    custom_js: str | None = None
    custom_r: str | None = None
    cron_active: bool | None = None
    use_material_design: bool | None = None
    expiresOn: str | None = None
    expire_cookie_value: int | None = None
    expire_cookie_unit: str | None = None
    public: int | None = Field(default=None, ge=0, le=1)
    locked: int | None = Field(default=None, ge=0, le=1)


class SurveyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    maximum_number_displayed: int | None = None
    displayed_percentage_maximum: int | None = None
    add_percentage_points: int | None = None
    expire_after: int | None = None
    expire_invitation_after: int | None = None
    expire_invitation_grace: int | None = None
    enable_instant_validation: int | None = Field(default=None, ge=0, le=1)
    unlinked: int | None = Field(default=None, ge=0, le=1)
    hide_results: int | None = Field(default=None, ge=0, le=1)
    use_paging: int | None = Field(default=None, ge=0, le=1)
    google_sheet: str | None = None


class SessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str | list[str] | None = None
    testing: bool = False


class SessionAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: SessionActionName
    testing: bool | None = None
    position: int | None = None

    @model_validator(mode="after")
    def required_fields(self) -> "SessionAction":
        if self.action == "move_to_position" and self.position is None:
            raise ValueError("position is required for move_to_position")
        if self.action == "toggle_testing" and self.testing is None:
            raise ValueError("testing is required for toggle_testing")
        return self


class SurveyUpload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    google_sheet: str | None = None
    filename: str | None = None
    content_base64: str | None = None

    @model_validator(mode="after")
    def one_source(self) -> "SurveyUpload":
        has_sheet = bool(self.google_sheet)
        has_file = bool(self.filename or self.content_base64)
        if has_sheet == has_file:
            raise ValueError("Provide either google_sheet or both filename and content_base64")
        if has_file and not (self.filename and self.content_base64):
            raise ValueError("filename and content_base64 are both required")
        return self


class FileUpload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filename: str = Field(min_length=1)
    content_base64: str = Field(min_length=1)
