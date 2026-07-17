from pathlib import Path
import pypdf
import markdown

def extrat_text_from_pdf(file_path:str)->str:
    text = ""
    with open(file_path,"rb") as f:
        reader = pypdf.PdfReader(f)
        for page in reader.pages:
            text+= page.extract_text() or ""
    return text

def extract_text_from_markdown(file_path:str)->str:
    with open(file_path,"r",encoding="utf-8") as f:
        md_content = f.read()
    return markdown.markdown(md_content)

def extract_from_txt(file_path:str)->str:
    with open(file_path,"r") as f:
        txt = f.read()
    return f