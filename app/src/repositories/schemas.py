"""
Pydantic schemas for repository operations.

These schemas provide type-safe input validation for repository methods.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class EventCreateSchema(BaseModel):
    """Schema for creating a new event."""

    user_id: int = Field(..., description="Telegram user ID")
    title: str = Field(..., min_length=1, max_length=255, description="Event title")
    date_start: datetime = Field(..., description="Event start date and time")
    date_end: datetime = Field(..., description="Event end date and time")
    reminder_offset: int | None = Field(None, ge=0, description="Reminder offset in seconds")
    need_to_remind: bool = Field(True, description="Whether to send reminder")
    description: str | None = Field(None, max_length=1024, description="Event description")
    rrule: str | None = Field(None, max_length=255, description="Recurrence rule (RFC 5545)")
    calendar_id: int | None = Field(None, description="Associated calendar ID")

    @field_validator("date_end")
    @classmethod
    def validate_date_end(cls, v: datetime, info) -> datetime:
        """Validate that date_end is not before date_start."""
        if hasattr(info, "data") and "date_start" in info.data and v < info.data["date_start"]:
            raise ValueError("date_end must be after or equal to date_start")
        return v

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "user_id": 123456789,
                "title": "Meeting",
                "date_start": "2024-01-15T10:00:00Z",
                "date_end": "2024-01-15T11:00:00Z",
                "reminder_offset": 900,
                "need_to_remind": True,
                "description": "Team meeting",
            }
        }


class EventUpdateSchema(BaseModel):
    """Schema for updating an existing event.

    All fields are optional - only provided fields will be updated.
    """

    title: str | None = Field(None, min_length=1, max_length=255, description="Event title")
    date_start: datetime | None = Field(None, description="Event start date and time")
    date_end: datetime | None = Field(None, description="Event end date and time")
    reminder_offset: int | None = Field(None, ge=0, description="Reminder offset in seconds")
    need_to_remind: bool | None = Field(None, description="Whether to send reminder")
    description: str | None = Field(None, max_length=1024, description="Event description")
    rrule: str | None = Field(None, max_length=255, description="Recurrence rule (RFC 5545)")
    calendar_id: int | None = Field(None, description="Associated calendar ID")

    @field_validator("date_end")
    @classmethod
    def validate_date_end(cls, v: datetime | None, info) -> datetime | None:
        """Validate that date_end is not before date_start."""
        if (
            v is not None
            and hasattr(info, "data")
            and "date_start" in info.data
            and info.data["date_start"] is not None
        ):
            if v < info.data["date_start"]:
                raise ValueError("date_end must be after or equal to date_start")
        return v

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "title": "Updated Meeting",
                "description": "Updated description",
            }
        }


class EventFilter(BaseModel):
    """Schema for filtering events in repository queries.

    All fields are optional - multiple filters can be combined.
    """

    user_id: int | None = Field(None, description="Filter by user ID")
    calendar_id: int | None = Field(None, description="Filter by calendar ID")
    start_date_from: datetime | None = Field(None, description="Filter events starting from this date")
    start_date_to: datetime | None = Field(None, description="Filter events starting until this date")
    need_to_remind: bool | None = Field(None, description="Filter by reminder requirement")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")

    @field_validator("start_date_to")
    @classmethod
    def validate_date_range(cls, v: datetime | None, info) -> datetime | None:
        """Validate that start_date_to is not before start_date_from."""
        if (
            v is not None
            and hasattr(info, "data")
            and "start_date_from" in info.data
            and info.data["start_date_from"] is not None
            and v < info.data["start_date_from"]
        ):
            raise ValueError("start_date_to must be after or equal to start_date_from")
        return v

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "user_id": 123456789,
                "start_date_from": "2024-01-15T00:00:00Z",
                "start_date_to": "2024-01-16T00:00:00Z",
                "need_to_remind": True,
                "limit": 50,
            }
        }

