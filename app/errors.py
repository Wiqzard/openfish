from __future__ import annotations


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: str | None = None,
        raw_response: str | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.raw_response = raw_response
        self.status_code = status_code

    def to_dict(self) -> dict[str, str]:
        payload: dict[str, str] = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            payload["details"] = self.details
        if self.raw_response:
            payload["rawResponse"] = self.raw_response
        return payload
