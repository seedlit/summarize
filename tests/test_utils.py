import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from pydantic import SecretStr
from pypdf import PdfWriter

from src import utils
from src.exceptions import DocumentError, DocumentNotFoundError, InvalidDocumentError


@pytest.fixture
def sample_pdf() -> Generator[Path, None, None]:
    """Create a sample PDF file for testing."""
    temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with open(temp_pdf.name, "wb") as f:
        writer.write(f)

    yield Path(temp_pdf.name)
    # Cleanup
    os.remove(temp_pdf.name)


@pytest.fixture
def mock_pdf_reader(monkeypatch):
    """Mock PdfReader for consistent test results."""

    def mock_reader(f):
        class MockReader:
            pages = [type("MockPage", (), {"extract_text": lambda self: "mock text"})()]

        return MockReader()

    monkeypatch.setattr("pypdf.PdfReader", mock_reader)


class TestPDFExtraction:
    def test_extract_pdf_text_live(self, sample_pdf):
        """Test PDF text extraction with a real PDF file."""
        text = utils.extract_pdf_text(str(sample_pdf))
        assert isinstance(text, str)

    def test_extract_pdf_text_mock(self, mock_pdf_reader, sample_pdf):
        """Test PDF text extraction with a mocked PDF reader."""
        text = utils.extract_pdf_text(str(sample_pdf))
        assert text == "mock text"

    def test_extract_pdf_text_invalid_file(self):
        """Test PDF text extraction with a non-existent file."""
        with pytest.raises(DocumentNotFoundError):
            utils.extract_pdf_text("nonexistent.pdf")

    def test_extract_pdf_text_corrupted(self, tmp_path):
        """Test PDF text extraction with a corrupted PDF file."""
        bad_pdf = tmp_path / "corrupt.pdf"
        bad_pdf.write_bytes(b"not a pdf file")
        with pytest.raises(DocumentError):
            utils.extract_pdf_text(str(bad_pdf))


class TestOpenAIKey:
    def test_get_openai_key_valid(self, monkeypatch):
        """Test retrieving a valid OpenAI API key."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-testkey")
        key = utils.get_openai_key()
        assert isinstance(key, SecretStr)
        assert key.get_secret_value() == "sk-testkey"

    def test_get_openai_key_missing(self, monkeypatch):
        """Test behavior when OpenAI API key is missing."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError) as exc_info:
            utils.get_openai_key()
        assert "OPENAI_API_KEY not set" in str(exc_info.value)


class TestDocumentValidation:
    @pytest.fixture
    def text_file(self, tmp_path) -> Path:
        """Create a sample text file for testing."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("hello world")
        return file_path

    def test_validate_document_valid_txt(self, text_file):
        """Test validation of a valid text file."""
        ext = utils.validate_document(
            str(text_file), allowed_types=[".txt"], max_size_bytes=100
        )
        assert ext == ".txt"

    def test_validate_document_nonexistent(self):
        """Test validation of a non-existent file."""
        with pytest.raises(DocumentNotFoundError) as exc_info:
            utils.validate_document("nonexistent.txt")
        assert "File not found" in str(exc_info.value)

    def test_validate_document_invalid_type(self, tmp_path):
        """Test validation of a file with invalid extension."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("data")
        with pytest.raises(InvalidDocumentError) as exc_info:
            utils.validate_document(str(file_path), allowed_types=[".txt"])
        assert "Unsupported file type" in str(exc_info.value)

    def test_validate_document_empty_file(self, tmp_path):
        """Test validation of an empty file."""
        file_path = tmp_path / "empty.txt"
        file_path.write_text("")
        with pytest.raises(InvalidDocumentError) as exc_info:
            utils.validate_document(str(file_path))
        assert "File is empty" in str(exc_info.value)

    def test_validate_document_large_file(self, tmp_path):
        """Test validation of a file exceeding size limit."""
        file_path = tmp_path / "large.txt"
        file_path.write_text("a" * 200)
        with pytest.raises(InvalidDocumentError) as exc_info:
            utils.validate_document(str(file_path), max_size_bytes=100)
        assert "File too large" in str(exc_info.value)

    def test_validate_document_custom_types(self, tmp_path):
        """Test validation with custom allowed file types."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("test data")
        ext = utils.validate_document(str(file_path), allowed_types=[".csv"])
        assert ext == ".csv"
