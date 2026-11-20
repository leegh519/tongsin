"""Place user-provided diagram replacements without touching surrounding content."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]

def apply_replacements(im,question_id,rect,zoom):
 path=ROOT/'data/image_replacements.json'
 config=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
 draw=ImageDraw.Draw(im)
 def pixels(box):
  x0,y0,x1,y1=box
  return tuple(round(v) for v in ((x0-rect.x0)*zoom,(y0-rect.y0)*zoom,(x1-rect.x0)*zoom,(y1-rect.y0)*zoom))
 for replacement in config.get(question_id,[]):
  draw.rectangle(pixels(replacement['clear']),fill='white')
  x0,y0,x1,y1=pixels(replacement['place'])
  image=Image.open(ROOT/replacement['image']).convert('RGB')
  image.thumbnail((x1-x0,y1-y0),Image.Resampling.LANCZOS)
  # Resize within this one diagram area, preserving its aspect ratio.
  scale=min((x1-x0)/image.width,(y1-y0)/image.height)
  image=image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.LANCZOS)
  im.paste(image,(x0,y0))
 return im
