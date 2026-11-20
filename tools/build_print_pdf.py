"""A4 2x2 print sample, column-major order (1 3 / 2 4)."""
from pathlib import Path
import json,re,io,argparse
import pymupdf as fitz
from PIL import Image,ImageDraw,ImageChops
ROOT=Path(__file__).resolve().parents[1]

def make_question_image(q,full=False):
 doc=fitz.open(ROOT/q['source']['pdf']);p=doc[q['source']['page']-1];rect=fitz.Rect(q['source']['crop']);zoom=2.5
 # The sample's questions end in text choices; exclude clipped page rules/next-question fragments.
 body=[];body_top=[]
 for block in p.get_text('dict')['blocks']:
  for line in block.get('lines',[]):
   b=fitz.Rect(line['bbox']);t=''.join(s['text'] for s in line['spans'])
   if rect.intersects(b) and b.x0>=rect.x0 and b.x1<=rect.x1+2 and not re.fullmatch(r'\s*[ⒶⒷ]?\s*[-−]\s*\d+\s*[-−]?\s*',t):body.append(b.y1);body_top.append(b.y0)
 if body and not full:rect.y1=min(rect.y1,max(body)+1)
 pix=p.get_pixmap(matrix=fitz.Matrix(zoom,zoom),clip=rect,alpha=False)
 im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);draw=ImageDraw.Draw(im)
 cleanup=json.loads((ROOT/'data/image_cleanup.json').read_text(encoding='utf-8')) if (ROOT/'data/image_cleanup.json').exists() else {}
 for x0,y0,x1,y1 in cleanup.get(q['id'],[]):draw.rectangle(((x0-rect.x0)*zoom,(y0-rect.y0)*zoom,(x1-rect.x0)*zoom,(y1-rect.y0)*zoom),fill='white')
 if full and body_top:
  # Header rules can extend into the 14-point margin above the actual stem.
  bottom=(min(body_top)-rect.y0-2)*zoom
  if bottom>0:draw.rectangle((0,0,im.width,bottom),fill='white')
 for block in p.get_text('dict')['blocks']:
  for line in block.get('lines',[]):
   footer=''.join(s['text'] for s in line['spans'])
   if line['bbox'][1]>p.rect.height-85 and re.fullmatch(r'\s*[ⒶⒷ]?\s*[-−]\s*\d+\s*[-−]?\s*',footer):
    b=fitz.Rect(line['bbox']);draw.rectangle(((b.x0-rect.x0-2)*zoom,(b.y0-rect.y0-2)*zoom,(b.x1-rect.x0+2)*zoom,(b.y1-rect.y0+2)*zoom),fill='white')
 # Remove long page-divider strokes, including short ticks at their ends.
 for drawing in p.get_drawings():
  if drawing['rect'].height>p.rect.height*.7:
   for segment in drawing['items']:
    if segment[0]=='l':
     a,b=segment[1:3];draw.line(((a.x-rect.x0)*zoom,(a.y-rect.y0)*zoom,(b.x-rect.x0)*zoom,(b.y-rect.y0)*zoom),fill='white',width=5)
 gray=im.convert('L')
 for col in list(range(min(25,im.width)))+list(range(max(0,im.width-25),im.width)):
  if sum(gray.getpixel((col,y))<180 for y in range(im.height))>im.height*.8:draw.rectangle((max(0,col-2),0,min(im.width,col+2),im.height),fill='white')
 for y in list(range(min(12,im.height)))+list(range(max(0,im.height-12),im.height)):
  if sum(gray.getpixel((x,y))<180 for x in range(im.width))>im.width*.85:draw.rectangle((0,max(0,y-2),im.width,min(im.height,y+2)),fill='white')
 # Fix the print bounds before masking, keeping the original first-line indentation.
 box=ImageChops.difference(im,Image.new('RGB',im.size,'white')).point(lambda v:255 if v>55 else 0).getbbox()
 if full:
  # Ignore isolated specks at a distant page edge that would preserve a huge blank region.
  ink=im.convert('L').point(lambda v:255 if v<200 else 0)
  rows=[i for i in range(im.height) if ink.crop((0,i,im.width,i+1)).histogram()[255]>=3]
  cols=[i for i in range(im.width) if ink.crop((i,0,i+1,im.height)).histogram()[255]>=3]
  if rows and cols:box=(min(cols),min(rows),max(cols)+1,max(rows)+1)
 if not box:raise ValueError(q['id']+' empty image')
 crop=(max(0,box[0]-10),max(0,box[1]-10),min(im.width,box[2]+10),min(im.height,box[3]+10))
 masks=[]
 for block in p.get_text('rawdict')['blocks']:
  for line in block.get('lines',[]):
   chars=[c for s in line['spans'] for c in s['chars']];text=''.join(c['c'] for c in chars)
   match=re.match(r'^\s*(?:문\s*)?'+str(q['number'])+r'\s*\.\s*',text)
   at_start=rect.x0<=line['bbox'][0]<=rect.x0+45 and abs(line['bbox'][1]-(rect.y0+14))<5
   if at_start and (match or text.strip()=='문'):
    selected=chars[:match.end()] if match else chars;b=fitz.Rect(selected[0]['bbox'])
    for ch in selected[1:]:b|=fitz.Rect(ch['bbox'])
    b.x0-=.6;b.x1+=.3;b.y0-=.5;b.y1+=.5
    mask=((b.x0-rect.x0)*zoom,(b.y0-rect.y0)*zoom,(b.x1-rect.x0)*zoom,(b.y1-rect.y0)*zoom);draw.rectangle(mask,fill='white');masks.append(list(b))
 if not masks:raise ValueError(q['id']+' original question-number mask not found')
 im=im.crop(crop);out=io.BytesIO();im.save(out,format='PNG');doc.close()
 return out.getvalue(),im.size,masks

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 tax=json.loads((ROOT/'data/taxonomy.json').read_text(encoding='utf-8'));qs=json.loads((ROOT/'data/questions.json').read_text(encoding='utf-8'))
 ci={c['id']:i for i,c in enumerate(tax['categories'])};book=json.loads((ROOT/'data/book_taxonomy.json').read_text(encoding='utf-8'));ti={t['id']:i for c in book['categories'] for i,t in enumerate(c['topics'])}
 qs.sort(key=lambda q:(ci[q['classification']['category']],ti[q['classification'].get('bookPrimaryTopic',q['classification']['primaryTopic'])],q['year'],['지방직','서울시','국가직'].index(q['agency']),q['number']))
 sample=qs[:12];assert len({q['id'] for q in sample})==12
 font_path=Path('C:/Windows/Fonts/batang.ttc');font=fitz.Font(fontfile=str(font_path));font_bytes=font.buffer
 doc=fitz.open();width,height,margin,gap=595.276,841.89,36,24;cellw=(width-2*margin-gap)/2;cellh=350
 def text(page,x,y,value,size=8,right=False):
  if right:x-=font.text_length(value,fontsize=size)
  page.insert_text((x,y),value,fontname='kr',fontsize=size,color=(.12,.12,.12))
 def newpage():
  p=doc.new_page(width=width,height=height);p.insert_font(fontname='kr',fontbuffer=font_bytes);return p
 cover=newpage();cat=sample[0]['classification']['category'];title=next(c['label'] for c in tax['categories'] if c['id']==cat)+' 문제';count=sum(q['classification']['category']==cat for q in qs)
 for y,value,size in [(320,'통신이론 기출문제',12),(390,title,32),(440,f'{count}문제',12)]:text(cover,(width-font.text_length(value,fontsize=size))/2,y,value,size)
 cover.draw_line((width/2-95,410),(width/2+95,410),color=(.2,.2,.2),width=.6);text(cover,width-margin,height-25,'1 / 4',8,True)
 manifest=[]
 for start in range(0,12,4):
  p=newpage();pn=len(doc);text(p,margin,35,'통신이론 기출문제',10);text(p,width-margin,35,f'{len(qs)}문제',9,True);p.draw_line((margin,46),(width-margin,46),color=(.2,.2,.2),width=.6)
  group=sample[start:start+4]
  for offset,q in enumerate(group):
   # Column-major placement: offsets 0,1 occupy the left; 2,3 the right.
   col,row=offset//2,offset%2;x=margin+col*(cellw+gap);y=72+row*cellh;seq=start+offset+1
   text(p,x,y+10,f'{seq:03}',8);source=f'{q["year"]} {q["agency"]} {q["number"]}번';text(p,x+cellw,y+21,source,6,True)
   image,(iw,ih),masks=make_question_image(q);scale=min(cellw/iw,280/ih);dest=fitz.Rect(x,y+32,x+iw*scale,y+32+ih*scale);assert dest.y1<height-65;p.insert_image(dest,stream=image)
   manifest.append({'sequence':seq,'id':q['id'],'page':pn,'column':col,'row':row,'rect':list(dest),'originalNumberMasks':masks,'answer':q['answer']['choice'],'answerStatus':q['answer']['status']})
  label='정답(잠정 포함)' if any(q['answer']['status']!='official' for q in group) else '정답'
  answers=label+'   '+'   ·   '.join(f'{start+i+1:03}번 '+'/'.join(['','①','②','③','④','⑤'][v] for v in q['answer'].get('choices',[q['answer']['choice']])) for i,q in enumerate(group));text(p,width-margin,height-47,answers,6,True);text(p,width-margin,height-25,f'{pn} / 4',8,True)
 doc.set_metadata({'title':'통신이론 기출문제 테스트 4쪽','subject':'A4 · 1 3 / 2 4 · 단원 표지 1쪽과 문제 3쪽','author':'통신이론 문제은행'})
 doc.set_toc([[1,title,1]]);doc.subset_fonts();args.output.parent.mkdir(parents=True,exist_ok=True);doc.save(args.output,garbage=4,deflate=True);doc.close()
 check=fitz.open(args.output);assert len(check)==4
 assert [len(p.get_image_info()) for p in check]==[0,4,4,4]
 for pn in range(2,5):
  items=[m for m in manifest if m['page']==pn];assert [(m['column'],m['row']) for m in items]==[(0,0),(0,1),(1,0),(1,1)]
  labels=check[pn-1].get_text('words');nums=[w for w in labels if re.fullmatch(r'\d{3}',w[4])];visual=[w[4] for w in sorted(nums,key=lambda w:(round(w[1]/100),w[0]))];expect=[f'{(pn-2)*4+i:03}' for i in [1,3,2,4]];assert visual==expect,(visual,expect)
 work=ROOT/'work/print-sample';work.mkdir(parents=True,exist_ok=True)
 (work/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 for i,p in enumerate(check):p.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(work/f'page-{i+1}.png')
 print('PASS: 4 A4 pages, cover + 12 questions, correct column-major order, original numbers masked; '+str(args.output))
if __name__=='__main__':main()

