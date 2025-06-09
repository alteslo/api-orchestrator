import sys
import traceback
import typing

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from minio.error import S3Error
from pydantic import ValidationError

from app.src.core.constants.constants import FILES_PROJECT_NAME
from app.src.core.exception_handlers.exception_model import AppExceptionDTO
from app.src.core.logging import logger


def custom_handler(request: Request, exc: typing.Type[Exception]):
    match exc:
        case HTTPException():
            logger.error(f'Service {FILES_PROJECT_NAME} has Exception from path: "{request.url.path}", detail: "{exc.detail}"')
            app_exc = AppExceptionDTO(message=exc.detail, status_code=exc.status_code, context={"traceback": str(traceback.extract_tb(sys.exc_info()[-1], 1))})
        case S3Error():
            logger.error(f'Service {FILES_PROJECT_NAME} has Exception from path: "{request.url.path}", detail: "{exc.message}"')
            app_exc = AppExceptionDTO(message=exc.message, context={"traceback": str(traceback.extract_tb(sys.exc_info()[-1], 1))})
        case RequestValidationError():
            for error in exc.errors():
                type_error = error.get("type")
                location = error.get("loc")[0]
                logger.error(f'Service {FILES_PROJECT_NAME} has Exception from path: "{request.url.path}", type: "{type_error}" in "{location}"')
            app_exc = AppExceptionDTO(message=exc.errors()[0].get('msg'), context={'location': exc.errors()[0].get('loc')})
        case ValidationError():
            for error in exc.errors():
                type_error = error.get("type")
                location = error.get("loc")
                logger.critical(f'Service {FILES_PROJECT_NAME} has Exception from path: "{request.url.path}", type: "{type_error}" in "{location}"')
            app_exc = AppExceptionDTO(message=jsonable_encoder(str(exc)), context={'location': exc.errors()[0].get('loc')})
        case Exception():
            for error in exc.args:
                logger.critical(f'Service {FILES_PROJECT_NAME} has Exception from path: "{request.url.path}", detail: "{error}"')
            app_exc = AppExceptionDTO(message=jsonable_encoder(f"{str(exc)}"), context={"traceback": str(traceback.extract_tb(sys.exc_info()[-1], 1))})
    return JSONResponse(status_code=app_exc.status_code, content=app_exc.model_dump())


def register_custom_exc_handlers(app: FastAPI):
    app.add_exception_handler(HTTPException, custom_handler)
    app.add_exception_handler(S3Error, custom_handler)
    app.add_exception_handler(RequestValidationError, custom_handler)
    app.add_exception_handler(ValidationError, custom_handler)
    app.add_exception_handler(Exception, custom_handler)
