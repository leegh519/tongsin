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
 assert valid[x['classification']['primaryTopic']]==x['classification']['category']
 assert (root/x['source']['pdf']).exists()
 if x['agency']=='국가직':
  assert x['subject']=='무선공학개론'
  source=BeautifulSoup((root/f"sources/{x['examId']}.html").read_text(encoding='utf-8'),'html.parser')
  assert len(source.select(f"article#q{x['number']} ol.choices > li"))==x['choiceCount']
 else:assert len(set('①②③④⑤')&set(x['ocrText']))>=x['choiceCount'],x['id']
 with Image.open(root/x['image']['src']) as im:assert im.size==(x['image']['width'],x['image']['height']) and min(im.size)>30
 if x['answer']['status']=='official':assert (root/x['answer']['sources'][0]['url']).exists()
payload=json.loads((root/'data/data.js').read_text(encoding='utf-8').removeprefix('window.QUESTION_BANK = ').strip().removesuffix(';'))
assert payload['questions']==q and payload['taxonomy']==tax and payload['exams']==exams
print('PASS: 594 grade-9 questions, 34 exams, 43 study topics from 73 book sections; national inclusion/exclusion IDs, source subject, answer ranges, classification, images, original PDFs, official answer files, contact sheets and browser payload')
