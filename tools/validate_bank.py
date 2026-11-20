from pathlib import Path
import json,collections
from PIL import Image
root=Path(__file__).resolve().parents[1]
q=json.loads((root/'data/questions.json').read_text(encoding='utf-8'));tax=json.loads((root/'data/taxonomy.json').read_text(encoding='utf-8'));e=json.loads((root/'data/exams.json').read_text(encoding='utf-8'))
assert len(q)==320 and len(e)==16
assert len({x['id'] for x in q})==len(q)
assert sum(len(c['topics']) for c in tax['categories'] if c['id']!='pending')==73
valid={t['id']:c['id'] for c in tax['categories'] for t in c['topics']}
for exam in e:
 items=[x for x in q if x['examId']==exam['id']]
 assert sorted(x['number'] for x in items)==list(range(1,21)),exam['id']
 assert (root/f"review/contact-sheets/{exam['id']}.jpg").exists()
for x in q:
 assert x['agency'] in ['지방직','서울시'] and x['year']>=2009
 assert 1<=x['answer']['choice']<=x['choiceCount'],x['id']
 assert valid[x['classification']['primaryTopic']]==x['classification']['category']
 assert (root/x['source']['pdf']).exists()
 assert len(set('①②③④⑤')&set(x['ocrText']))>=x['choiceCount'],x['id']
 with Image.open(root/x['image']['src']) as im:assert im.size==(x['image']['width'],x['image']['height']) and min(im.size)>30
 if x['answer']['status']=='official': assert (root/x['answer']['sources'][0]['url']).exists()
loaded=json.loads((root/'data/data.js').read_text(encoding='utf-8').removeprefix('window.QUESTION_BANK = ').strip().removesuffix(';'))
assert loaded['questions']==q and loaded['taxonomy']==tax and loaded['exams']==e
print('PASS: 320 questions, 16 exams, 73 book sections, answer ranges, classification references, images, source PDFs, official answer references, contact sheets and browser payload')
