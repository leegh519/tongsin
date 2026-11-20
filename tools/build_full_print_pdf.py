"""Complete A4 question book; read down each column (1 3 / 2 4)."""
from pathlib import Path
import argparse,collections,copy,hashlib,json,math,re
import pymupdf as fitz
from build_print_pdf import ROOT,make_question_image

def plan_pages(items,prepared):
 pages=[];entries=[];slot=0
 for q in items:
  _,(iw,ih),_=prepared[q['id']]
  tall=ih/iw>1.4 or q['id']=='national-radio-2014-18'
  # Keep 588 and 589 together when the preceding page has just one slot left.
  if q['id']=='local-2009-19' and slot==3:slot=4
  if tall and slot%2:slot+=1
  if slot>=4:
   pages.append(entries);entries=[];slot=0
  entries.append({'question':q,'column':slot//2,'row':slot%2,'fullColumn':tall,'fullWidth':False})
  slot+=2 if tall else 1
 if entries:pages.append(entries)
 return pages

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
   cleanup=json.loads((ROOT/'data/image_cleanup.json').read_text(encoding='utf-8')) if (ROOT/'data/image_cleanup.json').exists() else {}
   signature=hashlib.sha256((repr(item['source'])+repr(cleanup.get(q['id'],[]))+str((ROOT/item['source']['pdf']).stat().st_mtime_ns)+(ROOT/'tools/build_print_pdf.py').read_text(encoding='utf-8')).encode()).hexdigest()
   old=json.loads(meta.read_text(encoding='utf-8')) if meta.exists() and path.exists() else {}
   if old.get('signature')==signature:size,masks=old['size'],old['masks']
   else:
    image,size,masks=make_question_image(item,full=True);path.write_bytes(image)
    meta.write_text(json.dumps({'signature':signature,'size':size,'masks':masks}),encoding='utf-8')
   prepared[q['id']]=(path,size,masks)
  except Exception as ex:errors.append((q['id'],str(ex)))
  if i%50==0:print('Prepared',i,'/ 594',flush=True)
 if errors:raise RuntimeError(errors)
 # The unclassified appendix continues directly after the last main chapter.
 print_groups=[(c,list(items)) for c,items in groups if c['id']!='pending']
 pending=next((items for c,items in groups if c['id']=='pending'),[])
 if pending:print_groups[-1][1].extend(pending)
 plans=[(c,items,plan_pages(items,prepared)) for c,items in print_groups]
 cover_count=sum(c['id']!='pending' for c,_ in groups)
 total=cover_count+sum(len(pages) for _,_,pages in plans)
 font=fitz.Font(fontfile='C:/Windows/Fonts/batang.ttc');font_bytes=font.buffer
 doc=fitz.open();width,height,margin,gap=595.276,841.89,36,24;cellw=(width-2*margin-gap)/2;cellh=350
 def text(p,x,y,value,size=8,right=False):
  if right:x-=font.text_length(value,fontsize=size)
  p.insert_text((x,y),value,fontname='kr',fontsize=size,color=(.12,.12,.12))
 def newpage():
  p=doc.new_page(width=width,height=height);p.insert_font(fontname='kr',fontbuffer=font_bytes);return p
 manifest=[];toc=[];seq=0
 for category,items,pages in plans:
  title=category['label']+' 문제';toc.append([1,title,len(doc)+1])
  if category['id']!='pending':
   p=newpage()
   title_size=min(32, (width-2*margin)/font.text_length(title,fontsize=1))
   category_count=sum(q['classification']['category']==category['id'] for q in items)
   for y,value,size in [(320,'통신이론 기출문제',12),(390,title,title_size),(440,f'{category_count}문제',12)]:text(p,(width-font.text_length(value,fontsize=size))/2,y,value,size)
   p.draw_line((width/2-95,410),(width/2+95,410),color=(.2,.2,.2),width=.6);text(p,width-margin,height-25,f'{len(doc)} / {total}',8,True)
  for entries in pages:
   p=newpage();pn=len(doc);text(p,margin,35,'통신이론 기출문제',10);text(p,width-margin,35,'594문제',9,True);p.draw_line((margin,46),(width-margin,46),color=(.2,.2,.2),width=.6)
   page_answers=[]
   for entry in entries:
    q=entry['question'];seq+=1;col,row=entry['column'],entry['row'];x=margin+col*(cellw+gap);y=72+row*cellh
    area_width=width-2*margin if entry['fullWidth'] else cellw
    text(p,x,y+10,f'{seq:03}',8);source=f'{q["year"]} {q["agency"]} {q["number"]}번';text(p,x+area_width,y+21,source,6,True)
    path,(iw,ih),masks=prepared[q['id']];limit_height=630 if entry['fullColumn'] or entry['fullWidth'] else 280
    scale=min((area_width-12)/iw,limit_height/ih,.72 if entry['fullWidth'] else .36);dest=fitz.Rect(x,y+32,x+iw*scale,y+32+ih*scale)
    assert dest.x1<=width-margin+.01 and dest.y1<height-65
    p.insert_image(dest,filename=str(path))
    accepted=q['answer'].get('choices',[q['answer']['choice']]);answer='/'.join('①②③④⑤'[v-1] for v in accepted);page_answers.append(f'{seq:03}번 {answer}')
    manifest.append({'sequence':seq,'id':q['id'],'category':q['classification']['category'],'page':pn,'column':col,'row':row,'fullColumn':entry['fullColumn'],'fullWidth':entry['fullWidth'],'rect':list(dest),'originalNumberMasks':masks,'answers':accepted,'imageSize':[iw,ih],'printedWidth':dest.width,'printedHeight':dest.height})
   answers='정답   '+'   ·   '.join(page_answers);text(p,width-margin,height-47,answers,6,True);text(p,width-margin,height-25,f'{pn} / {total}',8,True)
 assert seq==594 and len(doc)==total
 doc.set_metadata({'title':'통신이론 기출문제 594문항','subject':'9급 지방직·서울시 통신이론 및 국가직 무선공학개론 공통범위 · A4 · 1 3 / 2 4','author':'통신이론 문제은행'})
 if pending:toc.append([1,'목차 외 · 분류 검토 문제',next(m['page'] for m in manifest if m['category']=='pending')])
 doc.set_toc(toc);doc.subset_fonts();args.output.parent.mkdir(parents=True,exist_ok=True);doc.save(args.output,garbage=4,deflate=True);doc.close()
 check=fitz.open(args.output);assert len(check)==total
 for pn in range(1,total+1):
  page=check[pn-1];items=[m for m in manifest if m['page']==pn]
  assert len(page.get_image_info())==len(items)
  if any(m['fullWidth'] for m in items):assert len(items)==1
  assert [(m['column'],m['row']) for m in items]==sorted((m['column'],m['row']) for m in items)
  for col in [0,1]:
   column=[m for m in items if m['column']==col]
   if any(m['fullColumn'] for m in column):assert len(column)==1 and column[0]['row']==0
  nums=[w for w in page.get_text('words') if re.fullmatch(r'\d{3}',w[4]) and w[1]<height-70]
  actual=[w[4] for w in sorted(nums,key=lambda w:(round(w[1]/100),w[0]))]
  expected=[f'{m["sequence"]:03}' for m in sorted(items,key=lambda m:(m['row'],m['column']))]
  assert actual==expected,(pn,actual,expected)
  assert f'{pn} / {total}' in page.get_text()
  if [1,2] in [m['answers'] for m in items]:assert '①/②' in page.get_text()
  page.get_pixmap(matrix=fitz.Matrix(.9,.9),alpha=False).save(work/f'page-{pn:03}.png')
 assert {m['id'] for m in manifest}=={q['id'] for q in qs}
 (work/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 assert all(next(m for m in manifest if m['sequence']==n)['fullColumn'] for n in [160,162,236])
 assert len(check.get_toc())==10 and cover_count==9
 assert next(m for m in manifest if m['sequence']==562)['fullColumn']
 assert not next(m for m in manifest if m['sequence']==562)['fullWidth']
 assert next(m['page'] for m in manifest if m['sequence']==588)==next(m['page'] for m in manifest if m['sequence']==589)
 (ROOT/'review/full-print-audit.json').write_text(json.dumps({'questionCount':594,'pageCount':total,'coverCount':cover_count,'ordering':'column-major: 1 3 / 2 4; tall questions occupy one full column','rightInsetPoints':12,'maximumImageScale':.36,'fullColumnSequences':[m['sequence'] for m in manifest if m['fullColumn']],'chapters':[{'label':c['label'],'questionCount':len(v),'cover':c['id']!='pending'} for c,v in groups],'multipleAnswerIds':[q['id'] for q in qs if len(q['answer'].get('choices',[]))>1],'manifest':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
 print('PASS:',total,'A4 pages;',cover_count,'covers; 594 unique questions; full-column tall questions, column-major layout, answer sets, original number masks, and all-page render verified;',args.output)

if __name__=='__main__':main()
