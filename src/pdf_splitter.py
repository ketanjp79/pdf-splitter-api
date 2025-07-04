import os, re
import fitz
from src import config

class PDFSplitter:
    def __init__(self, pdf_path, output_base=None, prefixes=None):
        self.pdf_path = pdf_path
        self.outdir = (output_base or config.OUTPUT_BASE_DIR)
        self.prefixes = prefixes.split(",") if prefixes else []
        self.doc = fitz.open(pdf_path)
        self.name = os.path.splitext(os.path.basename(pdf_path))[0]
        self.dest = os.path.join(self.outdir, self.name)
        os.makedirs(self.dest, exist_ok=True)
    def split_prefix(self, prefix):
        """
        Split the PDF into sections based on the given prefix.
        #i want to generate list from prefixes = ["40-44",49,50]
        result = prefixes[40,41,42,43,44,49,50]
        """
        prefixes = []
        for p in self.prefixes:
            if isinstance(p, str):
                if "-" in p:
                    start, end = p.split("-")
                    start, end = int(start), int(end)
                    prefixes.extend([str(i) for i in range(start, end + 1)])
                
            elif isinstance(p, int):
                prefixes.append(str(p))
            else:
                raise ValueError(f"Invalid prefix type: {type(p)}")
        return prefixes 
    def _find_footer(self, page):
        clip = page.rect
        clip = fitz.Rect(clip.x0, clip.y1 - clip.height*0.2, clip.x1, clip.y1)
        txt = page.get_text(clip=clip)
        for pat in [r"\b\d{2} \d{2,4} \d{2,4}(?:[-.]\w{1,5})?\b",
                    r"\b\d{5}(?:[-.]\w{1,5})?\b",
                    r"\b\d{2}(?:\.\d+){2,3}\b",
                    r"\b\d{2,4}[- ]\d{2,4}[-]\d{2,4}\b"]:
            m = re.search(pat, txt)
            if m: return m.group().strip()
        return None

    def split(self):
        groups = []
        curr_id, curr_norm, pages = None, None, []
        for i,page in enumerate(self.doc):
            full = self._find_footer(page) or f"UNID_{i}"
            norm = re.sub(r"-\d{1,4}$","",full)
            if norm!=curr_norm:
                if pages: groups.append((curr_id, pages))
                pages=[i]; curr_norm=norm; curr_id=full
            else:
                pages.append(i)
        if pages: groups.append((curr_id,pages))

        out_paths=[]
        
        for sec,pgs in groups:
            if self.prefixes:
                if not any(p for p in self.prefixes if sec.startswith(p)):
                    continue
                
            new = fitz.open()
            for p in pgs: new.insert_pdf(self.doc, from_page=p, to_page=p)
            safe = re.sub(r'[\\/:"*?<>|]','_',sec)
            fn = f"{safe}.pdf"; dest=os.path.join(self.dest,fn)
            # avoid overwrite
            c=1
            while os.path.exists(dest):
                dest=os.path.join(self.dest,f"{safe}_{c}.pdf"); c+=1
            new.save(dest); new.close()
            out_paths.append(dest)
        return out_paths
def main():
    splitter = PDFSplitter("path/to/pdf", "output/directory", "40-44,49,50")
    splitter.split()
    
if __name__ == "__main__":
    main()
    