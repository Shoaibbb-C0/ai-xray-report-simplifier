"""Bounded in-memory JPEG/PNG analysis. Never trust filenames as paths."""
from io import BytesIO
import warnings
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image, ImageFile, ImageOps, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool
from backend.app.services.ml_service import ml_service, ModelBusyError, ModelNotLoadedError

router = APIRouter()
MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 16_000_000
ImageFile.LOAD_TRUNCATED_IMAGES = False


def decode_image(data):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                if source.format not in {"PNG", "JPEG"}:
                    raise HTTPException(415, detail={"code": "unsupported_type", "message": "Choose a PNG or JPEG image."})
                width, height = source.size
                if min(width, height) < 64 or max(width, height) > 8192 or width * height > MAX_PIXELS:
                    raise HTTPException(422, detail={"code": "invalid_dimensions", "message": "Use an image at least 64 pixels wide and tall, up to 16 megapixels."})
                if getattr(source, "n_frames", 1) != 1:
                    raise HTTPException(415, detail={"code": "animated_image", "message": "Use a single still image."})
                source.verify()
            with Image.open(BytesIO(data)) as source:
                source.load()
                return ImageOps.exif_transpose(source).convert("RGB")
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(422, detail={"code": "invalid_image", "message": "This image is damaged or cannot be read. Choose another PNG or JPEG."}) from None


@router.post("/analyze")
async def analyze(file: UploadFile = File(...), language: str = Form("en"), attention: bool = Form(False)):
    image = None
    try:
        if language not in {"en", "hi", "mr"}:
            raise HTTPException(422, detail={"code": "unsupported_language", "message": "Choose English, Hindi or Marathi."})
        if file.content_type not in {"image/png", "image/jpeg"}:
            raise HTTPException(415, detail={"code": "unsupported_type", "message": "Choose a PNG or JPEG image."})
        data = bytearray()
        while chunk := await file.read(64 * 1024):
            data.extend(chunk)
            if len(data) > MAX_BYTES:
                raise HTTPException(413, detail={"code": "file_too_large", "message": "Choose an image smaller than 10 MiB."})
        image = await run_in_threadpool(decode_image, data)
        try:
            return await run_in_threadpool(ml_service.run_inference, image, language, attention)
        except ModelNotLoadedError as error:
            raise HTTPException(503, detail={"code": "model_unavailable", "message": str(error)}) from None
        except ModelBusyError as error:
            raise HTTPException(429, detail={"code": "model_busy", "message": str(error)}) from None
    finally:
        if image is not None:
            image.close()
        await file.close()
