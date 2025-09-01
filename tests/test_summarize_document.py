from pathlib import Path
from typing import Generator

import pytest

from src import summarize_document
from src.exceptions import DocumentError, InvalidDocumentError, SummarizationError


@pytest.fixture
def mock_chain(monkeypatch) -> None:
    """Set up mock chain that returns a fixed summary."""

    class MockChain:
        def invoke(self, input_dict):
            if not isinstance(input_dict.get("input_documents", []), list):
                raise ValueError("Invalid input format")
            return {"output_text": "summary"}

    class MockLLM:
        pass

    monkeypatch.setattr(summarize_document, "ChatOpenAI", lambda *a, **kw: MockLLM())
    monkeypatch.setattr(
        summarize_document,
        "load_summarize_chain",
        lambda llm, chain_type: MockChain(),
    )


@pytest.fixture
def sample_pdf(tmp_path) -> Generator[Path, None, None]:
    """Create a sample PDF file for testing."""
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%mock\n")
    yield pdf_path


@pytest.fixture
def sample_txt(tmp_path) -> Generator[Path, None, None]:
    """Create a sample text file for testing."""
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("hello world")
    yield txt_path


class TestSummarizeText:
    """Tests for the summarize_text function."""

    def test_successful_summarization(self, mock_chain):
        """Test successful text summarization."""
        result = summarize_document.summarize_text("Some long text.")
        assert result == "summary"

    def test_empty_text(self, mock_chain):
        """Test summarization with empty text."""
        with pytest.raises(InvalidDocumentError) as exc_info:
            summarize_document.summarize_text("")
        assert "Empty text cannot be summarized" in str(exc_info.value)

    def test_invalid_input_format(self, mock_chain, monkeypatch):
        """Test summarization with invalid input format."""

        class MockChain:
            def invoke(self, input_dict):
                raise ValueError("Invalid input format")

        monkeypatch.setattr(
            summarize_document,
            "load_summarize_chain",
            lambda *args, **kwargs: MockChain(),
        )
        with pytest.raises(SummarizationError) as exc_info:
            summarize_document.summarize_text("text")
        assert "Error during text summarization" in str(exc_info.value)


class TestMainFunction:
    """Tests for the main function."""

    @pytest.fixture
    def mock_argv(self, monkeypatch) -> None:
        """Mock sys.argv for testing."""

        def _mock_argv(path: str) -> None:
            monkeypatch.setattr(
                summarize_document,
                "sys",
                type("MockSys", (), {"argv": ["script", path]})(),
            )

        return _mock_argv

    def test_pdf_summarization(self, mock_chain, sample_pdf, mock_argv, monkeypatch):
        """Test main function with PDF file."""
        mock_argv(str(sample_pdf))
        monkeypatch.setattr(
            summarize_document.utils,
            "validate_document",
            lambda path: ".pdf",
        )
        monkeypatch.setattr(
            summarize_document.utils,
            "extract_pdf_text",
            lambda path: "pdf text",
        )

        result = summarize_document.main()
        assert result == "summary"

    def test_txt_summarization(self, mock_chain, sample_txt, mock_argv, monkeypatch):
        """Test main function with text file."""
        mock_argv(str(sample_txt))
        monkeypatch.setattr(
            summarize_document.utils,
            "validate_document",
            lambda path: ".txt",
        )

        result = summarize_document.main()
        assert result == "summary"

    def test_no_arguments(self, monkeypatch):
        """Test main function with no arguments."""
        monkeypatch.setattr(
            summarize_document,
            "sys",
            type("MockSys", (), {"argv": ["script"]})(),
        )
        with pytest.raises(InvalidDocumentError) as exc_info:
            summarize_document.main()
        assert "Usage:" in str(exc_info.value)

    def test_nonexistent_file(self, mock_argv):
        """Test main function with non-existent file."""
        mock_argv("nonexistent.txt")
        with pytest.raises(DocumentError) as exc_info:
            summarize_document.main()
        assert "File not found" in str(exc_info.value)

    def test_empty_file(self, tmp_path, mock_argv):
        """Test main function with empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.touch()
        mock_argv(str(empty_file))
        with pytest.raises(InvalidDocumentError) as exc_info:
            summarize_document.main()
        assert "File is empty" in str(exc_info.value)
