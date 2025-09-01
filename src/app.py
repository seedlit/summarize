import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from pypdf import PdfReader

from src import summarize_document
from src.exceptions import DocumentError

app = FastAPI()


def extract_text_from_pdf(pdf_contents: bytes) -> str:
    """Extract text from PDF bytes."""
    pdf_reader = PdfReader(io.BytesIO(pdf_contents))
    return "".join(page.extract_text() or "" for page in pdf_reader.pages)


def extract_text_from_file(contents: bytes, filename: str) -> str:
    """
    Extract text from file contents based on file type.

    Args:
        contents: Raw file contents
        filename: Name of the file (used to determine type)

    Returns:
        str: Extracted text

    Raises:
        HTTPException: If file format is unsupported
    """
    if filename and filename.lower().endswith(".pdf"):
        return extract_text_from_pdf(contents)

    try:
        return contents.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a PDF or text file.",
        )


def generate_summary(text: str) -> dict[str, str]:
    """
    Generate summary from text.

    Args:
        text: Text to summarize

    Returns:
        dict: Contains the generated summary

    Raises:
        HTTPException: If summary generation fails
    """
    try:
        summary = summarize_document.summarize_text(text)
        if not summary:
            raise HTTPException(status_code=500, detail="Failed to generate summary")
        return {"summary": summary}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summarize")
async def summarize(file: UploadFile = File(...)) -> dict[str, str]:
    """
    Summarize the contents of an uploaded file.

    Args:
        file: Uploaded file (PDF or text)

    Returns:
        dict: Contains the generated summary

    Raises:
        HTTPException: For various error conditions
    """
    try:
        contents = await file.read()
        if file.filename is None:
            raise HTTPException(
                status_code=400, detail="Uploaded file must have a filename."
            )
        text = extract_text_from_file(contents, file.filename)
        return generate_summary(text)

    except DocumentError as e:
        # Handle our custom exceptions with their specific status codes
        raise HTTPException(status_code=e.status_code, detail=str(e))

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )
