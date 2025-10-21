from pathlib import Path
from typing import Set, Tuple, Optional, Union, List, Dict

from qbittorrentapi import TorrentFilesList
from torrentool.torrent import Torrent

from app import schemas
from app.core.cache import FileCache
from app.core.config import settings
from app.core.event import eventmanager, Event
from app.core.metainfo import MetaInfo
from app.log import logger
from app.modules import _ModuleBase, _DownloaderBase
from app.modules.qbittorrent.qbittorrent import Qbittorrent
from app.schemas import TransferTorrent, DownloadingTorrent
from app.schemas.types import TorrentStatus, ModuleType, DownloaderType, SystemConfigKey, EventType
from app.utils.string import StringUtils


class QbittorrentModule(_ModuleBase, _DownloaderBase[Qbittorrent]):

    def init_module(self) -> None:
        """
        初始化模块
        """
        super().init_service(service_name=Qbittorrent.__name__.lower(),
                             service_type=Qbittorrent)

    @eventmanager.register(EventType.ConfigChanged)
    def handle_config_changed(self, event: Event):
        """
        处理配置变更事件
        :param event: 事件对象
        """
        if not event:
            return
        event_data: schemas.ConfigChangeEventData = event.event_data
        if event_data.key not in [SystemConfigKey.Downloaders.value]:
            return
        logger.info("配置变更，重新加载Qbittorrent模块...")
        self.init_module()

    @staticmethod
    def get_name() -> str:
        return "Qbittorrent"

    @staticmethod
    def get_type() -> ModuleType:
        """
        获取模块类型
        """
        return ModuleType.Downloader

    @staticmethod
    def get_subtype() -> DownloaderType:
        """
        获取模块子类型
        """
        return DownloaderType.Qbittorrent

    @staticmethod
    def get_priority() -> int:
        """
        获取模块优先级，数字越小优先级越高，只有同一接口下优先级才生效
        """
        return 1

    def stop(self):
        pass

    def test(self) -> Optional[Tuple[bool, str]]:
        """
        测试模块连接性
        """
        if not self.get_instances():
            return None
        for name, server in self.get_instances().items():
            if server.is_inactive():
                server.reconnect()
            if not server.transfer_info():
                return False, f"无法连接Qbittorrent下载器：{name}"
        return True, ""

    def init_setting(self) -> Tuple[str, Union[str, bool]]:
        pass

    def scheduler_job(self) -> None:
        """
        定时任务，每10分钟调用一次
        """
        for name, server in self.get_instances().items():
            if server.is_inactive():
                logger.info(f"Qbittorrent下载器 {name} 连接断开，尝试重连 ...")
                server.reconnect()

    def download(self, content: Union[Path, str, bytes], download_dir: Path, cookie: str,
                 episodes: Set[int] = None, category: Optional[str] = None, label: Optional[str] = None,
                 downloader: Optional[str] = None) -> Optional[Tuple[Optional[str], Optional[str], Optional[str], str]]:
        """
        根据种子文件，选择并添加下载任务
        :param content:  种子文件地址或者磁力链接或者种子内容
        :param download_dir:  下载目录
        :param cookie:  cookie
        :param episodes:  需要下载的集数
        :param category:  分类
        :param label:  标签
        :param downloader:  下载器
        :return: 下载器名称、种子Hash、种子文件布局、错误原因
        """

        def __get_torrent_info() -> Tuple[Optional[Torrent], Optional[bytes]]:
            """
            获取种子名称
            """
            torrent_info, torrent_content = None, None
            try:
                if isinstance(content, Path):
                    if content.exists():
                        torrent_content = content.read_bytes()
                    else:
                        # 读取缓存的种子文件
                        torrent_content = FileCache().get(content.as_posix(), region="torrents")
                else:
                    torrent_content = content

                if torrent_content:
                    # 检查是否为磁力链接
                    if StringUtils.is_magnet_link(torrent_content):
                        return None, torrent_content
                    else:
                        torrent_info = Torrent.from_string(torrent_content)

                return torrent_info, torrent_content
            except Exception as e:
                logger.error(f"获取种子名称失败：{e}")
                return None, None

        if not content:
            return None, None, None, "下载内容为空"

        # 读取种子的名称
        torrent, content = __get_torrent_info()
        # 检查是否为磁力链接
        is_magnet = isinstance(content, str) and content.startswith("magnet:") or isinstance(content,
                                                                                             bytes) and content.startswith(
            b"magnet:")
        if not torrent and not is_magnet:
            return None, None, None, f"添加种子任务失败：无法读取种子文件"

        # 获取下载器
        server: Qbittorrent = self.get_instance(downloader)
        if not server:
            return None

        # 生成随机Tag
        tag = StringUtils.generate_random_str(10)
        if label:
            tags = label.split(',') + [tag]
        elif settings.TORRENT_TAG:
            tags = [tag, settings.TORRENT_TAG]
        else:
            tags = [tag]
        # 如果要选择文件则先暂停
        is_paused = True if episodes else False
        # 添加任务
        state = server.add_torrent(
            content=content,
            download_dir=str(download_dir),
            is_paused=is_paused,
            tag=tags,
            cookie=cookie,
            category=category,
            ignore_category_check=False
        )

        # 获取种子内容布局: `Original: 原始, Subfolder: 创建子文件夹, NoSubfolder: 不创建子文件夹`
        torrent_layout = server.get_content_layout()

        if not state:
            # 查询所有下载器的种子
            torrents, error = server.get_torrents()
            if error:
                return None, None, None, "无法连接qbittorrent下载器"
            if torrents:
                try:
                    for torrent in torrents:
                        # 名称与大小相等则认为是同一个种子
                        if torrent.get("name") == torrent.name \
                                and torrent.get("total_size") == torrent.total_size:
                            torrent_hash = torrent.get("hash")
                            torrent_tags = [str(tag).strip() for tag in torrent.get("tags").split(',')]
                            logger.warn(f"下载器中已存在该种子任务：{torrent_hash} - {torrent.get('name')}")
                            # 给种子打上标签
                            if "已整理" in torrent_tags:
                                server.remove_torrents_tag(ids=torrent_hash, tag=['已整理'])
                            if settings.TORRENT_TAG and settings.TORRENT_TAG not in torrent_tags:
                                logger.info(f"给种子 {torrent_hash} 打上标签：{settings.TORRENT_TAG}")
                                server.set_torrents_tag(ids=torrent_hash, tags=[settings.TORRENT_TAG])
                            return downloader or self.get_default_config_name(), torrent_hash, torrent_layout, f"下载任务已存在"
                finally:
                    torrents.clear()
                    del torrents
            return None, None, None, f"添加种子任务失败：{content}"
        else:
            # 获取种子Hash
            torrent_hash = server.get_torrent_id_by_tag(tags=tag)
            if not torrent_hash:
                return None, None, None, f"下载任务添加成功，但获取Qbittorrent任务信息失败：{content}"
            else:
                if is_paused:
                    # 种子文件
                    torrent_files = server.get_files(torrent_hash)
                    if not torrent_files:
                        return downloader or self.get_default_config_name(), torrent_hash, torrent_layout, "获取种子文件失败，下载任务可能在暂停状态"

                    # 不需要的文件ID
                    file_ids = []
                    # 需要的集清单
                    sucess_epidised = []
                    try:
                        for torrent_file in torrent_files:
                            file_id = torrent_file.get("id")
                            file_name = torrent_file.get("name")
                            meta_info = MetaInfo(file_name)
                            if not meta_info.episode_list \
                                    or not set(meta_info.episode_list).issubset(episodes):
                                file_ids.append(file_id)
                            else:
                                sucess_epidised = list(set(sucess_epidised).union(set(meta_info.episode_list)))
                    finally:
                        torrent_files.clear()
                        del torrent_files
                    if sucess_epidised and file_ids:
                        # 选择文件
                        server.set_files(torrent_hash=torrent_hash, file_ids=file_ids, priority=0)
                    # 开始任务
                    if server.is_force_resume():
                        # 强制继续
                        server.torrents_set_force_start(torrent_hash)
                    else:
                        server.start_torrents(torrent_hash)
                    return downloader or self.get_default_config_name(), torrent_hash, torrent_layout, f"添加下载成功，已选择集数：{sucess_epidised}"
                else:
                    if server.is_force_resume():
                        server.torrents_set_force_start(torrent_hash)
                    return downloader or self.get_default_config_name(), torrent_hash, torrent_layout, "添加下载成功"

    def list_torrents(self, status: TorrentStatus = None,
                      hashs: Union[list, str] = None,
                      downloader: Optional[str] = None
                      ) -> Optional[List[Union[TransferTorrent, DownloadingTorrent]]]:
        """
        获取下载器种子列表
        :param status:  种子状态
        :param hashs:  种子Hash
        :param downloader:  下载器
        :return: 下载器中符合状态的种子列表
        """
        # 获取下载器
        if downloader:
            server: Qbittorrent = self.get_instance(downloader)
            if not server:
                return None
            servers = {downloader: server}
        else:
            servers: Dict[str, Qbittorrent] = self.get_instances()
        ret_torrents = []
        if hashs:
            # 按Hash获取
            for name, server in servers.items():
                torrents, _ = server.get_torrents(ids=hashs, tags=settings.TORRENT_TAG) or []
                try:
                    for torrent in torrents:
                        content_path = torrent.get("content_path")
                        if content_path:
                            torrent_path = Path(content_path)
                        else:
                            torrent_path = Path(torrent.get('save_path')) / torrent.get('name')
                        ret_torrents.append(TransferTorrent(
                            downloader=name,
                            title=torrent.get('name'),
                            path=torrent_path,
                            hash=torrent.get('hash'),
                            size=torrent.get('total_size'),
                            tags=torrent.get('tags'),
                            progress=torrent.get('progress') * 100,
                            state="paused" if torrent.get('state') in ("paused", "pausedDL") else "downloading",
                        ))
                finally:
                    torrents.clear()
                    del torrents
        elif status == TorrentStatus.TRANSFER:
            # 获取已完成且未整理的
            for name, server in servers.items():
                torrents = server.get_completed_torrents(tags=settings.TORRENT_TAG) or []
                try:
                    for torrent in torrents:
                        tags = torrent.get("tags") or []
                        if "已整理" in tags:
                            continue
                        # 内容路径
                        content_path = torrent.get("content_path")
                        if content_path:
                            torrent_path = Path(content_path)
                        else:
                            torrent_path = torrent.get('save_path') / torrent.get('name')
                        ret_torrents.append(TransferTorrent(
                            downloader=name,
                            title=torrent.get('name'),
                            path=torrent_path,
                            hash=torrent.get('hash'),
                            tags=torrent.get('tags')
                        ))
                finally:
                    torrents.clear()
                    del torrents
        elif status == TorrentStatus.DOWNLOADING:
            # 获取正在下载的任务
            for name, server in servers.items():
                torrents = server.get_downloading_torrents(tags=settings.TORRENT_TAG) or []
                try:
                    for torrent in torrents:
                        meta = MetaInfo(torrent.get('name'))
                        ret_torrents.append(DownloadingTorrent(
                            downloader=name,
                            hash=torrent.get('hash'),
                            title=torrent.get('name'),
                            name=meta.name,
                            year=meta.year,
                            season_episode=meta.season_episode,
                            progress=torrent.get('progress') * 100,
                            size=torrent.get('total_size'),
                            state="paused" if torrent.get('state') in ("paused", "pausedDL") else "downloading",
                            dlspeed=StringUtils.str_filesize(torrent.get('dlspeed')),
                            upspeed=StringUtils.str_filesize(torrent.get('upspeed')),
                            left_time=StringUtils.str_secends(
                                (torrent.get('total_size') - torrent.get('completed')) / torrent.get(
                                    'dlspeed')) if torrent.get(
                                'dlspeed') > 0 else ''
                        ))
                finally:
                    torrents.clear()
                    del torrents
        else:
            return None
        return ret_torrents  # noqa

    def transfer_completed(self, hashs: str, downloader: Optional[str] = None) -> None:
        """
        转移完成后的处理
        :param hashs:  种子Hash
        :param downloader:  下载器
        """
        server: Qbittorrent = self.get_instance(downloader)
        if not server:
            return None
        server.set_torrents_tag(ids=hashs, tags=['已整理'])
        return None

    def remove_torrents(self, hashs: Union[str, list], delete_file: Optional[bool] = True,
                        downloader: Optional[str] = None) -> Optional[bool]:
        """
        删除下载器种子
        :param hashs:  种子Hash
        :param delete_file:  是否删除文件
        :param downloader:  下载器
        :return: bool
        """
        server: Qbittorrent = self.get_instance(downloader)
        if not server:
            return None
        return server.delete_torrents(delete_file=delete_file, ids=hashs)

    def start_torrents(self, hashs: Union[list, str],
                       downloader: Optional[str] = None) -> Optional[bool]:
        """
        开始下载
        :param hashs:  种子Hash
        :param downloader:  下载器
        :return: bool
        """
        server: Qbittorrent = self.get_instance(downloader)
        if not server:
            return None
        return server.start_torrents(ids=hashs)

    def stop_torrents(self, hashs: Union[list, str], downloader: Optional[str] = None) -> Optional[bool]:
        """
        停止下载
        :param hashs:  种子Hash
        :param downloader:  下载器
        :return: bool
        """
        server: Qbittorrent = self.get_instance(downloader)
        if not server:
            return None
        return server.stop_torrents(ids=hashs)

    def torrent_files(self, tid: str, downloader: Optional[str] = None) -> Optional[TorrentFilesList]:
        """
        获取种子文件列表
        """
        server: Qbittorrent = self.get_instance(downloader)
        if not server:
            return None
        return server.get_files(tid=tid)

    def downloader_info(self, downloader: Optional[str] = None) -> Optional[List[schemas.DownloaderInfo]]:
        """
        下载器信息
        """
        if downloader:
            server: Qbittorrent = self.get_instance(downloader)
            if not server:
                return None
            servers = [server]
        else:
            servers = self.get_instances().values()
        # 调用Qbittorrent API查询实时信息
        ret_info = []
        for server in servers:
            info = server.transfer_info()
            if not info:
                continue
            ret_info.append(schemas.DownloaderInfo(
                download_speed=info.get("dl_info_speed"),
                upload_speed=info.get("up_info_speed"),
                download_size=info.get("dl_info_data"),
                upload_size=info.get("up_info_data")
            ))
        return ret_info
