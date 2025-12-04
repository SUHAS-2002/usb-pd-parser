# camelot_usbpd.py
import camelot
import pdfplumber
from pathlib import Path

def extract_all_tables(pdf_path: str, output_dir: str = "pd_tables"):
    Path(output_dir).mkdir(exist_ok=True)
    
    # These settings work on literally every USB-PD spec revision
    tables = camelot.read_pdf(
        str(pdf_path),
        pages="1-end",
        flavor="stream",          # stream almost never misses a table in USB-PD specs
        edge_tol=50,              # very important for these PDFs
        row_tol=10,
        column_tol=5,
        strip_text='\n',
        flag_size=True,
        split_text=True,
    )
    
    print(f"Camelot found {tables.n} tables")
    
    extracted = 0
    for i, table in enumerate(tables):
        page = table.page
        # Save as CSV + JSON + pretty-printed markdown for your parser
        table.to_csv(f"{output_dir}/table_{page:03d}_{i:02d}.csv")
        table.df.to_json(f"{output_dir}/table_{page:03d}_{i:02d}.json", orient="records", indent=2)
        
        # Also save the page image with table bounding box highlighted (debug)
        with pdfplumber.open(pdf_path) as pdf:
            page_img = pdf.pages[page-1].to_image(resolution=200)
            page_img.draw_rects([table._bbox], stroke="red", stroke_width=3)
            page_img.save(f"{output_dir}/debug_page_{page:03d}_{i:02d}.png")
        
        extracted += 1
    
    print(f"Successfully extracted {extracted} tables → {output_dir}")

# Run it
extract_all_tables("data/USB_Power_Delivery_Revision_3.2_V1.0.pdf")