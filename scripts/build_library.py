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
:root{color-scheme:dark;--bg:#131614;--ink:#e0e2d8;--muted:#a4ada1;--line:#353e34;--accent:#c8d6a5}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,"Malgun Gothic",sans-serif}a{color:inherit}a:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:5px}.bar{border-bottom:1px solid var(--line);padding:24px 5%;display:flex;justify-content:space-between;gap:20px;color:var(--accent);font-size:11px;letter-spacing:.15em}.bar a{text-decoration:none}main{max-width:1180px;margin:auto;padding:70px 30px}.eyebrow{color:var(--accent);font-size:11px;letter-spacing:.2em}h1{font-family:"Batang",serif;font-size:clamp(38px,6vw,68px);font-weight:400;letter-spacing:-.06em;margin:22px 0}.intro{color:var(--muted);line-height:1.9}.controls{margin:48px 0 24px;display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap}label{display:block;font-size:12px;margin-bottom:10px;color:var(--muted)}input{font:inherit;font-size:15px;width:360px;max-width:100%;padding:14px 16px;background:#1a1e1b;border:1px solid var(--line);border-radius:5px;color:var(--ink)}.count{font-size:13px;color:var(--accent)}.shelf{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}.card{display:flex;flex-direction:column;min-height:310px;padding:28px 26px;text-decoration:none;background:linear-gradient(140deg,#242b20,#191e1a);border:1px solid #3c4535;border-radius:3px;box-shadow:inset 5px 0 0 #101411}.card:nth-child(2n){background:linear-gradient(140deg,#272b2c,#191d1e)}.card:nth-child(3n){background:linear-gradient(140deg,#2c2922,#1e1b17)}.card:hover{border-color:var(--accent)}.card small{color:var(--accent);font-size:10px;letter-spacing:.1em}.card h2{font-family:"Batang",serif;font-size:24px;font-weight:500;line-height:1.6;letter-spacing:-.04em;word-break:keep-all;overflow-wrap:anywhere;margin:24px 0 14px}.card p{color:var(--muted);font-size:12px;line-height:1.8;margin:0 0 22px;overflow-wrap:anywhere}.card .open{margin-top:auto;padding-top:16px;border-top:1px solid #ffffff18;font-size:12px;color:var(--accent)}[hidden]{display:none!important}.empty{padding:40px 0;color:var(--muted)}footer{margin-top:48px;border-top:1px solid var(--line);padding-top:22px;color:var(--muted);font-size:12px;line-height:1.9}@media(max-width:900px){.shelf{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){main{padding:44px 22px}.shelf{grid-template-columns:1fr}.card{min-height:260px}.controls>div{width:100%}input{width:100%}.bar span{display:none}}
'''

SEARCH = '''
const input=document.getElementById('search');
const cards=[...document.querySelectorAll('.card')];
const count=document.getElementById('count');
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
    for number, (path, title, subtitle) in enumerate(books, 1):
        search = escape(' '.join((title, subtitle, path)), quote=True)
        description = subtitle or path
        cards.append(f'<a class="card" href="{quote(prefix + path, safe="/")}" data-search="{search}">'
                     f'<small>BOOK {number:02d}</small><h2>{escape(title)}</h2>'
                     f'<p>{escape(description)}</p><div class="open">펼쳐 읽기 ↗</div></a>')
    empty = '<p class="empty">아직 등록된 HTML이 없습니다.</p>' if not books else ''
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><title>영상 서재</title><style>{STYLE}</style></head>
<body><header class="bar"><a href="index.html">영상 서재 / LIBRARY</a><span>읽는 속도로, 더 깊이</span></header>
<main><div class="eyebrow">A QUIET PLACE TO READ</div><h1>영상에서, 책으로.</h1><p class="intro">모아 둔 이야기를 한자리에서.<br>마음이 가는 한 권을 펼쳐 보세요.</p>
<div class="controls"><div><label for="search">서재에서 찾기</label><input id="search" type="search" placeholder="제목 또는 파일명 검색" autocomplete="off"></div><p id="count" class="count" role="status" aria-live="polite">전체 {len(books)}편</p></div>
<div class="shelf">{''.join(cards)}</div>{empty}<p id="no-results" class="empty" hidden>검색 결과가 없습니다. 다른 검색어로 찾아보세요.</p>
<footer>영상 서재 · 읽고 싶은 이야기를 천천히.</footer></main><script>{SEARCH}</script></body></html>
'''


def build(root=ROOT, output=None):
    books = collect(root)
    (root / 'index.html').write_text(render(books, 'html/'), encoding='utf-8')
    (root / 'html/index.html').write_text(render(books, ''), encoding='utf-8')
    if output:
        # A fresh publish directory avoids stale deleted books and excludes repo internals.
        output.mkdir(parents=True, exist_ok=False)
        shutil.copy2(root / 'index.html', output / 'index.html')
        for name in ('html', '원본 유튜브 요약 텍스트'):
            source = root / name
            if source.exists():
                shutil.copytree(source, output / name)
        (output / '.nojekyll').touch()
    return len(books)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='New, non-existing directory for Pages upload')
    args = parser.parse_args()
    print(f'Library generated: {build(output=args.output)} HTML books')
