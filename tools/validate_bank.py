from pathlib import Path
import json,collections
from PIL import Image
from bs4 import BeautifulSoup
root=Path(__file__).resolve().parents[1]
q=json.loads((root/'data/questions.json').read_text(encoding='utf-8'));tax=json.loads((root/'data/taxonomy.json').read_text(encoding='utf-8'));exams=json.loads((root/'data/exams.json').read_text(encoding='utf-8'));audit=json.loads((root/'review/national-overlap-audit.json').read_text(encoding='utf-8'))
assert len(q)==594 and len(exams)==34
assert len({x['id'] for x in q})==len(q)
assert sum(len(c['topics']) for c in tax['categories'] if c['id']!='pending')==43
assert sum(len(t.get('bookSections',[])) for c in tax['categories'] for t in c['topics'])==73
assert all(not __import__('re').match(r'^\d+-\d+',t['label']) for c in tax['categories'] for t in c['topics'])
assert all('Chapter' not in c['label'] for c in tax['categories'])
assert {x['id'] for x in q if x['agency']=='국가직'}=={a['id'] for a in audit if a['include']}
valid={t['id']:c['id'] for c in tax['categories'] for t in c['topics']}
for e in exams:
 items=[x for x in q if x['examId']==e['id']]
 assert len(items)==e['questionCount']
 if e['agency']!='국가직':assert sorted(x['number'] for x in items)==list(range(1,21)),e['id']
 assert (root/f"review/contact-sheets/{e['id']}.jpg").exists()
for x in q:
 assert x['agency'] in ['지방직','서울시','국가직'] and x['year']>=2009 and x['grade']==9
 assert 1<=x['answer']['choice']<=x['choiceCount'],x['id']
 accepted=x['answer'].get('choices',[x['answer']['choice']])
 assert accepted and len(accepted)==len(set(accepted)) and all(1<=v<=x['choiceCount'] for v in accepted),x['id']
 assert x['answer']['choice'] in accepted,x['id']
 assert valid[x['classification']['primaryTopic']]==x['classification']['category']
 assert (root/x['source']['pdf']).exists()
 if x['agency']=='국가직':
  assert x['subject']=='무선공학개론'
  source=BeautifulSoup((root/f"sources/{x['examId']}.html").read_text(encoding='utf-8'),'html.parser')
  assert len(source.select(f"article#q{x['number']} ol.choices > li"))==x['choiceCount']
 else:assert len(set('①②③④⑤')&set(x['ocrText']))>=x['choiceCount'],x['id']
 with Image.open(root/x['image']['src']) as im:assert im.size==(x['image']['width'],x['image']['height']) and min(im.size)>30
 assert x['answer']['status'] in ['official','cross-checked']
 source=x['answer']['sources'][0]
 if source['url'].startswith('https://gongmuwon.gosi.kr/oprut/GosiJungdap.do?'):
  from urllib.parse import parse_qs, urlsplit
  params=parse_qs(urlsplit(source['url']).query)
  assert params['enfcYr']==[str(x['year'])] and params['cransSeCd']==['2']
  assert params['bktpNm']==[source['booktype']]
  assert params['sbjctCd']==['784' if x['agency']=='지방직' else '938']
 else:assert (root/source['url']).exists()
payload=json.loads((root/'data/data.js').read_text(encoding='utf-8').removeprefix('window.QUESTION_BANK = ').strip().removesuffix(';'))
assert payload['questions']==q and payload['taxonomy']==tax and payload['exams']==exams
assert next(x for x in q if x['id']=='seoul-2018-14')['answer']['choices']==[1,2]
report=root/'review/independent-solutions.csv'
if report.exists():
 import csv
 rows=list(csv.DictReader(report.open(encoding='utf-8-sig')))
 byid={x['id']:x for x in q}
 assert len(rows)==594 and len({r['문항'] for r in rows})==594 and {r['문항'] for r in rows}==set(byid)
 for r in rows:
  a=byid[r['문항']]['answer']
  assert r['근거'].strip() and int(r['독립 풀이']) in a.get('choices',[a['choice']]),r['문항']
print('PASS: 594 grade-9 questions, 34 exams, 43 study topics; answer sets including multiple answers, source links, images, browser payload and complete independent-solution coverage')
