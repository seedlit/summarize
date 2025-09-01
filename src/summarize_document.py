import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging

from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI

from src import constants, utils
from src.exceptions import DocumentError, InvalidDocumentError, SummarizationError

# Configure logging
logging.basicConfig(
    level=getattr(logging, constants.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def summarize_text(text: str) -> str:
    """
    Summarizes the provided text using OpenAI via LangChain.

    Args:
        text (str): The text to summarize.

    Returns:
        str: The summary of the text.

    Raises:
        InvalidDocumentError: If the text is empty or invalid.
        SummarizationError: If summarization fails for any reason.
    """
    logging.info("Starting text summarization using OpenAI.")

    # Validate input text
    if not text or not text.strip():
        msg = "Empty text cannot be summarized"
        logging.error(msg)
        raise InvalidDocumentError(msg)

    try:
        llm = ChatOpenAI(api_key=utils.get_openai_key())
        chain = load_summarize_chain(llm, chain_type="stuff")
        docs = [Document(page_content=text)]
        try:
            result = chain.invoke({"input_documents": docs})
        except (ValueError, AttributeError) as e:
            msg = f"Error during text summarization: {str(e)}"
            logging.error(msg)
            raise SummarizationError(msg) from e

        summary = result.get("output_text")
        if not summary:
            msg = "No summary returned from model"
            logging.error(msg)
            raise SummarizationError(msg)

        logging.info("Text summarization complete.")
        return summary
    except DocumentError:
        # Re-raise document-related errors (like missing API key) as is
        raise
    except Exception as e:
        msg = f"Unexpected error during summarization: {str(e)}"
        logging.error(msg)
        raise SummarizationError(msg) from e
    except Exception as e:
        msg = f"Error during text summarization: {str(e)}"
        logging.error(msg, exc_info=True)
        raise SummarizationError(msg)


def main() -> str:
    """
    Main function to read a document, extract its text, and print its summary.

    Returns:
        str: The summary of the document.

    Raises:
        DocumentNotFoundError: If the document path is not provided or file not found.
        InvalidDocumentError: If the document is empty or invalid.
        SummarizationError: If summarization fails.
    """
    if len(sys.argv) < 2:
        msg = "Usage: python summarize_document.py <document_path>"
        logging.error(msg)
        raise InvalidDocumentError(msg)

    doc_path = sys.argv[1]
    ext = utils.validate_document(doc_path)

    try:
        # Read document
        if ext == ".pdf":
            text = utils.extract_pdf_text(doc_path)
        else:
            logging.info(f"Extracting text from file: {doc_path}")
            try:
                with open(doc_path, "r", encoding="utf-8") as f:
                    text = f.read()
                if not text.strip():
                    msg = f"File is empty or unreadable: {doc_path}"
                    logging.error(msg)
                    raise InvalidDocumentError(msg)
            except UnicodeDecodeError as e:
                msg = f"File is not a valid text file: {str(e)}"
                logging.error(msg)
                raise InvalidDocumentError(msg)
            except Exception as e:
                msg = f"Error reading file: {str(e)}"
                logging.error(msg, exc_info=True)
                raise DocumentError(msg)

        # Summarize
        summary = summarize_text(text)
        logging.info("Summary generated successfully.")
        return summary

    except DocumentError:
        # Re-raise document-related errors as is
        raise
    except Exception as e:
        msg = f"Unhandled error in main: {str(e)}"
        logging.error(msg, exc_info=True)
        raise DocumentError(msg)


if __name__ == "__main__":
    try:
        summary = main()
        print(summary)
    except DocumentError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
