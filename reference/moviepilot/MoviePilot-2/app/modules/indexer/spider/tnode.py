import re
from typing import Tuple, List, Optional

from app.core.cache import cached
from app.core.config import settings
from app.log import logger
from app.utils.http import RequestUtils, AsyncRequestUtils
from app.utils.singleton import SingletonClass
from app.utils.string import StringUtils


class TNodeSpider(metaclass=SingletonClass):
    _size = 100
    _timeout = 15
    _proxy = None
    _baseurl = "%sapi/torrent/advancedSearch"
    _downloadurl = "%sapi/torrent/download/%s"
    _pageurl = "%storrent/info/%s"

    def __init__(self, indexer: dict):
        if indexer:
            self._indexerid = indexer.get('id')
            self._domain = indexer.get('domain')
            self._searchurl = self._baseurl % self._domain
            self._name = indexer.get('name')
            if indexer.get('proxy'):
                self._proxy = settings.PROXY
            self._cookie = indexer.get('cookie')
            self._ua = indexer.get('ua')
            self._timeout = indexer.get('timeout') or 15

    @cached(region="indexer_spider", maxsize=1, ttl=60 * 60 * 24, skip_empty=True)
    def __get_token(self) -> Optional[str]:
        if not self._domain:
            return
        res = RequestUtils(ua=self._ua,
                           cookies=self._cookie,
                           proxies=self._proxy,
                           timeout=self._timeout).get_res(url=self._domain)
        if res and res.status_code == 200:
            csrf_token = re.search(r'<meta name="x-csrf-token" content="(.+?)">', res.text)
            if csrf_token:
                return csrf_token.group(1)
        return None

    @cached(region="indexer_spider", maxsize=1, ttl=60 * 60 * 24, skip_empty=True)
    async def __async_get_token(self) -> Optional[str]:
        if not self._domain:
            return
        res = await AsyncRequestUtils(ua=self._ua,
                                      cookies=self._cookie,
                                      proxies=self._proxy,
                                      timeout=self._timeout).get_res(url=self._domain)
        if res and res.status_code == 200:
            csrf_token = re.search(r'<meta name="x-csrf-token" content="(.+?)">', res.text)
            if csrf_token:
                return csrf_token.group(1)
        return None

    def __get_params(self, keyword: str = None, page: Optional[int] = 0) -> dict:
        """
        获取搜索参数
        """
        search_type = "imdbid" if (keyword and keyword.startswith('tt')) else "title"
        return {
            "page": int(page) + 1,
            "size": self._size,
            "type": search_type,
            "keyword": keyword or "",
            "sorter": "id",
            "order": "desc",
            "tags": [],
            "category": [501, 502, 503, 504],
            "medium": [],
            "videoCoding": [],
            "audioCoding": [],
            "resolution": [],
            "group": []
        }

    def __parse_result(self, results: List[dict]) -> List[dict]:
        """
        解析搜索结果
        """
        torrents = []
        if not results:
            return torrents

        for result in results:
            torrent = {
                'title': result.get('title'),
                'description': result.get('subtitle'),
                'enclosure': self._downloadurl % (self._domain, result.get('id')),
                'pubdate': StringUtils.format_timestamp(result.get('upload_time')),
                'size': result.get('size'),
                'seeders': result.get('seeding'),
                'peers': result.get('leeching'),
                'grabs': result.get('complete'),
                'downloadvolumefactor': result.get('downloadRate'),
                'uploadvolumefactor': result.get('uploadRate'),
                'page_url': self._pageurl % (self._domain, result.get('id')),
                'imdbid': result.get('imdb')
            }
            torrents.append(torrent)

        return torrents

    def search(self, keyword: str, page: Optional[int] = 0) -> Tuple[bool, List[dict]]:
        """
        搜索
        """
        # 获取token
        _token = self.__get_token()
        if not _token:
            logger.warn(f"{self._name} 未获取到token，无法搜索")
            return True, []

        # 获取请求参数
        params = self.__get_params(keyword, page)

        # 发送请求
        res = RequestUtils(
            headers={
                'X-CSRF-TOKEN': _token,
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": f"{self._ua}"
            },
            cookies=self._cookie,
            proxies=self._proxy,
            timeout=self._timeout
        ).post_res(url=self._searchurl, json=params)
        if res and res.status_code == 200:
            results = res.json().get('data', {}).get("torrents") or []
            return False, self.__parse_result(results)
        elif res is not None:
            logger.warn(f"{self._name} 搜索失败，错误码：{res.status_code}")
            return True, []
        else:
            logger.warn(f"{self._name} 搜索失败，无法连接 {self._domain}")
            return True, []
        
    async def async_search(self, keyword: str, page: Optional[int] = 0) -> Tuple[bool, List[dict]]:
        """
        异步搜索
        """
        # 获取token
        _token = await self.__async_get_token()
        if not _token:
            logger.warn(f"{self._name} 未获取到token，无法搜索")
            return True, []

        # 获取请求参数
        params = self.__get_params(keyword, page)

        # 发送请求
        res = await AsyncRequestUtils(
            headers={
                'x-csrf-token': _token,
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": f"{self._ua}"
            },
            cookies=self._cookie,
            proxies=self._proxy,
            timeout=self._timeout
        ).post_res(url=self._searchurl, json=params)
        if res and res.status_code == 200:
            results = res.json().get('data', {}).get("torrents") or []
            return False, self.__parse_result(results)
        elif res is not None:
            logger.warn(f"{self._name} 搜索失败，错误码：{res.status_code}")
            return True, []
        else:
            logger.warn(f"{self._name} 搜索失败，无法连接 {self._domain}")
            return True, []
