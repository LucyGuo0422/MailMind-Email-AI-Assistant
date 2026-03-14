from typing import TypedDict


class EmailState(TypedDict):
    emails: list[dict]
    history: list[dict]
    current_email: dict      # each dict holds one email's full lifecycle data
    user_name: str

