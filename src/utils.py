import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging

import pypdf
from dotenv import load_dotenv
from pydantic import SecretStr

from src import constants
from src.exceptions import DocumentError, DocumentNotFoundError, InvalidDocumentError

# Configure logging
logging.basicConfig(
    level=getattr(logging, constants.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# load the environment variables
load_dotenv()


def extract_pdf_text(pdf_path: str) -> str:
    """
    Extracts text from a PDF file.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: Extracted text from the pdf file.

    Raises:
        DocumentNotFoundError: If the PDF file does not exist
        DocumentError: If the PDF is corrupted or cannot be read
    """
    logging.info(f"Extracting text from pdf: {pdf_path}")

    if not os.path.exists(pdf_path):
        msg = f"File not found: {pdf_path}"
        logging.error(msg)
        raise DocumentNotFoundError(msg)

    text = ""
    try:
        with open(pdf_path, "rb") as f:
            try:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
                logging.info("PDF text extraction complete.")
                return text
            except pypdf.errors.PdfStreamError as e:
                msg = f"Invalid or corrupted PDF file: {str(e)}"
                logging.error(msg)
                raise InvalidDocumentError(msg)
            except Exception as e:
                msg = f"Error reading PDF file: {str(e)}"
                logging.error(msg, exc_info=True)
                raise DocumentError(msg)
    except (IOError, OSError) as e:
        msg = f"Error accessing file: {str(e)}"
        logging.error(msg)
        raise DocumentError(msg)


def get_openai_key() -> SecretStr:
    """
    Retrieves the OpenAI API key from environment variable OPENAI_API_KEY.

    Returns:
        SecretStr: The OpenAI API key.

    Raises:
        SystemExit: If the API key is not set.
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logging.error("OPENAI_API_KEY not set in environment.")
            raise ValueError("OPENAI_API_KEY not set in environment")
        logging.info("OpenAI API key loaded from environment.")
        return SecretStr(api_key)
    except Exception as e:
        logging.error(f"Error loading OpenAI API key: {e}", exc_info=True)
        raise


def validate_document(
    doc_path: str,
    allowed_types: list = constants.ALLOWED_TYPES,
    max_size_bytes: int = constants.MAX_SIZE_BYTES,
) -> str:
    """
    Validates the document for existence, type, size, and non-empty content.

    Args:
        doc_path (str): Path to the document.
        allowed_types (list): Allowed file extensions. Defaults to [".pdf", ".txt"].
        max_size_bytes (int): Maximum allowed file size in bytes. Defaults to 10MB.

    Returns:
        str: File extension if valid.

    Raises:
        DocumentNotFoundError: If the file does not exist.
        InvalidDocumentError: If the file type is not supported, is empty, or too large.
    """
    if not os.path.exists(doc_path):
        msg = f"File not found: {doc_path}"
        logging.error(msg)
        raise DocumentNotFoundError(msg)

    ext = os.path.splitext(doc_path)[1].lower()
    if ext not in allowed_types:
        msg = f"Unsupported file type: {ext}. Allowed types: {allowed_types}"
        logging.error(msg)
        raise InvalidDocumentError(msg)

    file_size = os.path.getsize(doc_path)
    if file_size == 0:
        msg = f"File is empty: {doc_path}"
        logging.error(msg)
        raise InvalidDocumentError(msg)

    if file_size > max_size_bytes:
        msg = (
            f"File too large: {file_size} bytes. Max allowed is {max_size_bytes} bytes."
        )
        logging.error(msg)
        raise InvalidDocumentError(msg)

    return ext
