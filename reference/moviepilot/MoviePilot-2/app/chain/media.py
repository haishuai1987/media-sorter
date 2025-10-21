import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from typing import Optional, List, Tuple, Union

from app import schemas
from app.chain import ChainBase
from app.chain.storage import StorageChain
from app.core.config import settings
from app.core.context import Context, MediaInfo
from app.core.event import eventmanager, Event
from app.core.meta import MetaBase
from app.core.metainfo import MetaInfo, MetaInfoPath
from app.db.systemconfig_oper import SystemConfigOper
from app.log import logger
from app.schemas import FileItem
from app.schemas.types import EventType, MediaType, ChainEventType, SystemConfigKey
from app.utils.http import RequestUtils
from app.utils.string import StringUtils

recognize_lock = Lock()
scraping_lock = Lock()

current_umask = os.umask(0)
os.umask(current_umask)


class MediaChain(ChainBase):
    """
    媒体信息处理链，单例运行
    """

    @staticmethod
    def _get_scraping_switchs() -> dict:
        """
        获取刮削开关配置
        """
        switchs = SystemConfigOper().get(SystemConfigKey.ScrapingSwitchs) or {}
        # 默认配置
        default_switchs = {
            'movie_nfo': True,  # 电影NFO
            'movie_poster': True,  # 电影海报
            'movie_backdrop': True,  # 电影背景图
            'movie_logo': True,  # 电影Logo
            'movie_disc': True,  # 电影光盘图
            'movie_banner': True,  # 电影横幅图
            'movie_thumb': True,  # 电影缩略图
            'tv_nfo': True,  # 电视剧NFO
            'tv_poster': True,  # 电视剧海报
            'tv_backdrop': True,  # 电视剧背景图
            'tv_banner': True,  # 电视剧横幅图
            'tv_logo': True,  # 电视剧Logo
            'tv_thumb': True,  # 电视剧缩略图
            'season_nfo': True,  # 季NFO
            'season_poster': True,  # 季海报
            'season_banner': True,  # 季横幅图
            'season_thumb': True,  # 季缩略图
            'episode_nfo': True,  # 集NFO
            'episode_thumb': True  # 集缩略图
        }
        # 合并用户配置和默认配置
        for key, default_value in default_switchs.items():
            if key not in switchs:
                switchs[key] = default_value
        return switchs

    @staticmethod
    def set_scraping_switchs(switchs: dict) -> bool:
        """
        设置刮削开关配置
        :param switchs: 开关配置字典
        :return: 是否设置成功
        """
        return SystemConfigOper().set(SystemConfigKey.ScrapingSwitchs, switchs)

    def metadata_nfo(self, meta: MetaBase, mediainfo: MediaInfo,
                     season: Optional[int] = None, episode: Optional[int] = None) -> Optional[str]:
        """
        获取NFO文件内容文本
        :param meta: 元数据
        :param mediainfo: 媒体信息
        :param season: 季号
        :param episode: 集号
        """
        return self.run_module("metadata_nfo", meta=meta, mediainfo=mediainfo, season=season, episode=episode)

    def recognize_by_meta(self, metainfo: MetaBase, episode_group: Optional[str] = None) -> Optional[MediaInfo]:
        """
        根据主副标题识别媒体信息
        """
        title = metainfo.title
        # 识别媒体信息
        mediainfo: MediaInfo = self.recognize_media(meta=metainfo, episode_group=episode_group)
        if not mediainfo:
            # 尝试使用辅助识别，如果有注册响应事件的话
            if eventmanager.check(ChainEventType.NameRecognize):
                logger.info(f'请求辅助识别，标题：{title} ...')
                mediainfo = self.recognize_help(title=title, org_meta=metainfo)
            if not mediainfo:
                logger.warn(f'{title} 未识别到媒体信息')
                return None
        # 识别成功
        logger.info(f'{title} 识别到媒体信息：{mediainfo.type.value} {mediainfo.title_year}')
        # 更新媒体图片
        self.obtain_images(mediainfo=mediainfo)
        # 返回上下文
        return mediainfo

    def recognize_help(self, title: str, org_meta: MetaBase) -> Optional[MediaInfo]:
        """
        请求辅助识别，返回媒体信息
        :param title: 标题
        :param org_meta: 原始元数据
        """
        # 发送请求事件，等待结果
        result: Event = eventmanager.send_event(
            ChainEventType.NameRecognize,
            {
                'title': title,
            }
        )
        if not result:
            return None
        # 获取返回事件数据
        event_data = result.event_data or {}
        logger.info(f'获取到辅助识别结果：{event_data}')
        # 处理数据格式
        title, year, season_number, episode_number = None, None, None, None
        if event_data.get("name"):
            title = str(event_data["name"]).split("/")[0].strip().replace(".", " ")
        if event_data.get("year"):
            year = str(event_data["year"]).split("/")[0].strip()
        if event_data.get("season") and str(event_data["season"]).isdigit():
            season_number = int(event_data["season"])
        if event_data.get("episode") and str(event_data["episode"]).isdigit():
            episode_number = int(event_data["episode"])
        if not title:
            return None
        if title == 'Unknown':
            return None
        if not str(year).isdigit():
            year = None
        # 结果赋值
        if title == org_meta.name and year == org_meta.year:
            logger.info(f'辅助识别与原始识别结果一致，无需重新识别媒体信息')
            return None
        logger.info(f'辅助识别结果与原始识别结果不一致，重新匹配媒体信息 ...')
        org_meta.name = title
        org_meta.year = year
        org_meta.begin_season = season_number
        org_meta.begin_episode = episode_number
        if org_meta.begin_season or org_meta.begin_episode:
            org_meta.type = MediaType.TV
        # 重新识别
        return self.recognize_media(meta=org_meta)

    def recognize_by_path(self, path: str, episode_group: Optional[str] = None) -> Optional[Context]:
        """
        根据文件路径识别媒体信息
        """
        logger.info(f'开始识别媒体信息，文件：{path} ...')
        file_path = Path(path)
        # 元数据
        file_meta = MetaInfoPath(file_path)
        # 识别媒体信息
        mediainfo = self.recognize_media(meta=file_meta, episode_group=episode_group)
        if not mediainfo:
            # 尝试使用辅助识别，如果有注册响应事件的话
            if eventmanager.check(ChainEventType.NameRecognize):
                logger.info(f'请求辅助识别，标题：{file_path.name} ...')
                mediainfo = self.recognize_help(title=path, org_meta=file_meta)
            if not mediainfo:
                logger.warn(f'{path} 未识别到媒体信息')
                return Context(meta_info=file_meta)
        logger.info(f'{path} 识别到媒体信息：{mediainfo.type.value} {mediainfo.title_year}')
        # 更新媒体图片
        self.obtain_images(mediainfo=mediainfo)
        # 返回上下文
        return Context(meta_info=file_meta, media_info=mediainfo)

    def search(self, title: str) -> Tuple[Optional[MetaBase], List[MediaInfo]]:
        """
        搜索媒体/人物信息
        :param title: 搜索内容
        :return: 识别元数据，媒体信息列表
        """
        # 提取要素
        mtype, key_word, season_num, episode_num, year, content = StringUtils.get_keyword(title)
        # 识别
        meta = MetaInfo(content)
        if not meta.name:
            meta.cn_name = content
        # 合并信息
        if mtype:
            meta.type = mtype
        if season_num:
            meta.begin_season = season_num
        if episode_num:
            meta.begin_episode = episode_num
        if year:
            meta.year = year
        # 开始搜索
        logger.info(f"开始搜索媒体信息：{meta.name}")
        medias: Optional[List[MediaInfo]] = self.search_medias(meta=meta)
        if not medias:
            logger.warn(f"{meta.name} 没有找到对应的媒体信息！")
            return meta, []
        logger.info(f"{content} 搜索到 {len(medias)} 条相关媒体信息")
        # 识别的元数据，媒体信息列表
        return meta, medias

    def get_tmdbinfo_by_doubanid(self, doubanid: str, mtype: MediaType = None) -> Optional[dict]:
        """
        根据豆瓣ID获取TMDB信息
        """
        tmdbinfo = None
        doubaninfo = self.douban_info(doubanid=doubanid, mtype=mtype)
        if doubaninfo:
            # 优先使用原标题匹配
            if doubaninfo.get("original_title"):
                meta = MetaInfo(title=doubaninfo.get("title"))
                meta_org = MetaInfo(title=doubaninfo.get("original_title"))
            else:
                meta_org = meta = MetaInfo(title=doubaninfo.get("title"))
            # 年份
            if doubaninfo.get("year"):
                meta.year = doubaninfo.get("year")
            # 处理类型
            if isinstance(doubaninfo.get('media_type'), MediaType):
                meta.type = doubaninfo.get('media_type')
            else:
                meta.type = MediaType.MOVIE if doubaninfo.get("type") == "movie" else MediaType.TV
            # 匹配TMDB信息
            meta_names = list(dict.fromkeys([k for k in [meta_org.name,
                                                         meta.cn_name,
                                                         meta.en_name] if k]))
            tmdbinfo = self._match_tmdb_with_names(
                meta_names=meta_names,
                year=meta.year,
                mtype=mtype or meta.type,
                season=meta.begin_season
            )
            if tmdbinfo:
                # 合季季后返回
                tmdbinfo['season'] = meta.begin_season
        return tmdbinfo

    def get_tmdbinfo_by_bangumiid(self, bangumiid: int) -> Optional[dict]:
        """
        根据BangumiID获取TMDB信息
        """
        bangumiinfo = self.bangumi_info(bangumiid=bangumiid)
        if bangumiinfo:
            # 优先使用原标题匹配
            if bangumiinfo.get("name_cn"):
                meta = MetaInfo(title=bangumiinfo.get("name"))
                meta_cn = MetaInfo(title=bangumiinfo.get("name_cn"))
            else:
                meta_cn = meta = MetaInfo(title=bangumiinfo.get("name"))
            # 年份
            year = self._extract_year_from_bangumi(bangumiinfo)
            # 识别TMDB媒体信息
            meta_names = list(dict.fromkeys([k for k in [meta_cn.name,
                                                         meta.name] if k]))
            tmdbinfo = self._match_tmdb_with_names(
                meta_names=meta_names,
                year=year,
                mtype=MediaType.TV,
                season=meta.begin_season
            )
            return tmdbinfo
        return None

    def get_doubaninfo_by_tmdbid(self, tmdbid: int,
                                 mtype: MediaType = None, season: Optional[int] = None) -> Optional[dict]:
        """
        根据TMDBID获取豆瓣信息
        """
        tmdbinfo = self.tmdb_info(tmdbid=tmdbid, mtype=mtype)
        if tmdbinfo:
            # 名称
            name = tmdbinfo.get("title") or tmdbinfo.get("name")
            # 年份
            year = self._extract_year_from_tmdb(tmdbinfo, season)
            # IMDBID
            imdbid = tmdbinfo.get("external_ids", {}).get("imdb_id")
            return self.match_doubaninfo(
                name=name,
                year=year,
                mtype=mtype,
                imdbid=imdbid
            )
        return None

    def get_doubaninfo_by_bangumiid(self, bangumiid: int) -> Optional[dict]:
        """
        根据BangumiID获取豆瓣信息
        """
        bangumiinfo = self.bangumi_info(bangumiid=bangumiid)
        if bangumiinfo:
            # 优先使用中文标题匹配
            if bangumiinfo.get("name_cn"):
                meta = MetaInfo(title=bangumiinfo.get("name_cn"))
            else:
                meta = MetaInfo(title=bangumiinfo.get("name"))
            # 年份
            year = self._extract_year_from_bangumi(bangumiinfo)
            # 使用名称识别豆瓣媒体信息
            return self.match_doubaninfo(
                name=meta.name,
                year=year,
                mtype=MediaType.TV,
                season=meta.begin_season
            )
        return None

    @staticmethod
    def is_bluray_folder(fileitem: schemas.FileItem) -> bool:
        """
        判断是否为原盘目录
        """
        if not fileitem or fileitem.type != "dir":
            return False
        # 蓝光原盘目录必备的文件或文件夹
        required_files = ['BDMV', 'CERTIFICATE']
        # 检查目录下是否存在所需文件或文件夹
        for item in StorageChain().list_files(fileitem):
            if item.name in required_files:
                return True
        return False

    @eventmanager.register(EventType.MetadataScrape)
    def scrape_metadata_event(self, event: Event):
        """
        监控手动刮削事件
        """
        if not event:
            return
        event_data = event.event_data or {}
        # 媒体根目录
        fileitem: FileItem = event_data.get("fileitem")
        # 媒体文件列表
        file_list: List[str] = event_data.get("file_list", [])
        # 媒体元数据
        meta: MetaBase = event_data.get("meta")
        # 媒体信息
        mediainfo: MediaInfo = event_data.get("mediainfo")
        # 是否覆盖
        overwrite = event_data.get("overwrite", False)
        # 检查媒体根目录
        if not fileitem:
            return

        # 刮削锁
        with scraping_lock:
            # 检查文件项是否存在
            storagechain = StorageChain()
            if not storagechain.get_item(fileitem):
                logger.warn(f"文件项不存在：{fileitem.path}")
                return
            # 检查是否为目录
            if fileitem.type == "file":
                # 单个文件刮削
                self.scrape_metadata(fileitem=fileitem,
                                     mediainfo=mediainfo,
                                     init_folder=False,
                                     parent=storagechain.get_parent_item(fileitem),
                                     overwrite=overwrite)
            else:
                if file_list:
                    # 如果是BDMV原盘目录，只对根目录进行刮削，不处理子目录
                    if self.is_bluray_folder(fileitem):
                        logger.info(f"检测到BDMV原盘目录，只对根目录进行刮削：{fileitem.path}")
                        self.scrape_metadata(fileitem=fileitem,
                                             mediainfo=mediainfo,
                                             init_folder=True,
                                             recursive=False,
                                             overwrite=overwrite)
                    else:
                        # 1. 收集fileitem和file_list中每个文件之间所有子目录
                        all_dirs = set()
                        root_path = Path(fileitem.path)

                        logger.debug(f"开始收集目录，根目录：{root_path}")
                        # 收集根目录
                        all_dirs.add(root_path)

                        # 收集所有目录（包括所有层级）
                        for sub_file in file_list:
                            sub_path = Path(sub_file)
                            # 收集从根目录到文件的所有父目录
                            current_path = sub_path.parent
                            while current_path != root_path and current_path.is_relative_to(root_path):
                                all_dirs.add(current_path)
                                current_path = current_path.parent

                        logger.debug(f"共收集到 {len(all_dirs)} 个目录")

                        # 2. 初始化一遍子目录，但不处理文件
                        for sub_dir in all_dirs:
                            sub_dir_item = storagechain.get_file_item(storage=fileitem.storage, path=sub_dir)
                            if sub_dir_item:
                                logger.info(f"为目录生成海报和nfo：{sub_dir}")
                                # 初始化目录元数据，但不处理文件
                                self.scrape_metadata(fileitem=sub_dir_item,
                                                     mediainfo=mediainfo,
                                                     init_folder=True,
                                                     recursive=False,
                                                     overwrite=overwrite)
                            else:
                                logger.warn(f"无法获取目录项：{sub_dir}")

                        # 3. 刮削每个文件
                        logger.info(f"开始刮削 {len(file_list)} 个文件")
                        for sub_file_path in file_list:
                            sub_file_item = storagechain.get_file_item(storage=fileitem.storage,
                                                                       path=Path(sub_file_path))
                            if sub_file_item:
                                self.scrape_metadata(fileitem=sub_file_item,
                                                     mediainfo=mediainfo,
                                                     init_folder=False,
                                                     overwrite=overwrite)
                            else:
                                logger.warn(f"无法获取文件项：{sub_file_path}")
                else:
                    # 执行全量刮削
                    logger.info(f"开始刮削目录 {fileitem.path} ...")
                    self.scrape_metadata(fileitem=fileitem, meta=meta, init_folder=True,
                                         mediainfo=mediainfo, overwrite=overwrite)

    def scrape_metadata(self, fileitem: schemas.FileItem,
                        meta: MetaBase = None, mediainfo: MediaInfo = None,
                        init_folder: bool = True, parent: schemas.FileItem = None,
                        overwrite: bool = False, recursive: bool = True):
        """
        手动刮削媒体信息
        :param fileitem: 刮削目录或文件
        :param meta: 元数据
        :param mediainfo: 媒体信息
        :param init_folder: 是否刮削根目录
        :param parent: 上级目录
        :param overwrite: 是否覆盖已有文件
        :param recursive: 是否递归处理目录内文件
        """

        storagechain = StorageChain()

        def __list_files(_fileitem: schemas.FileItem):
            """
            列出下级文件
            """
            return storagechain.list_files(fileitem=_fileitem)

        def __save_file(_fileitem: schemas.FileItem, _path: Path, _content: Union[bytes, str]):
            """
            保存或上传文件
            :param _fileitem: 关联的媒体文件项
            :param _path: 元数据文件路径
            :param _content: 文件内容
            """
            if not _fileitem or not _content or not _path:
                return
            # 使用tempfile创建临时文件，自动删除
            with NamedTemporaryFile(delete=True, delete_on_close=False, suffix=_path.suffix) as tmp_file:
                tmp_file_path = Path(tmp_file.name)
                # 写入内容
                if isinstance(_content, bytes):
                    tmp_file.write(_content)
                else:
                    tmp_file.write(_content.encode('utf-8'))
                tmp_file.flush()
                tmp_file.close()  # 关闭文件句柄

                # 刮削文件只需要读写权限
                tmp_file_path.chmod(0o666 & ~current_umask)

                # 上传文件
                item = storagechain.upload_file(fileitem=_fileitem, path=tmp_file_path, new_name=_path.name)
                if item:
                    logger.info(f"已保存文件：{item.path}")
                else:
                    logger.warn(f"文件保存失败：{_path}")

        def __download_and_save_image(_fileitem: schemas.FileItem, _path: Path, _url: str):
            """
            流式下载图片并直接保存到文件（减少内存占用）
            :param _fileitem: 关联的媒体文件项
            :param _path: 图片文件路径
            :param _url: 图片下载URL
            """
            if not _fileitem or not _url or not _path:
                return
            try:
                logger.info(f"正在下载图片：{_url} ...")
                request_utils = RequestUtils(proxies=settings.PROXY, ua=settings.NORMAL_USER_AGENT)
                with request_utils.get_stream(url=_url) as r:
                    if r and r.status_code == 200:
                        # 使用tempfile创建临时文件，自动删除
                        with NamedTemporaryFile(delete=True, delete_on_close=False, suffix=_path.suffix) as tmp_file:
                            tmp_file_path = Path(tmp_file.name)
                            # 流式写入文件
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    tmp_file.write(chunk)
                            tmp_file.flush()
                            tmp_file.close()  # 关闭文件句柄

                            # 刮削的图片只需要读写权限
                            tmp_file_path.chmod(0o666 & ~current_umask)

                            # 上传文件
                            item = storagechain.upload_file(fileitem=_fileitem, path=tmp_file_path,
                                                            new_name=_path.name)
                            if item:
                                logger.info(f"已保存图片：{item.path}")
                            else:
                                logger.warn(f"图片保存失败：{_path}")
                    else:
                        logger.info(f"{_url} 图片下载失败")
            except Exception as err:
                logger.error(f"{_url} 图片下载失败：{str(err)}！")

        if not fileitem:
            return

        # 当前文件路径
        filepath = Path(fileitem.path)
        if fileitem.type == "file" \
                and (not filepath.suffix or filepath.suffix.lower() not in settings.RMT_MEDIAEXT):
            return
        if not meta:
            meta = MetaInfoPath(filepath)
        if not mediainfo:
            mediainfo = self.recognize_by_meta(meta)
        if not mediainfo:
            logger.warn(f"{filepath} 无法识别文件媒体信息！")
            return

        # 获取刮削开关配置
        scraping_switchs = self._get_scraping_switchs()
        logger.info(f"开始刮削：{filepath} ...")
        if mediainfo.type == MediaType.MOVIE:
            # 电影
            if fileitem.type == "file":
                # 检查电影NFO开关
                if scraping_switchs.get('movie_nfo', True):
                    # 是否已存在
                    nfo_path = filepath.with_suffix(".nfo")
                    if overwrite or not storagechain.get_file_item(storage=fileitem.storage, path=nfo_path):
                        # 电影文件
                        movie_nfo = self.metadata_nfo(meta=meta, mediainfo=mediainfo)
                        if movie_nfo:
                            # 保存或上传nfo文件到上级目录
                            if not parent:
                                parent = storagechain.get_parent_item(fileitem)
                            __save_file(_fileitem=parent, _path=nfo_path, _content=movie_nfo)
                        else:
                            logger.warn(f"{filepath.name} nfo文件生成失败！")
                    else:
                        logger.info(f"已存在nfo文件：{nfo_path}")
                else:
                    logger.info("电影NFO刮削已关闭，跳过")
            else:
                # 电影目录
                if recursive:
                    # 处理文件
                    if self.is_bluray_folder(fileitem):
                        # 原盘目录
                        if scraping_switchs.get('movie_nfo', True):
                            nfo_path = filepath / (filepath.name + ".nfo")
                            if overwrite or not storagechain.get_file_item(storage=fileitem.storage, path=nfo_path):
                                # 生成原盘nfo
                                movie_nfo = self.metadata_nfo(meta=meta, mediainfo=mediainfo)
                                if movie_nfo:
                                    # 保存或上传nfo文件到当前目录
                                    __save_file(_fileitem=fileitem, _path=nfo_path, _content=movie_nfo)
                                else:
                                    logger.warn(f"{filepath.name} nfo文件生成失败！")
                            else:
                                logger.info(f"已存在nfo文件：{nfo_path}")
                        else:
                            logger.info("电影NFO刮削已关闭，跳过")
                    else:
                        # 处理目录内的文件
                        files = __list_files(_fileitem=fileitem)
                        for file in files:
                            if file.type == "dir":
                                # 电影不处理子目录
                                continue
                            self.scrape_metadata(fileitem=file,
                                                 mediainfo=mediainfo,
                                                 init_folder=False,
                                                 parent=fileitem,
                                                 overwrite=overwrite)
                # 生成目录内图片文件
                if init_folder:
                    # 图片
                    image_dict = self.metadata_img(mediainfo=mediainfo)
                    if image_dict:
                        for image_name, image_url in image_dict.items():
                            # 根据图片类型检查开关
                            if 'poster' in image_name.lower():
                                should_scrape = scraping_switchs.get('movie_poster', True)
                            elif ('backdrop' in image_name.lower()
                                  or 'fanart' in image_name.lower()
                                  or 'background' in image_name.lower()):
                                should_scrape = scraping_switchs.get('movie_backdrop', True)
                            elif 'logo' in image_name.lower():
                                should_scrape = scraping_switchs.get('movie_logo', True)
                            elif 'disc' in image_name.lower() or 'cdart' in image_name.lower():
                                should_scrape = scraping_switchs.get('movie_disc', True)
                            elif 'banner' in image_name.lower():
                                should_scrape = scraping_switchs.get('movie_banner', True)
                            elif 'thumb' in image_name.lower():
                                should_scrape = scraping_switchs.get('movie_thumb', True)
                            else:
                                should_scrape = True  # 未知类型默认刮削

                            if should_scrape:
                                image_path = filepath.with_name(image_name)
                                if overwrite or not storagechain.get_file_item(storage=fileitem.storage,
                                                                               path=image_path):
                                    # 流式下载图片并直接保存
                                    __download_and_save_image(_fileitem=fileitem, _path=image_path, _url=image_url)
                                else:
                                    logger.info(f"已存在图片文件：{image_path}")
                            else:
                                logger.info(f"电影图片刮削已关闭，跳过：{image_name}")
        else:
            # 电视剧
            if fileitem.type == "file":
                # 重新识别季集
                file_meta = MetaInfoPath(filepath)
                if not file_meta.begin_episode:
                    logger.warn(f"{filepath.name} 无法识别文件集数！")
                    return
                file_mediainfo = self.recognize_media(meta=file_meta, tmdbid=mediainfo.tmdb_id,
                                                      episode_group=mediainfo.episode_group)
                if not file_mediainfo:
                    logger.warn(f"{filepath.name} 无法识别文件媒体信息！")
                    return
                # 检查集NFO开关
                if scraping_switchs.get('episode_nfo', True):
                    # 是否已存在
                    nfo_path = filepath.with_suffix(".nfo")
                    if overwrite or not storagechain.get_file_item(storage=fileitem.storage, path=nfo_path):
                        # 获取集的nfo文件
                        episode_nfo = self.metadata_nfo(meta=file_meta, mediainfo=file_mediainfo,
                                                        season=file_meta.begin_season,
                                                        episode=file_meta.begin_episode)
                        if episode_nfo:
                            # 保存或上传nfo文件到上级目录
                            if not parent:
                                parent = storagechain.get_parent_item(fileitem)
                            __save_file(_fileitem=parent, _path=nfo_path, _content=episode_nfo)
                        else:
                            logger.warn(f"{filepath.name} nfo文件生成失败！")
                    else:
                        logger.info(f"已存在nfo文件：{nfo_path}")
                else:
                    logger.info("集NFO刮削已关闭，跳过")
                # 获取集的图片
                if scraping_switchs.get('episode_thumb', True):
                    image_dict = self.metadata_img(mediainfo=file_mediainfo,
                                                   season=file_meta.begin_season, episode=file_meta.begin_episode)
                    if image_dict:
                        for episode, image_url in image_dict.items():
                            image_path = filepath.with_suffix(Path(image_url).suffix)
                            if overwrite or not storagechain.get_file_item(storage=fileitem.storage, path=image_path):
                                # 流式下载图片并直接保存
                                if not parent:
                                    parent = storagechain.get_parent_item(fileitem)
                                __download_and_save_image(_fileitem=parent, _path=image_path, _url=image_url)
                            else:
                                logger.info(f"已存在图片文件：{image_path}")
                else:
                    logger.info("集缩略图刮削已关闭，跳过")
            else:
                # 当前为电视剧目录，处理目录内的文件
                if recursive:
                    files = __list_files(_fileitem=fileitem)
                    for file in files:
                        if file.type == "dir" and not file.name.lower().startswith("season"):
                            # 电视剧不处理非季子目录
                            continue
                        self.scrape_metadata(fileitem=file,
                                             mediainfo=mediainfo,
                                             parent=fileitem if file.type == "file" else None,
                                             init_folder=True if file.type == "dir" else False,
                                             overwrite=overwrite)
                # 生成目录的nfo和图片
                if init_folder:
                    # 识别文件夹名称
                    season_meta = MetaInfo(filepath.name)
                    # 当前文件夹为Specials或者SPs时，设置为S0
                    if filepath.name in settings.RENAME_FORMAT_S0_NAMES:
                        season_meta.begin_season = 0
                    if season_meta.begin_season is not None:
                        # 检查季NFO开关
                        if scraping_switchs.get('season_nfo', True):
                            # 是否已存在
                            nfo_path = filepath / "season.nfo"
                            if overwrite or not storagechain.get_file_item(storage=fileitem.storage, path=nfo_path):
                                # 当前目录有季号，生成季nfo
                                season_nfo = self.metadata_nfo(meta=meta, mediainfo=mediainfo,
                                                               season=season_meta.begin_season)
                                if season_nfo:
                                    # 写入nfo到根目录
                                    __save_file(_fileitem=fileitem, _path=nfo_path, _content=season_nfo)
                                else:
                                    logger.warn(f"无法生成电视剧季nfo文件：{meta.name}")
                            else:
                                logger.info(f"已存在nfo文件：{nfo_path}")
                        else:
                            logger.info("季NFO刮削已关闭，跳过")
                        # TMDB季poster图片
                        if scraping_switchs.get('season_poster', True):
                            image_dict = self.metadata_img(mediainfo=mediainfo, season=season_meta.begin_season)
                            if image_dict:
                                for image_name, image_url in image_dict.items():
                                    image_path = filepath.with_name(image_name)
                                    if overwrite or not storagechain.get_file_item(storage=fileitem.storage,
                                                                                   path=image_path):
                                        # 流式下载图片并直接保存
                                        if not parent:
                                            parent = storagechain.get_parent_item(fileitem)
                                        __download_and_save_image(_fileitem=parent, _path=image_path, _url=image_url)
                                    else:
                                        logger.info(f"已存在图片文件：{image_path}")
                        else:
                            logger.info("季海报刮削已关闭，跳过")
                        # 额外fanart季图片：poster thumb banner
                        image_dict = self.metadata_img(mediainfo=mediainfo)
                        if image_dict:
                            for image_name, image_url in image_dict.items():
                                if image_name.startswith("season"):
                                    # 根据季图片类型检查开关
                                    if 'poster' in image_name.lower():
                                        should_scrape = scraping_switchs.get('season_poster', True)
                                    elif 'banner' in image_name.lower():
                                        should_scrape = scraping_switchs.get('season_banner', True)
                                    elif 'thumb' in image_name.lower():
                                        should_scrape = scraping_switchs.get('season_thumb', True)
                                    else:
                                        should_scrape = True  # 未知类型默认刮削

                                    if should_scrape:
                                        image_path = filepath.with_name(image_name)
                                        # 只下载当前刮削季的图片
                                        image_season = "00" if "specials" in image_name else image_name[6:8]
                                        if image_season != str(season_meta.begin_season).rjust(2, '0'):
                                            logger.info(
                                                f"当前刮削季为：{season_meta.begin_season}，跳过文件：{image_path}")
                                            continue
                                        if overwrite or not storagechain.get_file_item(storage=fileitem.storage,
                                                                                       path=image_path):
                                            # 流式下载图片并直接保存
                                            if not parent:
                                                parent = storagechain.get_parent_item(fileitem)
                                            __download_and_save_image(_fileitem=parent, _path=image_path,
                                                                      _url=image_url)
                                        else:
                                            logger.info(f"已存在图片文件：{image_path}")
                                    else:
                                        logger.info(f"季图片刮削已关闭，跳过：{image_name}")
                    # 判断当前目录是不是剧集根目录
                    if not season_meta.season:
                        # 检查电视剧NFO开关
                        if scraping_switchs.get('tv_nfo', True):
                            # 是否已存在
                            nfo_path = filepath / "tvshow.nfo"
                            if overwrite or not storagechain.get_file_item(storage=fileitem.storage, path=nfo_path):
                                # 当前目录有名称，生成tvshow nfo 和 tv图片
                                tv_nfo = self.metadata_nfo(meta=meta, mediainfo=mediainfo)
                                if tv_nfo:
                                    # 写入tvshow nfo到根目录
                                    __save_file(_fileitem=fileitem, _path=nfo_path, _content=tv_nfo)
                                else:
                                    logger.warn(f"无法生成电视剧nfo文件：{meta.name}")
                            else:
                                logger.info(f"已存在nfo文件：{nfo_path}")
                        else:
                            logger.info("电视剧NFO刮削已关闭，跳过")
                        # 生成目录图片
                        image_dict = self.metadata_img(mediainfo=mediainfo)
                        if image_dict:
                            for image_name, image_url in image_dict.items():
                                # 不下载季图片
                                if image_name.startswith("season"):
                                    continue
                                # 根据电视剧图片类型检查开关
                                if 'poster' in image_name.lower():
                                    should_scrape = scraping_switchs.get('tv_poster', True)
                                elif ('backdrop' in image_name.lower()
                                      or 'fanart' in image_name.lower()
                                      or 'background' in image_name.lower()):
                                    should_scrape = scraping_switchs.get('tv_backdrop', True)
                                elif 'banner' in image_name.lower():
                                    should_scrape = scraping_switchs.get('tv_banner', True)
                                elif 'logo' in image_name.lower():
                                    should_scrape = scraping_switchs.get('tv_logo', True)
                                elif 'thumb' in image_name.lower():
                                    should_scrape = scraping_switchs.get('tv_thumb', True)
                                else:
                                    should_scrape = True  # 未知类型默认刮削

                                if should_scrape:
                                    image_path = filepath / image_name
                                    if overwrite or not storagechain.get_file_item(storage=fileitem.storage,
                                                                                   path=image_path):
                                        # 流式下载图片并直接保存
                                        __download_and_save_image(_fileitem=fileitem, _path=image_path, _url=image_url)
                                    else:
                                        logger.info(f"已存在图片文件：{image_path}")
                                else:
                                    logger.info(f"电视剧图片刮削已关闭，跳过：{image_name}")
        logger.info(f"{filepath.name} 刮削完成")

    async def async_recognize_by_meta(self, metainfo: MetaBase,
                                      episode_group: Optional[str] = None) -> Optional[MediaInfo]:
        """
        根据主副标题识别媒体信息（异步版本）
        """
        title = metainfo.title
        # 识别媒体信息
        mediainfo: MediaInfo = await self.async_recognize_media(meta=metainfo, episode_group=episode_group)
        if not mediainfo:
            # 尝试使用辅助识别，如果有注册响应事件的话
            if eventmanager.check(ChainEventType.NameRecognize):
                logger.info(f'请求辅助识别，标题：{title} ...')
                mediainfo = await self.async_recognize_help(title=title, org_meta=metainfo)
            if not mediainfo:
                logger.warn(f'{title} 未识别到媒体信息')
                return None
        # 识别成功
        logger.info(f'{title} 识别到媒体信息：{mediainfo.type.value} {mediainfo.title_year}')
        # 更新媒体图片
        await self.async_obtain_images(mediainfo=mediainfo)
        # 返回上下文
        return mediainfo

    async def async_recognize_help(self, title: str, org_meta: MetaBase) -> Optional[MediaInfo]:
        """
        请求辅助识别，返回媒体信息（异步版本）
        :param title: 标题
        :param org_meta: 原始元数据
        """
        # 发送请求事件，等待结果
        result: Event = await eventmanager.async_send_event(
            ChainEventType.NameRecognize,
            {
                'title': title,
            }
        )
        if not result:
            return None
        # 获取返回事件数据
        event_data = result.event_data or {}
        logger.info(f'获取到辅助识别结果：{event_data}')
        # 处理数据格式
        title, year, season_number, episode_number = None, None, None, None
        if event_data.get("name"):
            title = str(event_data["name"]).split("/")[0].strip().replace(".", " ")
        if event_data.get("year"):
            year = str(event_data["year"]).split("/")[0].strip()
        if event_data.get("season") and str(event_data["season"]).isdigit():
            season_number = int(event_data["season"])
        if event_data.get("episode") and str(event_data["episode"]).isdigit():
            episode_number = int(event_data["episode"])
        if not title:
            return None
        if title == 'Unknown':
            return None
        if not str(year).isdigit():
            year = None
        # 结果赋值
        if title == org_meta.name and year == org_meta.year:
            logger.info(f'辅助识别与原始识别结果一致，无需重新识别媒体信息')
            return None
        logger.info(f'辅助识别结果与原始识别结果不一致，重新匹配媒体信息 ...')
        org_meta.name = title
        org_meta.year = year
        org_meta.begin_season = season_number
        org_meta.begin_episode = episode_number
        if org_meta.begin_season or org_meta.begin_episode:
            org_meta.type = MediaType.TV
        # 重新识别
        return await self.async_recognize_media(meta=org_meta)

    async def async_recognize_by_path(self, path: str, episode_group: Optional[str] = None) -> Optional[Context]:
        """
        根据文件路径识别媒体信息（异步版本）
        """
        logger.info(f'开始识别媒体信息，文件：{path} ...')
        file_path = Path(path)
        # 元数据
        file_meta = MetaInfoPath(file_path)
        # 识别媒体信息
        mediainfo = await self.async_recognize_media(meta=file_meta, episode_group=episode_group)
        if not mediainfo:
            # 尝试使用辅助识别，如果有注册响应事件的话
            if eventmanager.check(ChainEventType.NameRecognize):
                logger.info(f'请求辅助识别，标题：{file_path.name} ...')
                mediainfo = await self.async_recognize_help(title=path, org_meta=file_meta)
            if not mediainfo:
                logger.warn(f'{path} 未识别到媒体信息')
                return Context(meta_info=file_meta)
        logger.info(f'{path} 识别到媒体信息：{mediainfo.type.value} {mediainfo.title_year}')
        # 更新媒体图片
        await self.async_obtain_images(mediainfo=mediainfo)
        # 返回上下文
        return Context(meta_info=file_meta, media_info=mediainfo)

    async def async_search(self, title: str) -> Tuple[Optional[MetaBase], List[MediaInfo]]:
        """
        搜索媒体/人物信息（异步版本）
        :param title: 搜索内容
        :return: 识别元数据，媒体信息列表
        """
        # 提取要素
        mtype, key_word, season_num, episode_num, year, content = StringUtils.get_keyword(title)
        # 识别
        meta = MetaInfo(content)
        if not meta.name:
            meta.cn_name = content
        # 合并信息
        if mtype:
            meta.type = mtype
        if season_num:
            meta.begin_season = season_num
        if episode_num:
            meta.begin_episode = episode_num
        if year:
            meta.year = year
        # 开始搜索
        logger.info(f"开始搜索媒体信息：{meta.name}")
        medias: Optional[List[MediaInfo]] = await self.async_search_medias(meta=meta)
        if not medias:
            logger.warn(f"{meta.name} 没有找到对应的媒体信息！")
            return meta, []
        logger.info(f"{content} 搜索到 {len(medias)} 条相关媒体信息")
        # 识别的元数据，媒体信息列表
        return meta, medias

    @staticmethod
    def _extract_year_from_bangumi(bangumiinfo: dict) -> Optional[str]:
        """
        从Bangumi信息中提取年份
        """
        release_date = bangumiinfo.get("date") or bangumiinfo.get("air_date")
        if release_date:
            return release_date[:4]
        return None

    @staticmethod
    def _extract_year_from_tmdb(tmdbinfo: dict, season: Optional[int] = None) -> Optional[str]:
        """
        从TMDB信息中提取年份
        """
        year = None
        if tmdbinfo.get('release_date'):
            year = tmdbinfo['release_date'][:4]
        elif tmdbinfo.get('seasons') and season:
            for seainfo in tmdbinfo['seasons']:
                season_number = seainfo.get("season_number")
                if not season_number:
                    continue
                air_date = seainfo.get("air_date")
                if air_date and season_number == season:
                    year = air_date[:4]
                    break
        return year

    def _match_tmdb_with_names(self, meta_names: list, year: Optional[str],
                               mtype: MediaType, season: Optional[int] = None) -> Optional[dict]:
        """
        使用名称列表匹配TMDB信息
        """
        for name in meta_names:
            tmdbinfo = self.match_tmdbinfo(
                name=name,
                year=year,
                mtype=mtype,
                season=season
            )
            if tmdbinfo:
                return tmdbinfo
        return None

    async def _async_match_tmdb_with_names(self, meta_names: list, year: Optional[str],
                                           mtype: MediaType, season: Optional[int] = None) -> Optional[dict]:
        """
        使用名称列表匹配TMDB信息（异步版本）
        """
        for name in meta_names:
            tmdbinfo = await self.async_match_tmdbinfo(
                name=name,
                year=year,
                mtype=mtype,
                season=season
            )
            if tmdbinfo:
                return tmdbinfo
        return None

    async def async_get_tmdbinfo_by_doubanid(self, doubanid: str, mtype: MediaType = None) -> Optional[dict]:
        """
        根据豆瓣ID获取TMDB信息（异步版本）
        """
        tmdbinfo = None
        doubaninfo = await self.async_douban_info(doubanid=doubanid, mtype=mtype)
        if doubaninfo:
            # 优先使用原标题匹配
            if doubaninfo.get("original_title"):
                meta = MetaInfo(title=doubaninfo.get("title"))
                meta_org = MetaInfo(title=doubaninfo.get("original_title"))
            else:
                meta_org = meta = MetaInfo(title=doubaninfo.get("title"))
            # 年份
            if doubaninfo.get("year"):
                meta.year = doubaninfo.get("year")
            # 处理类型
            if isinstance(doubaninfo.get('media_type'), MediaType):
                meta.type = doubaninfo.get('media_type')
            else:
                meta.type = MediaType.MOVIE if doubaninfo.get("type") == "movie" else MediaType.TV
            # 匹配TMDB信息
            meta_names = list(dict.fromkeys([k for k in [meta_org.name,
                                                         meta.cn_name,
                                                         meta.en_name] if k]))
            tmdbinfo = await self._async_match_tmdb_with_names(
                meta_names=meta_names,
                year=meta.year,
                mtype=mtype or meta.type,
                season=meta.begin_season
            )
            if tmdbinfo:
                # 合季季后返回
                tmdbinfo['season'] = meta.begin_season
        return tmdbinfo

    async def async_get_tmdbinfo_by_bangumiid(self, bangumiid: int) -> Optional[dict]:
        """
        根据BangumiID获取TMDB信息（异步版本）
        """
        bangumiinfo = await self.async_bangumi_info(bangumiid=bangumiid)
        if bangumiinfo:
            # 优先使用原标题匹配
            if bangumiinfo.get("name_cn"):
                meta = MetaInfo(title=bangumiinfo.get("name"))
                meta_cn = MetaInfo(title=bangumiinfo.get("name_cn"))
            else:
                meta_cn = meta = MetaInfo(title=bangumiinfo.get("name"))
            # 年份
            year = self._extract_year_from_bangumi(bangumiinfo)
            # 识别TMDB媒体信息
            meta_names = list(dict.fromkeys([k for k in [meta_cn.name,
                                                         meta.name] if k]))
            tmdbinfo = await self._async_match_tmdb_with_names(
                meta_names=meta_names,
                year=year,
                mtype=MediaType.TV,
                season=meta.begin_season
            )
            return tmdbinfo
        return None

    async def async_get_doubaninfo_by_tmdbid(self, tmdbid: int, mtype: MediaType = None,
                                             season: Optional[int] = None) -> Optional[dict]:
        """
        根据TMDBID获取豆瓣信息（异步版本）
        """
        tmdbinfo = await self.async_tmdb_info(tmdbid=tmdbid, mtype=mtype)
        if tmdbinfo:
            # 名称
            name = tmdbinfo.get("title") or tmdbinfo.get("name")
            # 年份
            year = self._extract_year_from_tmdb(tmdbinfo, season)
            # IMDBID
            imdbid = tmdbinfo.get("external_ids", {}).get("imdb_id")
            return await self.async_match_doubaninfo(
                name=name,
                year=year,
                mtype=mtype,
                imdbid=imdbid
            )
        return None

    async def async_get_doubaninfo_by_bangumiid(self, bangumiid: int) -> Optional[dict]:
        """
        根据BangumiID获取豆瓣信息（异步版本）
        """
        bangumiinfo = await self.async_bangumi_info(bangumiid=bangumiid)
        if bangumiinfo:
            # 优先使用中文标题匹配
            if bangumiinfo.get("name_cn"):
                meta = MetaInfo(title=bangumiinfo.get("name_cn"))
            else:
                meta = MetaInfo(title=bangumiinfo.get("name"))
            # 年份
            year = self._extract_year_from_bangumi(bangumiinfo)
            # 使用名称识别豆瓣媒体信息
            return await self.async_match_doubaninfo(
                name=meta.name,
                year=year,
                mtype=MediaType.TV,
                season=meta.begin_season
            )
        return None
