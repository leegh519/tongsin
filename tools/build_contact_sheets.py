from pathlib import Path
import json,collections
from PIL import Image,ImageOps,ImageDraw,ImageFont
r=Path(__file__).resolve().parents[1];qs=json.loads((r/'data/questions.json').read_text(encoding='utf-8'));out=r/'review/contact-sheets';out.mkdir(exist_ok=True)
for exam in sorted(set(q['examId'] for q in qs)):
 sheet=Image.new('RGB',(1200,1600),'#dddddd');draw=ImageDraw.Draw(sheet)
 for i,q in enumerate(x for x in qs if x['examId']==exam):
  im=Image.open(r/q['image']['src']);im.thumbnail((290,285));x=(i%4)*300;y=(i//4)*320;sheet.paste(im,(x+(300-im.width)//2,y+25));draw.text((x+8,y+5),q['id'],fill='black')
 sheet.save(out/f'{exam}.jpg',quality=88)
errors=[]
for q in qs:
 im=Image.open(r/q['image']['src']);assert im.size==(q['image']['width'],q['image']['height']);assert q['answer']['choice'] and 1<=q['answer']['choice']<=q['choiceCount']
 if len(set('①②③④⑤')&set(q['ocrText']))<q['choiceCount']:errors.append(q['id'])
print('Choice glyph extraction warnings',errors)
