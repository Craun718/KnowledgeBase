import json
from fastapi import HTTPException, UploadFile, File, Form, APIRouter, status

router = APIRouter()


@router.post("/search")
async def search(
    # 文件参数
    file: UploadFile = File(...),
    # 表单参数（与文件同属multipart/form-data）
    search_type: str = Form(...),  # 必选表单参数
):
    if not search_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Type parameter is required"
        )
    if not search_type in ["relationship", "definition"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid type parameter"
        )

    file_content = await file.read()
    try:
        obj = json.loads(file_content)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON file"
        )

    return obj
