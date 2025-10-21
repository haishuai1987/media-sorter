from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

import app.modules.trimemedia.api as fnapi
from app import schemas
from app.log import logger
from app.schemas import MediaType
from app.utils.url import UrlUtils


class TrimeMedia:
    _username: Optional[str] = None
    _password: Optional[str] = None

    _userinfo: Optional[fnapi.User] = None
    _host: Optional[str] = None
    _playhost: Optional[str] = None

    _libraries: dict[str, fnapi.MediaDb] = {}
    _sync_libraries: List[str] = []

    _api: Optional[fnapi.Api] = None

    def __init__(
        self,
        host: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        play_host: Optional[str] = None,
        sync_libraries: Optional[list] = None,
        **kwargs,
    ):
        if not host or not username or not password:
            logger.error("飞牛影视配置不完整！！")
            return
        self._username = username
        self._password = password
        self._host = host
        self._sync_libraries = sync_libraries or []

        if not self.reconnect():
            logger.error(f"请检查服务端地址 {host}")
            return
        if result := self.__create_api(play_host):
            self._playhost = result.api.host
            result.api.close()
        elif play_host:
            logger.warning(f"请检查外网播放地址 {play_host}")
            self._playhost = UrlUtils.standardize_base_url(play_host).rstrip("/")

    @property
    def api(self) -> Optional[fnapi.Api]:
        """
        获得飞牛API
        """
        return self._api

    class _ApiCreateResult:
        api: fnapi.Api
        version: fnapi.Version

    @staticmethod
    def __create_api(host: Optional[str]) -> Optional["TrimeMedia._ApiCreateResult"]:
        """
        创建一个飞牛API

        :param host:  服务端地址
        :return: 如果地址无效、不可访问则返回None
        """

        if not host:
            return None
        api_key = "16CCEB3D-AB42-077D-36A1-F355324E4237"
        host = UrlUtils.standardize_base_url(host).rstrip("/")

        if not host.endswith("/v"):
            # 尝试补上结尾的/v 测试能否正常访问
            res = TrimeMedia._ApiCreateResult()
            res.api = fnapi.Api(host + "/v", api_key)
            if fnver := res.api.sys_version():
                res.version = fnver
                return res
        # 测试用户配置的地址
        res = TrimeMedia._ApiCreateResult()
        res.api = fnapi.Api(host, api_key)
        if fnver := res.api.sys_version():
            res.version = fnver
            return res
        return None

    def close(self):
        self.disconnect()

    def is_configured(self) -> bool:
        return bool(self._host and self._username and self._password)

    def is_authenticated(self) -> bool:
        """
        是否已登录
        """
        return (
            self.is_configured()
            and self._api is not None
            and self._api.token is not None
            and self._userinfo is not None
        )

    def is_inactive(self) -> bool:
        """
        判断是否需要重连
        """
        if not self.is_authenticated():
            return True
        self._userinfo = self._api.user_info()
        return self._userinfo is None

    def reconnect(self):
        """
        重连
        """
        if not self.is_configured():
            return False
        self.disconnect()
        if result := self.__create_api(self._host):
            self._api = result.api
            # 版本号:0.8.53, 服务版本:0.8.23
            logger.debug(
                f"版本号:{result.version.frontend}, 服务版本:{result.version.backend}"
            )
        else:
            return False
        if self._api.login(self._username, self._password) is None:
            return False
        self._userinfo = self._api.user_info()
        if self._userinfo is None:
            return False
        logger.debug(f"{self._username} 成功登录飞牛影视")
        # 刷新媒体库列表
        self.get_librarys()
        return True

    def disconnect(self):
        """
        断开与飞牛的连接
        """
        if self._api:
            self._api.logout()
            self._api.close()
            self._api = None
            self._userinfo = None
            logger.debug(f"{self._username} 已断开飞牛影视")

    def get_librarys(
        self, hidden: Optional[bool] = False
    ) -> List[schemas.MediaServerLibrary]:
        """
        获取媒体服务器所有媒体库列表
        """
        if not self.is_authenticated():
            return []
        if self._userinfo.is_admin == 1:
            mdb_list = self._api.mdb_list() or []
        else:
            mdb_list = self._api.mediadb_list() or []
        self._libraries = {lib.guid: lib for lib in mdb_list}
        libraries = []
        for library in self._libraries.values():
            if hidden and self.__is_library_blocked(library.guid):
                continue
            if library.category == fnapi.Category.MOVIE:
                library_type = MediaType.MOVIE.value
            elif library.category == fnapi.Category.TV:
                library_type = MediaType.TV.value
            elif library.category == fnapi.Category.OTHERS:
                # 忽略这个库
                continue
            else:
                library_type = MediaType.UNKNOWN.value
            libraries.append(
                schemas.MediaServerLibrary(
                    server="trimemedia",
                    id=library.guid,
                    name=library.name,
                    type=library_type,
                    path=library.dir_list,
                    image_list=[
                        f"{self._api.host}{img_path}?w=256"
                        for img_path in library.posters or []
                    ],
                    link=f"{self._playhost or self._api.host}/library/{library.guid}",
                    server_type="trimemedia",
                )
            )
        return libraries

    def get_user_count(self) -> int:
        """
        获取用户数量(非管理员不能调用)
        """
        if not self.is_authenticated():
            return 0
        if not self._userinfo or self._userinfo.is_admin != 1:
            return 0
        return len(self._api.user_list() or [])

    def get_medias_count(self) -> schemas.Statistic:
        """
        获取媒体数量

        :return: MovieCount SeriesCount
        """
        if not self.is_authenticated():
            return schemas.Statistic()
        if (info := self._api.mediadb_sum()) is None:
            return schemas.Statistic()
        return schemas.Statistic(
            movie_count=info.movie,
            tv_count=info.tv,
        )

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """
        用户认证

        :param username: 用户名
        :param password: 密码
        :return: 认证成功返回token，否则返回None
        """
        if not username or not password:
            return None
        if not self.is_configured():
            return None
        if result := self.__create_api(self._host):
            try:
                return result.api.login(username, password)
            finally:
                result.api.logout()
                result.api.close()

    def get_movies(
        self, title: str, year: Optional[str] = None, tmdb_id: Optional[int] = None
    ) -> Optional[List[schemas.MediaServerItem]]:
        """
        根据标题和年份，检查电影是否在飞牛中存在，存在则返回列表

        :param title: 标题
        :param year: 年份，为空则不过滤
        :param tmdb_id: TMDB ID
        :return: 含title、year属性的字典列表
        """
        if not self.is_authenticated():
            return None
        movies = []
        items = self._api.search_list(keywords=title) or []
        for item in items:
            if item.type != fnapi.Type.MOVIE:
                continue
            if (
                (not tmdb_id or tmdb_id == item.tmdb_id)
                and title in [item.title, item.original_title]
                and (not year or (item.release_date and item.release_date[:4] == year))
            ):
                movies.append(self.__build_media_server_item(item))
        return movies

    def __get_series_id_by_name(self, name: str, year: str) -> Optional[str]:
        items = self._api.search_list(keywords=name) or []
        for item in items:
            if item.type != fnapi.Type.TV:
                continue
            # 可惜搜索接口不下发original_title 也不能指定分类、年份
            if name in [item.title, item.original_title]:
                if not year or (item.air_date and item.air_date[:4] == year):
                    return item.guid
        return None

    def get_tv_episodes(
        self,
        item_id: Optional[str] = None,
        title: Optional[str] = None,
        year: Optional[str] = None,
        tmdb_id: Optional[int] = None,
        season: Optional[int] = None,
    ) -> Tuple[Optional[str], Optional[Dict[int, list]]]:
        """
        根据标题和年份和季，返回飞牛中的剧集列表

        :param item_id: 飞牛影视中的guid
        :param title: 标题
        :param year: 年份
        :param tmdb_id: TMDBID
        :param season: 季
        :return: 集号的列表
        """
        if not self.is_authenticated():
            return None, None

        if not item_id:
            item_id = self.__get_series_id_by_name(title, year)
            if item_id is None:
                return None, None

        item_info = self.get_iteminfo(item_id)
        if not item_info:
            return None, {}

        if tmdb_id and item_info.tmdbid:
            if tmdb_id != item_info.tmdbid:
                return None, {}

        seasons = self._api.season_list(item_id)
        if not seasons:
            # 季列表获取失败
            return None, {}

        if season is not None:
            for item in seasons:
                if item.season_number == season:
                    seasons = [item]
                    break
            else:
                # 没有匹配的季
                return None, {}

        season_episodes = {}
        for item in seasons:
            episodes = self._api.episode_list(item.guid)
            for episode in episodes or []:
                if episode.season_number not in season_episodes:
                    season_episodes[episode.season_number] = []
                season_episodes[episode.season_number].append(episode.episode_number)
        return item_id, season_episodes

    def refresh_root_library(self) -> Optional[bool]:
        """
        通知飞牛刷新整个媒体库(非管理员不能调用)
        """
        if not self.is_authenticated():
            return None
        if not self._userinfo or self._userinfo.is_admin != 1:
            logger.error("飞牛仅支持管理员账号刷新媒体库")
            return False

        # 必须调用 否则容易误报 -14 Task duplicate
        self._api.task_running()
        logger.info("刷新所有媒体库")
        return self._api.mdb_scanall()

    def refresh_library_by_items(
        self, items: List[schemas.RefreshMediaItem]
    ) -> Optional[bool]:
        """
        按路径刷新所在的媒体库(非管理员不能调用)

        :param items: 已识别的需要刷新媒体库的媒体信息列表
        """
        if not self.is_authenticated():
            return None
        if not self._userinfo or self._userinfo.is_admin != 1:
            logger.error("飞牛仅支持管理员账号刷新媒体库")
            return False

        libraries = set()
        for item in items:
            lib = self.__match_library_by_path(item.target_path)
            if lib is None:
                # 如果有匹配失败的,刷新整个库
                return self.refresh_root_library()
            # 媒体库去重
            libraries.add(lib.guid)

        # 必须调用 否则容易误报 -14 Task duplicate
        self._api.task_running()
        for lib_guid in libraries:
            # 逐个刷新
            lib = self._libraries[lib_guid]
            logger.info(f"刷新媒体库：{lib.name}")
            if not self._api.mdb_scan(lib):
                # 如果失败，刷新整个库
                return self.refresh_root_library()
        return True

    def __match_library_by_path(self, path: Path) -> Optional[fnapi.MediaDb]:
        def is_subpath(_path: Path, _parent: Path) -> bool:
            """
            判断_path是否是_parent的子目录下
            """
            _path = _path.resolve()
            _parent = _parent.resolve()
            return _path.parts[: len(_parent.parts)] == _parent.parts

        if path is None:
            return None
        for lib in self._libraries.values():
            for d in lib.dir_list or []:
                if is_subpath(path, Path(d)):
                    return lib
        return None

    def get_webhook_message(self, body: any) -> Optional[schemas.WebhookEventInfo]:
        pass

    def get_iteminfo(self, itemid: str) -> Optional[schemas.MediaServerItem]:
        """
        获取单个项目详情
        """
        if not self.is_authenticated():
            return None
        if item := self._api.item(guid=itemid):
            return self.__build_media_server_item(item)
        return None

    @staticmethod
    def __build_media_server_item(item: fnapi.Item):
        if item.air_date and item.type == fnapi.Type.TV:
            year = item.air_date[:4]
        elif item.release_date:
            year = item.release_date[:4]
        else:
            year = None

        user_state = schemas.MediaServerItemUserState()
        if item.watched:
            user_state.played = True
        if item.duration and item.ts is not None:
            user_state.percentage = item.ts / item.duration * 100
            user_state.resume = True
        if item.type is None:
            item_type = None
        else:
            # 将飞牛的媒体类型转为MP能识别的
            item_type = "Series" if item.type == fnapi.Type.TV else item.type.value
        return schemas.MediaServerItem(
            server="trimemedia",
            library=item.ancestor_guid,
            item_id=item.guid,
            item_type=item_type,
            title=item.title,
            original_title=item.original_title,
            year=year,
            tmdbid=item.tmdb_id,
            imdbid=item.imdb_id,
            user_state=user_state,
        )

    @staticmethod
    def __build_play_url(host: str, item: fnapi.Item) -> str:
        """
        拼装播放链接
        """
        if item.type == fnapi.Type.EPISODE:
            return f"{host}/tv/episode/{item.guid}"
        elif item.type == fnapi.Type.SEASON:
            return f"{host}/tv/season/{item.guid}"
        elif item.type == fnapi.Type.MOVIE:
            return f"{host}/movie/{item.guid}"
        elif item.type == fnapi.Type.TV:
            return f"{host}/tv/{item.guid}"
        else:
            # 其它类型走通用页面，由飞牛来判断
            return f"{host}/other/{item.guid}"

    def __build_media_server_play_item(
        self, item: fnapi.Item
    ) -> schemas.MediaServerPlayItem:
        if item.type == fnapi.Type.EPISODE:
            title = item.tv_title
            subtitle = f"S{item.season_number}:{item.episode_number} - {item.title}"
        else:
            title = item.title
            subtitle = "电影" if item.type == fnapi.Type.MOVIE else "视频"
        types = (
            MediaType.MOVIE.value
            if item.type in [fnapi.Type.MOVIE, fnapi.Type.VIDEO]
            else MediaType.TV.value
        )
        return schemas.MediaServerPlayItem(
            id=item.guid,
            title=title,
            subtitle=subtitle,
            type=types,
            image=f"{self._api.host}{item.poster}",
            link=self.__build_play_url(self._playhost or self._api.host, item),
            percent=(
                item.ts / item.duration * 100.0
                if item.duration and item.ts is not None
                else 0
            ),
            server_type="trimemedia",
        )

    def get_items(
        self,
        parent: Union[str, int],
        start_index: Optional[int] = 0,
        limit: Optional[int] = -1,
    ) -> Generator[schemas.MediaServerItem | None | Any, Any, None]:
        """
        获取媒体服务器项目列表，支持分页和不分页逻辑，默认不分页获取所有数据

        :param parent: 媒体库ID，用于标识要获取的媒体库
        :param start_index: 起始索引，用于分页获取数据。默认为 0，即从第一个项目开始获取
        :param limit: 每次请求的最大项目数，用于分页。如果为 None 或 -1，则表示一次性获取所有数据，默认为 -1

        :return: 返回一个生成器对象，用于逐步获取媒体服务器中的项目
        """
        if not self.is_authenticated():
            return None
        if (page_size := limit) is None:
            page_size = -1
        items = (
            self._api.item_list(
                guid=parent,
                page=start_index + 1,
                page_size=page_size,
                types=[fnapi.Type.MOVIE, fnapi.Type.TV, fnapi.Type.DIRECTORY],
            )
            or []
        )
        for item in items:
            if item.type == fnapi.Type.DIRECTORY:
                for items in self.get_items(parent=item.guid):
                    yield items
            elif item.type in [fnapi.Type.MOVIE, fnapi.Type.TV]:
                yield self.__build_media_server_item(item)
        return None

    def get_play_url(self, item_id: str) -> Optional[str]:
        """
        获取媒体的外网播放链接

        :param item_id: 媒体ID
        """
        if not self.is_authenticated():
            return None
        if (item := self._api.item(item_id)) is None:
            return None
        # 根据查询到的信息拼装出播放链接
        return self.__build_play_url(self._playhost or self._api.host, item)

    def get_resume(
        self, num: Optional[int] = 12
    ) -> Optional[List[schemas.MediaServerPlayItem]]:
        """
        获取继续观看列表

        :param num: 列表大小，None不限制数量
        """
        if not self.is_authenticated():
            return None
        ret_resume = []
        for item in self._api.play_list() or []:
            if len(ret_resume) == num:
                break
            if self.__is_library_blocked(item.ancestor_guid):
                continue
            ret_resume.append(self.__build_media_server_play_item(item))
        return ret_resume

    def get_latest(self, num=20) -> Optional[List[schemas.MediaServerPlayItem]]:
        """
        获取最近更新列表
        """
        if not self.is_authenticated():
            return None
        items = (
            self._api.item_list(
                page=1,
                page_size=max(100, num * 5),
                types=[fnapi.Type.MOVIE, fnapi.Type.TV],
            )
            or []
        )
        latest = []
        for item in items:
            if len(latest) == num:
                break
            if self.__is_library_blocked(item.ancestor_guid):
                continue
            latest.append(self.__build_media_server_play_item(item))
        return latest

    def get_latest_backdrops(self, num=20, remote=False) -> Optional[List[str]]:
        """
        获取最近更新的媒体Backdrop图片
        """
        if not self.is_authenticated():
            return None
        items = (
            self._api.item_list(
                page=1,
                page_size=max(100, num * 5),
                types=[fnapi.Type.MOVIE, fnapi.Type.TV],
            )
            or []
        )
        backdrops = []
        for item in items:
            if len(backdrops) == num:
                break
            if self.__is_library_blocked(item.ancestor_guid):
                continue
            if (item_details := self._api.item(item.guid)) is None:
                continue
            if remote:
                img_host = self._playhost or self._api.host
            else:
                img_host = self._api.host
            if item_details.backdrops:
                item_image = item_details.backdrops
            else:
                item_image = (
                    item_details.posters
                    if item_details.posters
                    else item_details.poster
                )
            backdrops.append(f"{img_host}{item_image}")
        return backdrops

    def __is_library_blocked(self, library_guid: str):
        if library := self._libraries.get(library_guid):
            if library.category == fnapi.Category.OTHERS:
                # 忽略这个库
                return True
        return (
            True
            if (
                self._sync_libraries
                and "all" not in self._sync_libraries
                and library_guid not in self._sync_libraries
            )
            else False
        )
