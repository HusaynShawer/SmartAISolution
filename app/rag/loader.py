import aiofiles
import markdown
import pypdf


async def extract_text_from_pdf(file_path: str) -> str:
    """Extract raw text from a PDF file."""
    async with aiofiles.open(file_path, "rb") as file:
        reader = pypdf.PdfReader(file)
        text = "".join(page.extract_text() or "" for page in reader.pages)
    return text


async def extract_text_from_markdown(file_path: str) -> str:
    """Extract plain text from a Markdown file (returns HTML)."""
    async with aiofiles.open(file_path, encoding="utf-8") as file:
        md_content = await file.read()
    return markdown.markdown(md_content)


async def extract_text_from_txt(file_path: str) -> str:
    """Read the raw contents of a plain-text file."""
    async with aiofiles.open(file_path, encoding="utf-8") as file:
        text = await file.read()
    return text
