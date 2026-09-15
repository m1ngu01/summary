import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from transcript import extract


class ExtractionTests(unittest.TestCase):
    def downloader(self, info, payload=None):
        def factory(options):
            downloader = Mock()
            downloader.__enter__ = Mock(return_value=downloader)
            downloader.__exit__ = Mock(return_value=False)
            def extract_info(url, download=False):
                if download:
                    Path(options['outtmpl'].replace('%(ext)s', 'webm')).write_bytes(b'audio')
                return info
            downloader.extract_info.side_effect = extract_info
            downloader.urlopen.side_effect = lambda _: io.BytesIO(json.dumps(payload).encode())
            return downloader
        return SimpleNamespace(YoutubeDL=factory)

    def test_captions_do_not_call_audio_api(self):
        info = {'title': 'Title', 'subtitles': {'ko': [{'ext': 'json3', 'url': 'caption'}]}}
        fake = self.downloader(info, {'events': [{'segs': [{'utf8': 'original speech'}]}]})
        client = Mock()
        with patch.dict('sys.modules', yt_dlp=fake):
            result = extract('https://youtu.be/abcdefghijk', client=client, log=lambda _: None)
        self.assertEqual(result['text'], 'original speech')
        self.assertEqual(result['method'], 'subtitles:ko')
        client.audio.transcriptions.create.assert_not_called()

    def test_missing_captions_requires_key(self):
        with patch.dict('sys.modules', yt_dlp=self.downloader({'title': 'Title'})):
            with self.assertRaisesRegex(RuntimeError, 'API 키'):
                extract('https://youtu.be/abcdefghijk', log=lambda _: None)

    def test_audio_fallback_preserves_chunk_order(self):
        fake = self.downloader({'title': 'Title'})
        def segment(args, **kwargs):
            for number in range(2):
                Path(args[-1].replace('%04d', f'{number:04d}')).write_bytes(b'RIFF-test')
            return SimpleNamespace(returncode=0)
        client = Mock()
        client.audio.transcriptions.create.side_effect = [SimpleNamespace(text='first'), SimpleNamespace(text='second')]
        with patch.dict('sys.modules', yt_dlp=fake), patch('transcript.shutil.which', return_value='ffmpeg'), \
                patch('transcript.subprocess.run', side_effect=segment):
            result = extract('https://youtu.be/abcdefghijk', client=client, log=lambda _: None)
        self.assertEqual(result['text'], 'first\n\nsecond')
        self.assertEqual(client.audio.transcriptions.create.call_count, 2)
        for call in client.audio.transcriptions.create.call_args_list:
            self.assertTrue(call.kwargs['file'].closed)


if __name__ == '__main__':
    unittest.main()
