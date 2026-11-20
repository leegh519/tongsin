from pathlib import Path
import json,re,shutil
import pymupdf as fitz
from bs4 import BeautifulSoup
from PIL import Image,ImageChops,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
chapters=[
('신호해석과 시스템','신호의 분류|기본 신호 파형|직교 벡터 좌표계와 직교 함수 좌표계|푸리에 급수(Fourier Series)|푸리에 변환(Fourier Transform)|콘볼루션(convolution)|표본화 정리(Sampling theorem)|변조|시스템의 특성|임펄스 응답과 전달 함수|이상 필터(ideal filter)'),
('아날로그 변복조','아날로그 변복조의 구성도|AM(Amplitude Modulation)|FM(Frequency Modulation)|PM(Phase Modulation)|FM과 PM의 변복조기 비교|아날로그 시스템 성능 분석'),
('랜덤 변수와 랜덤 과정','확률 이론|랜덤 변수|랜덤 변수의 확률 분포 함수와 확률 밀도 함수|결합 확률의 확률 분포 함수와 확률 밀도 함수|대표적인 랜덤 변수의 확률 분포 함수와 확률 밀도 함수|랜덤 변수의 합의 경우 확률 분포 함수와 확률 밀도 함수|랜덤 변수 변환|기대값과 중앙 모멘트|랜덤 과정|정상 과정(stationary process)|에르고딕 과정|자기 상관 함수와 상호 상관 함수|전력 밀도 스펙트럼과 평균 전력|에너지 밀도 스펙트럼과 에너지|실효치와 평균치|잡음'),
('디지털 변복조','디지털 변복조의 구성도|데이터 전송 방법|정합 필터(matched filter)|등화기|디지털 변조의 종류|디지털 변조의 특성 비교|통신 속도와 채널 용량'),
('스펙트럼 확산 통신 방식','스펙트럼 확산 통신의 개요|스펙트럼 확산 통신의 방식|스펙트럼 확산 통신의 응용'),
('이동통신과 주요 무선통신 기술','셀룰러 이동통신의 개념과 세대별 분류|셀(cell)의 종류와 크기|이동통신 시스템의 기본 구성|이동통신 시스템 구성도|순방향 채널과 역방향 채널|이동통신 관련 용어|주파수 재사용 거리(D)|IS-95 CDMA와 WCDMA|LTE(Long Term Evolution)|공공안전통신망|5세대 이동통신|주요 무선통신 기술'),
('음성의 디지털 부호화 기술','파형 부호화 방식|보코딩 방식'),
('정보이론과 부호화','정보이론의 개념|정보량과 단위|총 정보량과 평균 정보량|부호화 방법과 Huffman 부호|이산적 통신로|상호 정보량|채널 용량'),
('OSI-7 계층과 프로토콜','프로토콜의 개념과 기능|OSI-7 layer|TCP/IP|전송제어 프로토콜|착오 제어|통신망의 분류와 특징|교환 방식|데이터 전송 방식|광통신')]
tax={'version':1,'categories':[],'studyTags':[],'auxiliaryTags':{}}
for c,(title,sections) in enumerate(chapters,1):
 tax['categories'].append({'id':f'ch{c:02}','label':title,'topics':[{'id':f'{c}-{i}','label':f'{c}-{i} {s}','subtopics':[],'concepts':[]} for i,s in enumerate(sections.split('|'),1)]})
if (ROOT/'data/taxonomy.json').exists(): tax=json.loads((ROOT/'data/taxonomy.json').read_text(encoding='utf-8'))
else: (ROOT/'data/taxonomy.json').write_text(json.dumps(tax,ensure_ascii=False,indent=2),encoding='utf-8')
questions=[];exams=[]
classifications=json.loads((ROOT/'data/classifications.json').read_text(encoding='utf-8')) if (ROOT/'data/classifications.json').exists() else {}
for file in sorted((ROOT/'sources').glob('*.pdf')):
 if file.stem.startswith('compilation'):continue
 slug,year=file.stem.rsplit('-',1);year=int(year);agency={'local':'지방직','seoul':'서울시','national-radio':'국가직'}[slug];d=fitz.open(file);anchors=[]
 for pi,p in enumerate(d):
  for b in p.get_text('dict')['blocks']:
   for line in b.get('lines',[]):
    t=''.join(s['text'] for s in line['spans']);m=re.match(r'^\s*(?:문\s*)?(\d{1,2})\s*\.\s*',t)
    if m and 1<=int(m[1])<=20:
     x,y,*_=line['bbox']
     # Reject decimal values in formulas: question numbers sit at the column margin.
     if (slug=='seoul' and (abs(x-65)<3 or abs(x-71)<3 or abs(x-370)<3 or abs(x-376)<3)) or (slug!='seoul' and any(abs(x-v)<3 for v in [14,17,22,23,31,303,320,361,371,376,377])):anchors.append({'number':int(m[1]),'page':pi,'x':x,'y':y})
 for pi,p in enumerate(d):
  words=p.get_text('words')
  for w in words:
   if w[4]=='문':
    near=[v for v in words if abs(v[1]-w[1])<2 and 0<v[0]-w[0]<30 and re.fullmatch(r'\d{1,2}\.',v[4])]
    if near:
     n=int(near[0][4][:-1])
     if 1<=n<=20 and not any(a['number']==n for a in anchors):anchors.append({'number':n,'page':pi,'x':w[0],'y':w[1]})
 assert sorted(a['number'] for a in anchors)==list(range(1,21)),(file,anchors)
 answers={};answerfile=None
 if slug!='seoul':
  html=(ROOT/f'sources/{file.stem}.html').read_text(encoding='utf-8')
  if 'ì' in html: html=html.encode('latin1').decode('utf-8')
  s=BeautifulSoup(html,'html.parser')
  for a in s.select('article.q'):
   m=re.search(r'정답\s*([①②③④⑤])',a.select_one('.answer-box').text) if a.select_one('.answer-box') else None
   if m:answers[int(a['id'][1:])]='①②③④⑤'.index(m[1])+1
 # Official all-subject answer keys retained from the reference repository.
 official=Path(__file__).resolve().parents[1]/'official-answers'/f'{year}-{agency}-{"정답" if slug=="seoul" else "최종정답"}.pdf'
 if official.exists():
  ad=fitz.open(official);full='\n'.join(p.get_text() for p in ad)
  book='B' if (slug=='seoul' and year==2020) or (slug!='seoul' and year>=2024) else 'A'
  pattern=(r'통신이론\s*[_（(]?\s*9급\s*[)）]?\s*'+book+r'\s*(?:형)?\s*((?:[1-5]\s*){20})' if slug=='seoul' else rf'{"무선공학개론" if slug=="national-radio" else "통신이론"}\s*[ⒶⒷⒸⒹABCD가나]\s*((?:[1-5]\s*){20})')
  m=re.search(pattern,full)
  if m:
   answers={i:int(v) for i,v in enumerate(re.findall('[1-5]',m[1]),1)};answerfile='official-answers/'+official.name
  else:print('OFFICIAL PARSE PENDING',file.stem)
 sourcesurl=f'https://cbtnow.kr/시험/9급-{"국가직-무선공학개론" if slug=="national-radio" else "지방직-통신이론"}/{year}년/' if slug!='seoul' else ('https://ingyerlog.kr/2021-9-seoul-comm/' if year==2021 else 'https://baekchwijun.tistory.com/61')
 exams.append({'id':file.stem,'year':year,'agency':agency,'title':f'{year}년 {agency} 9급 통신이론','sourcePdf':'sources/'+file.name,'questionCount':20,'sourceUrl':sourcesurl})
 for a in sorted(anchors,key=lambda a:a['number']):
  if slug=='national-radio' and f'{file.stem}-{a["number"]:02}' not in classifications: continue
  p=d[a['page']];w,h=p.rect.width,p.rect.height;right=a['x']>w/2
  col=[b for b in anchors if b['page']==a['page'] and (b['x']>w/2)==right];start=min(b['x'] for b in col)
  nxt=[b['y'] for b in col if b['y']>a['y']+1];bottom=min(nxt)-7 if nxt else h-(65 if slug=='seoul' else 5)
  other=[b['x'] for b in anchors if b['page']==a['page'] and b['x']>w/2]
  x0=start-7;x1=(min(other)-10 if other and not right else min(w-10,start+(305 if slug=='seoul' else w/2)-9))
  rect=fitz.Rect(x0,a['y']-14,x1,bottom);text=p.get_text(clip=rect)
  pix=p.get_pixmap(matrix=fitz.Matrix(2.5,2.5),clip=rect,alpha=False);im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
  # Remove printed footer page numbers only.
  draw=ImageDraw.Draw(im)
  for block in p.get_text('dict')['blocks']:
   for line in block.get('lines',[]):
    footer=''.join(span['text'] for span in line['spans'])
    if line['bbox'][1]>h-85 and re.fullmatch(r'\s*[-−]\s*\d+\s*[-−]?\s*',footer):
     bx=fitz.Rect(line['bbox'])
     draw.rectangle(((bx.x0-rect.x0-2)*2.5,(bx.y0-rect.y0-2)*2.5,(bx.x1-rect.x0+2)*2.5,(bx.y1-rect.y0+2)*2.5),fill='white')
  # Exclude page border rules at crop edges so they do not retain blank space.
  gray=im.convert('L')
  for edge in list(range(min(25,im.width)))+list(range(max(0,im.width-25),im.width)):
   if sum(gray.getpixel((edge,row))<180 for row in range(im.height))>im.height*.8:
    draw.rectangle((max(0,edge-2),0,min(im.width,edge+2),im.height),fill='white')
  for row in list(range(min(12,im.height)))+list(range(max(0,im.height-12),im.height)):
   if sum(gray.getpixel((col,row))<180 for col in range(im.width))>im.width*.85:
    draw.rectangle((0,max(0,row-2),im.width,min(im.height,row+2)),fill='white')
  box=ImageChops.difference(im,Image.new('RGB',im.size,'white')).point(lambda x:255 if x>55 else 0).getbbox()
  if box: im=im.crop((max(0,box[0]-10),max(0,box[1]-10),min(im.width,box[2]+10),min(im.height,box[3]+10)))
  path=f'assets/questions/{file.stem}-{a["number"]:02}.png';im.save(ROOT/path)
  questions.append({'id':f'{file.stem}-{a["number"]:02}','examId':file.stem,'year':year,'agency':agency,'number':a['number'],'choiceCount':5 if year==2014 and slug=='seoul' else 4,'image':{'src':path,'width':im.width,'height':im.height},'classification':{},'answer':{'choice':answers.get(a['number']),'status':'official' if answerfile else 'unverified','sources':[{'label':'공식 정답표' if answerfile else 'CBTNow 수록 정답 (공식 대조 전)','url':answerfile or sourcesurl}]},'source':{'pdf':'sources/'+file.name,'page':a['page']+1,'column':'right' if right else 'left','crop':list(rect),'url':sourcesurl},'ocrText':text,'review':{'crop':'pending','classification':'pending','answer':'approved' if answerfile else 'pending'}})
(ROOT/'data/questions.json').write_text(json.dumps(questions,ensure_ascii=False,indent=2),encoding='utf-8');(ROOT/'data/exams.json').write_text(json.dumps(exams,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'review/stems.txt').write_text('\n'.join(q['id']+' '+re.sub(r'\s+',' ',q['ocrText'].split('①')[0])[:240] for q in questions),encoding='utf-8')
print('Built',len(exams),len(questions))

if (ROOT/'data/classifications.json').exists():
 mapping=json.loads((ROOT/'data/classifications.json').read_text(encoding='utf-8'))
 for q in questions:
  q['classification']=mapping.get(q['id'],{'category':'pending','topics':['pending'],'status':'pending'})
  q['review']['classification']=q['classification']['status']
 (ROOT/'data/questions.json').write_text(json.dumps(questions,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'data/data.js').write_text('window.QUESTION_BANK = '+json.dumps({'questions':questions,'taxonomy':tax,'exams':exams},ensure_ascii=False)+';\n',encoding='utf-8')

for q in questions:
 q['grade']=9
 q['subject']='무선공학개론' if q['agency']=='국가직' else '통신이론'
for exam in exams:
 exam['grade']=9
 exam['subject']='무선공학개론' if exam['agency']=='국가직' else '통신이론'
 exam['title']=f"{exam['year']}년 {exam['agency']} 9급 {exam['subject']}"
 exam['questionCount']=sum(q['examId']==exam['id'] for q in questions)
 exam['originalQuestionCount']=20
(ROOT/'data/questions.json').write_text(json.dumps(questions,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'data/exams.json').write_text(json.dumps(exams,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'data/data.js').write_text('window.QUESTION_BANK = '+json.dumps({'questions':questions,'taxonomy':tax,'exams':exams},ensure_ascii=False)+';\n',encoding='utf-8')

if (ROOT/'data/answer_keys.json').exists():
 answer_keys=json.loads((ROOT/'data/answer_keys.json').read_text(encoding='utf-8'))
 for q in questions:
  if q['id'] in answer_keys:q['answer']=answer_keys[q['id']]
  q['review']['answer']='approved' if q['answer']['status']=='official' else 'pending'
 (ROOT/'data/questions.json').write_text(json.dumps(questions,ensure_ascii=False,indent=2),encoding='utf-8')
 (ROOT/'data/data.js').write_text('window.QUESTION_BANK = '+json.dumps({'questions':questions,'taxonomy':tax,'exams':exams},ensure_ascii=False)+';\n',encoding='utf-8')
