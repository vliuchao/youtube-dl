from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
)


class GoogleDriveIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:docs|drive)\.google\.com/(?:uc\?.*?id=|file/d/)|video\.google\.com/get_player\?.*?docid=)(?P<id>[a-zA-Z0-9_-]{28,})'
    _TESTS = [{
        'url': 'https://drive.google.com/file/d/0ByeS4oOUV-49Zzh4R1J6R09zazQ/edit?pli=1',
        'md5': '5c602afbbf2c1db91831f5d82f678554',
        'params': {
            'format': "Original"
        },
        'info_dict': {
            'id': '0ByeS4oOUV-49Zzh4R1J6R09zazQ',
            'ext': 'mp4',
            'title': 'Big Buck Bunny.mp4',
            'duration': 45,
        }
    }, {
        'url': 'https://drive.google.com/file/d/0ByeS4oOUV-49Zzh4R1J6R09zazQ/edit?pli=1',
        'md5': 'd109872761f7e7ecf353fa108c0dbe1e',
        'params': {
            'format': "37"
        },
        'info_dict': {
            'id': '0ByeS4oOUV-49Zzh4R1J6R09zazQ',
            'ext': 'mp4',
            'title': 'Big Buck Bunny.mp4',
            'duration': 45,
        }
    }, {
        # video id is longer than 28 characters
        'url': 'https://drive.google.com/file/d/1ENcQ_jeCuj7y19s66_Ou9dRP4GKGsodiDQ/edit',
        'only_matching': True,
    }]
    _FORMATS_EXT = {
        '5': 'flv',
        '6': 'flv',
        '13': '3gp',
        '17': '3gp',
        '18': 'mp4',
        '22': 'mp4',
        '34': 'flv',
        '35': 'flv',
        '36': '3gp',
        '37': 'mp4',
        '38': 'mp4',
        '43': 'webm',
        '44': 'webm',
        '45': 'webm',
        '46': 'webm',
        '59': 'mp4',
    }

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+src="https?://(?:video\.google\.com/get_player\?.*?docid=|(?:docs|drive)\.google\.com/file/d/)(?P<id>[a-zA-Z0-9_-]{28,})',
            webpage)
        if mobj:
            return 'https://drive.google.com/file/d/%s' % mobj.group('id')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            'http://docs.google.com/file/d/%s' % video_id, video_id, encoding='unicode_escape')

        reason = self._search_regex(r'"reason"\s*,\s*"([^"]+)', webpage, 'reason', default=None)
        if reason:
            raise ExtractorError(reason)

        title = self._search_regex(r'"title"\s*,\s*"([^"]+)', webpage, 'title')
        duration = int_or_none(self._search_regex(
            r'"length_seconds"\s*,\s*"([^"]+)', webpage, 'length seconds', default=None))
        fmt_stream_map = self._search_regex(
            r'"fmt_stream_map"\s*,\s*"([^"]+)', webpage, 'fmt stream map').split(',')
        fmt_list = self._search_regex(r'"fmt_list"\s*,\s*"([^"]+)', webpage, 'fmt_list').split(',')

        formats = []
        for fmt, fmt_stream in zip(fmt_list, fmt_stream_map):
            fmt_id, fmt_url = fmt_stream.split('|')
            resolution = fmt.split('/')[1]
            width, height = resolution.split('x')
            formats.append({
                'url': fmt_url,
                'format_id': fmt_id,
                'resolution': resolution,
                'width': int_or_none(width),
                'height': int_or_none(height),
                'ext': self._FORMATS_EXT[fmt_id],
            })
        self._sort_formats(formats)

        downloadable = True
        # DownloadPage will either be the actual file, a "we can't virus-scan this" page with a confirmation button, or a "you don't have permission" page.
        # The actual file supports range requests, but the confirmation/permission pages don't, so this will download the whole page for either of those.
        downloadPage = self._download_webpage('https://docs.google.com/uc?export=download&id=%s' % video_id, video_id, headers={'Range': 'bytes=0-15'}, encoding='unicode_escape')
        if 'html' in downloadPage:
            confirm = self._search_regex(r'confirm=([^&"]+)', downloadPage, 'confirm', default=None)
            if confirm:
                dlstring = 'https://docs.google.com/uc?export=download&confirm=%s&id=%s' % (confirm, video_id)
            else:
                downloadable = False
        else:
            dlstring = 'https://docs.google.com/uc?export=download&id=%s' % video_id
        if downloadable:
            originalExtension = self._search_regex(r'"([^"]+)",[^,]*,[^,]*$', webpage, 'original extension', default=None)
            originalSize = int_or_none(self._search_regex(r'"([^"]+)"[^"]*\n[^\n]*,[^,]*$', webpage, 'original size', default=None))
            formats.append({
                'url': dlstring,
                'format_id': 'Original',
                'ext': originalExtension,
                'filesize': originalSize,
                'protocol': 'https',
            })

        return {
            'id': video_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': duration,
            'formats': formats,
        }
