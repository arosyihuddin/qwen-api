from pydantic import BaseModel


class FileResult(BaseModel):
    file_url: str
    file_id: str
    image_mimetype: str
