"""Shared constants."""

DATE_PARSE_FORMAT = "%d.%m.%Y"
# local part: dots only between characters; domain labels can't start or end with a hyphen
EMAIL_REGEX = (
    r"^[A-Za-z0-9_%+-]+(\.[A-Za-z0-9_%+-]+)*"
    r"@([A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}$"
)
