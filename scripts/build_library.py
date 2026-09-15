"""Generate the library from every reading HTML; no third-party packages needed."""
import argparse
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import shutil
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = {}
        self.capture = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.capture and tag == 'br':
            self.values[self.capture[1]] += ' '
        if self.capture is None:
            key = tag if tag in ('title', 'h1') else None
            if tag == 'p' and 'subtitle' in attrs.get('class', '').split():
                key = 'subtitle'
            if key and key not in self.values:
                self.values[key] = ''
                self.capture = (tag, key)

    def handle_data(self, data):
        if self.capture:
            self.values[self.capture[1]] += data

    def handle_endtag(self, tag):
        if self.capture and self.capture[0] == tag:
            self.capture = None


STYLE = '''
:root{color-scheme:dark;--bg:#131614;--ink:#e0e2d8;--muted:#a4ada1;--line:#353e34;--accent:#c8d6a5}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,"Malgun Gothic",sans-serif}a{color:inherit}a:focus-visible,input:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:5px}.bar{border-bottom:1px solid var(--line);padding:24px 5%;display:flex;justify-content:space-between;gap:20px;color:var(--accent);font-size:11px;letter-spacing:.15em}.bar a{text-decoration:none}main{max-width:1180px;margin:auto;padding:70px 30px}h1{font-family:"Batang",serif;font-size:clamp(38px,6vw,68px);font-weight:400;letter-spacing:-.06em;margin:22px 0}.controls{margin:48px 0 24px;display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap}label{display:block;font-size:12px;margin-bottom:10px;color:var(--muted)}input{font:inherit;font-size:15px;width:360px;max-width:100%;padding:14px 16px;background:#1a1e1b;border:1px solid var(--line);border-radius:5px;color:var(--ink)}.count{font-size:13px;color:var(--accent)}.shelf{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}.card{display:flex;flex-direction:column;min-height:200px;padding:28px 26px;text-decoration:none;background:linear-gradient(140deg,#242b20,#191e1a);border:1px solid #3c4535;border-radius:3px;box-shadow:inset 5px 0 0 #101411}.card:nth-child(2n){background:linear-gradient(140deg,#272b2c,#191d1e)}.card:nth-child(3n){background:linear-gradient(140deg,#2c2922,#1e1b17)}.card:hover{border-color:var(--accent)}.card h2{font-family:"Batang",serif;font-size:24px;font-weight:500;line-height:1.6;letter-spacing:-.04em;word-break:keep-all;overflow-wrap:anywhere;margin:0 0 24px}.card .open{margin-top:auto;padding-top:16px;border-top:1px solid #ffffff18;font-size:12px;color:var(--accent)}[hidden]{display:none!important}.empty{padding:40px 0;color:var(--muted)}@media(max-width:900px){.shelf{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){main{padding:44px 22px}.shelf{grid-template-columns:1fr}.card{min-height:180px}.search-field{width:100%}.view-controls{width:100%;justify-content:space-between}input{width:100%}}
.view-controls{display:flex;align-items:center;gap:20px}.view-toggle{display:flex;gap:4px;padding:4px;border:1px solid var(--line);border-radius:6px}.view-toggle button{font:inherit;font-size:13px;padding:10px 16px;border:0;border-radius:3px;background:transparent;color:var(--muted);cursor:pointer}.view-toggle button:hover{color:var(--ink)}.view-toggle button[aria-pressed="true"]{background:var(--accent);color:var(--bg)}
.shelf[data-view="list"]{grid-template-columns:minmax(0,1fr);gap:10px}.shelf[data-view="list"] .card{flex-direction:row;align-items:center;gap:24px;min-height:0;padding:20px 24px}.shelf[data-view="list"] h2{flex:1;min-width:0;font-family:inherit;font-size:17px;margin:0}.shelf[data-view="list"] .open{flex-shrink:0;margin:0;padding:0;border:0}
@media(max-width:600px){.shelf[data-view="list"] .card{padding:18px 16px;gap:14px}.shelf[data-view="list"] h2{font-size:15px}}
'''

SEARCH = '''
const input=document.getElementById('search');
const cards=[...document.querySelectorAll('.card')];
const count=document.getElementById('count');
const shelf=document.getElementById('shelf');
const viewButtons=[...document.querySelectorAll('[data-view-button]')];
function setView(view){
 const selected=view==='list'?'list':'card';
 shelf.dataset.view=selected;
 for(const button of viewButtons){
  button.setAttribute('aria-pressed',String(button.dataset.viewButton===selected));
 }
}
for(const button of viewButtons){
 button.addEventListener('click',()=>{
  setView(button.dataset.viewButton);
  try{localStorage.setItem('library-view',shelf.dataset.view);}catch{}
 });
}
try{setView(localStorage.getItem('library-view'));}catch{setView('card');}
input.addEventListener('input',()=>{
 const term=input.value.normalize('NFC').toLocaleLowerCase().trim();
 let visible=0;
 for(const card of cards){
  card.hidden=!card.dataset.search.normalize('NFC').toLocaleLowerCase().includes(term);
  if(!card.hidden)visible++;
 }
 count.textContent=term?`${visible}편 / 전체 ${cards.length}편`:`전체 ${cards.length}편`;
 document.getElementById('no-results').hidden=visible!==0;
});
'''


def collect(root):
    books = []
    folder = root / 'html'
    for path in sorted(folder.rglob('*'), key=lambda p: p.as_posix().casefold()):
        if not path.is_file() or path.suffix.lower() not in ('.html', '.htm'):
            continue
        if path == folder / 'index.html':
            continue
        meta = Metadata()
        meta.feed(path.read_text(encoding='utf-8-sig'))
        title = meta.values.get('h1') or meta.values.get('title') or path.stem
        title = ' '.join(title.removesuffix(' · 영상 서재').split())
        books.append((path.relative_to(folder).as_posix(), title,
                      ' '.join(meta.values.get('subtitle', '').split())))
    return books


def render(books, prefix):
    cards = []
    for path, title, subtitle in books:
        search = escape(' '.join((title, subtitle, path)), quote=True)
        cards.append(f'<a class="card" href="{quote(prefix + path, safe="/")}" data-search="{search}">'
                     f'<h2>{escape(title)}</h2>'
                     f'<div class="open">펼쳐 읽기 ↗</div></a>')
    empty = '<p class="empty">아직 등록된 HTML이 없습니다.</p>' if not books else ''
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><title>영상 서재</title><style>{STYLE}</style></head>
<body><header class="bar"><a href="index.html">영상 서재 / LIBRARY</a></header>
<main><h1>영상 서재</h1>
<div class="controls"><div class="search-field"><label for="search">서재에서 찾기</label><input id="search" type="search" placeholder="제목 또는 파일명 검색" autocomplete="off"></div><div class="view-controls"><p id="count" class="count" role="status" aria-live="polite">전체 {len(books)}편</p><div class="view-toggle" role="group" aria-label="보기 방식"><button type="button" data-view-button="card" aria-pressed="true" aria-controls="shelf">카드</button><button type="button" data-view-button="list" aria-pressed="false" aria-controls="shelf">리스트</button></div></div></div>
<div id="shelf" class="shelf" data-view="card">{''.join(cards)}</div>{empty}<p id="no-results" class="empty" hidden>검색 결과가 없습니다.</p>
</main><script>{SEARCH}</script></body></html>
'''


def build(root=ROOT, output=None):
    if output and output.exists():
        raise FileExistsError(f'Output directory already exists: {output}')
    (root / 'html').mkdir(parents=True, exist_ok=True)
    books = collect(root)
    (root / 'index.html').write_text(render(books, 'html/'), encoding='utf-8')
    (root / 'html/index.html').write_text(render(books, ''), encoding='utf-8')
    if output:
        # A fresh publish directory avoids stale deleted books and excludes repo internals.
        output.mkdir(parents=True, exist_ok=False)
        shutil.copy2(root / 'index.html', output / 'index.html')
        # Publish only HTML; transcripts and application code stay out of Pages.
        for source in (root / 'html').rglob('*'):
            if source.is_file() and source.suffix.lower() in ('.html', '.htm'):
                target = output / source.relative_to(root)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        (output / '.nojekyll').touch()
    return len(books)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='New, non-existing directory for Pages upload')
    args = parser.parse_args()
    print(f'Library generated: {build(output=args.output)} HTML books')
