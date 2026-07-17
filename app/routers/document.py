from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db
from core.dependencies import get_current_user
from models.user import User
from services.document_service import DocumentService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Upload request received from user: %s file=%s", current_user.id, file.filename)
    service = DocumentService(db)
    result = await service.upload_and_process(file, current_user.id)
    logger.info("Upload processing finished for user: %s file=%s", current_user.id, file.filename)
    return result