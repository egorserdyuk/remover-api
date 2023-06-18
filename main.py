from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse


from sqlmodel import SQLModel, create_engine, Column, Integer, String, Field, ForeignKey, Session
from typing import Optional

from rembg import remove
from datetime import datetime
import logging
import os


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SourceFile(SQLModel, table=True):
    """
    Represents a source file in the database.

    Attributes:
        id (int, optional): The ID of the edited source file.
        name (str): The name of the original source filed.
        date (datetime): The time of transfer to the database.
        content (bytes): The content of the edited source file.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String))
    date: datetime = Field(default_factory=datetime.utcnow)
    content: bytes


class EditedSourceFile(SQLModel, table=True):
    """
    Represents a source file that has been edited.

    Attributes:
        id (int, optional): The ID of the edited source file.
        source_file_id (int): The ID of the original source file that was edited.
        content (bytes): The content of the edited source file.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    source_file_id: int = Field(sa_column=Column(
        Integer, ForeignKey("sourcefile.id")))
    content: bytes


# Logger for debugging

logs_dir = "./logs"
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(
    logs_dir, f"logs_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.log")

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s"
)


engine = create_engine("sqlite:///database.db")


def start_session():
    """
    Initializes a new database session by creating all necessary tables in the database.
    This function does not take any parameters and does not return anything.
    """
    SQLModel.metadata.create_all(engine)


@app.post("/remove_background")
async def remove_background(file: UploadFile = File(...)) -> FileResponse:
    """
    An endpoint that removes the background from an image file uploaded in the request.

    Args:
        file (UploadFile): The image file to be processed.

    Returns:
        FileResponse: A response containing the processed image file without the background.

    Raises:
        JSONResponse: If the uploaded file is not a valid image file in the png or jpeg format.
    """
    valid_content_types = {"image/png", "image/jpeg"}
    if file.content_type not in valid_content_types:
        return JSONResponse({"error": "Invalid file type"}, status_code=400)

    content = await file.read()

    source_file = SourceFile(name=f"{file.filename}", content=content)

    with Session(engine) as session:
        session.add(source_file)
        session.commit()
        session.refresh(source_file)

    output_file = f"output_{file.filename}"
    with open(output_file, "wb") as f:
        removed_background_file = remove(content)
        f.write(removed_background_file)

    edited_file = EditedSourceFile(
        source_file_id=source_file.id, content=removed_background_file)

    with Session(engine) as session:
        session.add(edited_file)
        session.commit()
        session.refresh(edited_file)

    return FileResponse(output_file, media_type=file.content_type)


if __name__ == '__main__':
    import uvicorn
    start_session()
    uvicorn.run(app, host="0.0.0.0", port=4000)
