from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

data_path = Path(__file__).parent / "data"
files_path = data_path / "files"

app = FastAPI()

@app.post("/file/upload/")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    if not file.filename.endswith(('.txt', '.pdf')):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    content = await file.read()
    with open(files_path.joinpath(file.filename), "wb") as f:
        f.write(content)

    return {"filename": file.filename}

@app.get("/file/download/{filename}")
async def download_file(filename: str):
    file_path = files_path.joinpath(filename)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)

@app.get("/file/list/")
async def list_files():
    files = [f.name for f in files_path.iterdir() if f.is_file()]
    return {"files": files}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)