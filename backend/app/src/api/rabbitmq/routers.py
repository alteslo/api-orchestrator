from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.configs.settings import get_settings
from app.src.api.auth.service import check_auth
from app.src.api.base.models import ResponseBase
from backend.app.src.api.objects.schemas import (
    DownloadZipObjectsByListDTO,
    ObjectDTO,
    ObjectFileDTO,
    ObjectItemInfo,
    ObjectMultiUploadFileDTO,
    ObjectUploadFileDTO
)
from app.src.api.objects.services import ObjectService
from app.src.core.constants.regex import REGX_BUCKET

router = APIRouter()
config = get_settings()


@router.get(path="/list_objects", tags=["objects"])
async def list_objects(object_params: ObjectDTO = Depends(), start_after: str | None = None, auth=Depends(check_auth)):
    """Возвращает список объектов относящихся к переданной сущности"""
    return await ObjectService().list_objects(object_params=object_params)
