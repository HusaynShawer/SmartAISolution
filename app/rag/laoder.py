from pathlib import Path
import pypdf
import markdown
import aiofiles

async def extract_text_from_pdf(file_path:str)->str:
    text = ""
    async with aiofiles.open(file_path,"rb") as f:
        reader = pypdf.PdfReader(f)
        for page in reader.pages:
            text+= page.extract_text() or ""
    return text

async def extract_text_from_markdown(file_path:str)->str:
    async with aiofiles.open(file_path,"r",encoding="utf-8") as f:
        md_content = await f.read()
    return markdown.markdown(md_content)

async def extract_text_from_txt(file_path:str)->str:
    async with aiofiles.open(file_path,"r",encoding="utf-8") as f:
        txt = await f.read()
    return txt