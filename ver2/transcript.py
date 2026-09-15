"""YouTube captions first, segmented audio transcription as a fallback."""
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs


def video_url(value):
    parsed = urlparse(value.strip())
    if parsed.scheme not in ('https', 'http') or parsed.username or parsed.password:
        raise ValueError('올바른 YouTube 영상 URL을 입력하세요.')
    host = (parsed.hostname or '').lower()
    pieces = parsed.path.strip('/').split('/')
    if host == 'youtu.be':
        ident = pieces[0]
    elif host in ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com'):
        if parsed.path == '/watch':
            ident = parse_qs(parsed.query).get('v', [''])[0]
        elif len(pieces) == 2 and pieces[0] in ('shorts', 'live', 'embed'):
            ident = pieces[1]
        else:
            ident = ''
    else:
        ident = ''
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', ident):
        raise ValueError('개별 YouTube 영상 링크를 입력하세요. 재생목록 URL은 지원하지 않습니다.')
    return ident, f'https://www.youtube.com/watch?v={ident}'


def parse_json3(payload):
    lines = []
    for event in payload.get('events', []):
        text = ''.join(segment.get('utf8', '') for segment in event.get('segs', []))
        text = ' '.join(text.split())
        if text:
            # Do not deduplicate repeated speech: repetition may be intentional.
            lines.append(text)
    return '\n'.join(lines)


def caption_candidates(info, preferred):
    for group in ('subtitles', 'automatic_captions'):
        tracks = info.get(group) or {}
        languages = list(dict.fromkeys([preferred, preferred + '-orig', info.get('language'), 'ko', 'en']))
        for language in languages:
            if not language:
                continue
            for track in tracks.get(language, []):
                if track.get('ext') == 'json3':
                    yield group, language, track


def extract(url, language='ko', client=None, audio_model='whisper-1', log=print):
    ident, canonical = video_url(url)
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError('ver2/requirements.txt의 패키지를 설치하세요.') from exc
    options = {'quiet': True, 'no_warnings': True, 'noplaylist': True,
               'socket_timeout': 30, 'retries': 2}
    runtimes = {name: {} for name in ('deno', 'node') if shutil.which(name)}
    if runtimes:
        options['js_runtimes'] = runtimes
    log('영상 정보와 자막 확인 중…')
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(canonical, download=False)
        if info.get('is_live'):
            raise ValueError('실시간 방송은 종료된 뒤 처리하세요.')
        for kind, lang, track in caption_candidates(info, language):
            try:
                with downloader.urlopen(track['url']) as response:
                    raw = json.loads(response.read().decode('utf-8'))
                text = parse_json3(raw)
                if text.strip():
                    return {'id': ident, 'url': canonical, 'title': info.get('title') or ident,
                            'text': text, 'method': f'{kind}:{lang}'}
            except Exception:
                log('자막을 읽지 못했습니다. 다음 자막 또는 음성 인식을 확인합니다.')
    if client is None:
        raise RuntimeError('사용 가능한 자막이 없습니다. 음성 인식을 위해 OpenAI API 키를 입력하세요.')
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        try:
            from imageio_ffmpeg import get_ffmpeg_exe
            ffmpeg = get_ffmpeg_exe()
        except (ImportError, RuntimeError) as exc:
            raise RuntimeError('음성 분할용 FFmpeg가 없습니다. ver2/requirements.txt를 설치하세요.') from exc
    with tempfile.TemporaryDirectory(prefix='summary-audio-') as tmp:
        folder = Path(tmp)
        log('자막이 없어 음성을 다운로드합니다…')
        with yt_dlp.YoutubeDL(dict(options, format='bestaudio/best', outtmpl=str(folder / 'audio.%(ext)s'))) as downloader:
            downloader.extract_info(canonical, download=True)
        audio = next((p for p in folder.glob('audio.*') if p.suffix not in ('.part', '.ytdl')), None)
        if audio is None:
            raise RuntimeError('다운로드한 음성 파일을 찾을 수 없습니다.')
        # 10 minute mono PCM at 16 kHz is ~19.2 MB, below the upload limit.
        log('긴 음성을 10분 단위로 나누는 중…')
        result = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-i', str(audio),
                                 '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le',
                                 '-f', 'segment', '-segment_time', '600', str(folder / 'part-%04d.wav')],
                                capture_output=True, timeout=1800,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode:
            raise RuntimeError('음성 분할 실패: ' + result.stderr.decode('utf-8', errors='replace')[-1000:])
        parts = sorted(folder.glob('part-*.wav'))
        if not parts:
            raise RuntimeError('음성 분할 결과가 없습니다.')
        texts = []
        for number, part in enumerate(parts, 1):
            log(f'음성 인식 {number}/{len(parts)}…')
            if part.stat().st_size >= 25_000_000:
                raise RuntimeError('음성 조각이 업로드 제한을 초과했습니다.')
            with part.open('rb') as stream:
                response = client.audio.transcriptions.create(
                    model=audio_model, file=stream, response_format='json',
                    **({'language': language} if language else {}))
            if not response.text.strip():
                raise RuntimeError(f'{number}번째 음성 조각의 인식 결과가 비어 있습니다.')
            texts.append(response.text.strip())
        return {'id': ident, 'url': canonical, 'title': info.get('title') or ident,
                'text': '\n\n'.join(texts), 'method': 'audio:' + audio_model}
