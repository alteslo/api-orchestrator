from fastapi import status
from pydantic import BaseModel


class AppExceptionDTO(BaseModel):
    status_code: int = status.HTTP_400_BAD_REQUEST
    message: str | None = None
    context: dict | None = None


# TODO Привести к виду
""""
{
  "exception_case": "Наименование исключения",
  "message": "Уточняющее сообщение",
  "status_code": "цифровой код исключения",
  "context": "Развёрнутая детализация ошибки или traceback",
  "type": "system | buiseness (тип исключения, БД или системное)"
}
"""
