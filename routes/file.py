from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from config import files_store_path

router = APIRouter()


@router.post("/files")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    if not file.filename.endswith((".txt", ".pdf")):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    content = await file.read()
    with open(files_store_path.joinpath(file.filename), "wb") as f:
        f.write(content)

    return {"filename": file.filename}


@router.get("/files/{filename}")
async def download_file(filename: str):
    if not filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_path = files_store_path.joinpath(filename)
    # Ensure the file is within the designated directory
    if (not file_path.resolve().is_relative_to(files_store_path.resolve())) or (
        not file_path.exists()
    ):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        file_path, media_type="application/octet-stream", filename=filename
    )


@router.get("/files/list/")
async def list_files():
    files = [f.name for f in files_store_path.iterdir() if f.is_file()]
    return {"files": files}


@router.delete("/files/{filename}")
async def delete_file(filename: str):
    file_path = files_store_path.joinpath(filename)
    if file_path.resolve().is_relative_to(files_store_path.resolve()) is False:
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    file_path.unlink()
    return {"filename": filename, "message": "File deleted successfully"}
