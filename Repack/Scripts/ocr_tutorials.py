"""Offline OCR for analysis only; composite transparent glyphs in memory."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

ROOT=Path(__file__).resolve().parents[2]

def main():
    inventory=json.loads((ROOT/'Repack/reports/tutorial_image_inventory.json').read_text('utf-8'))
    engine=RapidOCR(intra_op_num_threads=2,inter_op_num_threads=2)
    results=[]
    for entry in inventory['textures']:
        if not entry['name'].endswith('-EN'): continue
        rgba=np.array(Image.open(ROOT/entry['export']).convert('RGBA'))
        rgb=(rgba[:,:,:3].astype(float)*rgba[:,:,3:4]/255).astype('uint8')
        found,_=engine(rgb[:,:,::-1],use_cls=False)
        lines=[{'text':text,'y':float(min(p[1] for p in box)),'confidence':float(score)} for box,text,score in (found or [])]
        results.append({'name':entry['name'],'image':entry['export'],'lines':lines})
        print('OCR',entry['name'],len(lines),'lines',flush=True)
    (ROOT/'Repack/reports/tutorial_ocr.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__': main()
