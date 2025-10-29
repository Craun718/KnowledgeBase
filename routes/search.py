import json
from fastapi import HTTPException, Query, UploadFile, File, Form, APIRouter, status

from model import DefinitionResponse, DefinitionResult
from service.search import get_definition

router = APIRouter()


@router.post("/definition")
async def search_definition(
    query: str = Form(..., description="搜索关键词"),
) -> DefinitionResponse:
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Type parameter is required"
        )

    data = get_definition(query)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No definition found"
        )

    result: DefinitionResult = DefinitionResult(
        term=data.term,
        definition=data.definition.replace("\n", "").replace(" ", "").replace("\t", ""),
        documents=data.documents,
        page=data.page,
    )

    return DefinitionResponse(result=[result])


@router.post("/definition/batch")
async def search_definition_batch(
    query: str = Form(..., description="搜索关键词（用逗号分隔）"),
):
    results = []
    query.replace("，", ",")
    for q in query.split(","):
        data = get_definition(q.strip())
        if not data:
            continue

        result: DefinitionResult = DefinitionResult(
            term=data.term,
            definition=data.definition.replace("\n", "")
            .replace(" ", "")
            .replace("\t", ""),
            documents=data.documents,
            page=data.page,
        )
        results.append(result)

    return DefinitionResponse(result=results)


@router.post("/search/batch")
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
