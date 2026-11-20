"""Complete A4 question book; read down each column (1 3 / 2 4)."""
from pathlib import Path
import argparse,collections,copy,hashlib,json,math,re
import pymupdf as fitz
from build_print_pdf import ROOT,make_question_image

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'print/tongsin_594.pdf');args=parser.parse_args()
 qs=json.loads((ROOT/'data/questions.json').read_text(encoding='utf-8'))
 tax=json.loads((ROOT/'data/taxonomy.json').read_text(encoding='utf-8'))
 book=json.loads((ROOT/'data/book_taxonomy.json').read_text(encoding='utf-8'))
 ci={c['id']:i for i,c in enumerate(tax['categories'])};ti={t['id']:i for c in book['categories'] for i,t in enumerate(c['topics'])}
 qs.sort(key=lambda q:(ci[q['classification']['category']],ti.get(q['classification'].get('bookPrimaryTopic',q['classification']['primaryTopic']),999),q['year'],['지방직','서울시','국가직'].index(q['agency']),q['number']))
 assert len(qs)==594 and len({q['id'] for q in qs})==594
 groups=[(c,[q for q in qs if q['classification']['category']==c['id']]) for c in tax['categories']]
 groups=[(c,v) for c,v in groups if v]
 total=sum(1+math.ceil(len(v)/4) for _,v in groups)
 work=ROOT/'work/print-full';cache=work/'question-images';cache.mkdir(parents=True,exist_ok=True)
 # The source crops may include the first few pixels of the next question.
 # Keep all diagrams; only stop at the next question's known top margin.
 prepared={};errors=[]
 for i,q in enumerate(qs,1):
  item=copy.deepcopy(q);r=item['source']['crop']
  following=[v['source']['crop'][1] for v in qs if v['id']!=q['id'] and v['source']['pdf']==q['source']['pdf'] and v['source']['page']==q['source']['page'] and v['source']['column']==q['source']['column'] and v['source']['crop'][1]>r[1]+1]
  if following:r[3]=min(r[3],min(following))
  try:
   path=cache/(q['id']+'.png');meta=path.with_suffix('.json')
   signature=hashlib.sha256((repr(item['source'])+str((ROOT/item['source']['pdf']).stat().st_mtime_ns)+(ROOT/'tools/build_print_pdf.py').read_text(encoding='utf-8')).encode()).hexdigest()
   old=json.loads(meta.read_text(encoding='utf-8')) if meta.exists() and path.exists() else {}
   if old.get('signature')==signature:size,masks=old['size'],old['masks']
   else:
    image,size,masks=make_question_image(item,full=True);path.write_bytes(image)
    meta.write_text(json.dumps({'signature':signature,'size':size,'masks':masks}),encoding='utf-8')
   prepared[q['id']]=(path,size,masks)
  except Exception as ex:errors.append((q['id'],str(ex)))
  if i%50==0:print('Prepared',i,'/ 594',flush=True)
 if errors:raise RuntimeError(errors)
 font=fitz.Font(fontfile='C:/Windows/Fonts/batang.ttc');font_bytes=font.buffer
 doc=fitz.open();width,height,margin,gap=595.276,841.89,36,24;cellw=(width-2*margin-gap)/2;cellh=350
 def text(p,x,y,value,size=8,right=False):
  if right:x-=font.text_length(value,fontsize=size)
  p.insert_text((x,y),value,fontname='kr',fontsize=size,color=(.12,.12,.12))
 def newpage():
  p=doc.new_page(width=width,height=height);p.insert_font(fontname='kr',fontbuffer=font_bytes);return p
 manifest=[];toc=[];seq=0
 for category,items in groups:
  p=newpage();title=category['label']+' 문제';toc.append([1,title,len(doc)])
  title_size=min(32, (width-2*margin)/font.text_length(title,fontsize=1))
  for y,value,size in [(320,'통신이론 기출문제',12),(390,title,title_size),(440,f'{len(items)}문제',12)]:text(p,(width-font.text_length(value,fontsize=size))/2,y,value,size)
  p.draw_line((width/2-95,410),(width/2+95,410),color=(.2,.2,.2),width=.6);text(p,width-margin,height-25,f'{len(doc)} / {total}',8,True)
  for start in range(0,len(items),4):
   p=newpage();pn=len(doc);text(p,margin,35,'통신이론 기출문제',10);text(p,width-margin,35,'594문제',9,True);p.draw_line((margin,46),(width-margin,46),color=(.2,.2,.2),width=.6)
   page_answers=[]
   for offset,q in enumerate(items[start:start+4]):
    seq+=1;col,row=offset//2,offset%2;x=margin+col*(cellw+gap);y=72+row*cellh
    text(p,x,y+10,f'{seq:03}',8);source=f'{q["year"]} {q["agency"]} {q["number"]}번';text(p,x+cellw,y+21,source,6,True)
    path,(iw,ih),masks=prepared[q['id']];scale=min(cellw/iw,280/ih);dest=fitz.Rect(x,y+32,x+iw*scale,y+32+ih*scale)
    assert dest.x1<=width-margin+.01 and dest.y1<height-65
    p.insert_image(dest,filename=str(path))
    accepted=q['answer'].get('choices',[q['answer']['choice']]);answer='/'.join('①②③④⑤'[v-1] for v in accepted);page_answers.append(f'{seq:03}번 {answer}')
    manifest.append({'sequence':seq,'id':q['id'],'category':category['id'],'page':pn,'column':col,'row':row,'rect':list(dest),'originalNumberMasks':masks,'answers':accepted,'imageSize':[iw,ih],'printedWidth':dest.width,'printedHeight':dest.height})
   answers='정답   '+'   ·   '.join(page_answers);text(p,width-margin,height-47,answers,6,True);text(p,width-margin,height-25,f'{pn} / {total}',8,True)
 assert seq==594 and len(doc)==total
 doc.set_metadata({'title':'통신이론 기출문제 594문항','subject':'9급 지방직·서울시 통신이론 및 국가직 무선공학개론 공통범위 · A4 · 1 3 / 2 4','author':'통신이론 문제은행'})
 doc.set_toc(toc);doc.subset_fonts();args.output.parent.mkdir(parents=True,exist_ok=True);doc.save(args.output,garbage=4,deflate=True);doc.close()
 check=fitz.open(args.output);assert len(check)==total
 for pn in range(1,total+1):
  page=check[pn-1];items=[m for m in manifest if m['page']==pn]
  assert len(page.get_image_info())==len(items)
  assert [(m['column'],m['row']) for m in items]==[(i//2,i%2) for i in range(len(items))]
  nums=[w for w in page.get_text('words') if re.fullmatch(r'\d{3}',w[4]) and w[1]<height-70]
  actual=[w[4] for w in sorted(nums,key=lambda w:(round(w[1]/100),w[0]))]
  expected=[f'{m["sequence"]:03}' for m in sorted(items,key=lambda m:(m['row'],m['column']))]
  assert actual==expected,(pn,actual,expected)
  assert f'{pn} / {total}' in page.get_text()
  if [1,2] in [m['answers'] for m in items]:assert '①/②' in page.get_text()
  page.get_pixmap(matrix=fitz.Matrix(.9,.9),alpha=False).save(work/f'page-{pn:03}.png')
 assert {m['id'] for m in manifest}=={q['id'] for q in qs}
 (work/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 (ROOT/'review/full-print-audit.json').write_text(json.dumps({'questionCount':594,'pageCount':total,'coverCount':len(groups),'ordering':'column-major: 1 3 / 2 4','chapters':[{'label':c['label'],'questionCount':len(v)} for c,v in groups],'multipleAnswerIds':[q['id'] for q in qs if len(q['answer'].get('choices',[]))>1],'manifest':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
 print('PASS:',total,'A4 pages;',len(groups),'covers; 594 unique questions; column-major layout, answer sets, original number masks, and all-page render verified;',args.output)

if __name__=='__main__':main()
