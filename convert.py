from docx2pdf import convert
import os

docx_path = os.path.join(os.path.dirname(__file__), "Tehman CV.docx")
pdf_path = os.path.join(os.path.dirname(__file__), "Tehman CV.pdf")

print("Converting CV to PDF...")
convert(docx_path, pdf_path)
print(f"Done! PDF saved to: {pdf_path}")
