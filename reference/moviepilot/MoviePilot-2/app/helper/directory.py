import re
from pathlib import Path
from typing import List, Optional

from app import schemas
from app.core.context import MediaInfo
from app.db.systemconfig_oper import SystemConfigOper
from app.log import logger
from app.schemas.types import SystemConfigKey
from app.utils.system import SystemUtils

JINJA2_VAR_PATTERN = re.compile(r"\{\{.*?\}\}", re.DOTALL)


class DirectoryHelper:
    """
    下载目录/媒体库目录帮助类
    """

    @staticmethod
    def get_dirs() -> List[schemas.TransferDirectoryConf]:
        """
        获取所有下载目录
        """
        dir_confs: List[dict] = SystemConfigOper().get(SystemConfigKey.Directories)
        if not dir_confs:
            return []
        return [schemas.TransferDirectoryConf(**d) for d in dir_confs]

    def get_download_dirs(self) -> List[schemas.TransferDirectoryConf]:
        """
        获取所有下载目录
        """
        return sorted([d for d in self.get_dirs() if d.download_path], key=lambda x: x.priority)

    def get_local_download_dirs(self) -> List[schemas.TransferDirectoryConf]:
        """
        获取所有本地的可下载目录
        """
        return [d for d in self.get_download_dirs() if d.storage == "local"]

    def get_library_dirs(self) -> List[schemas.TransferDirectoryConf]:
        """
        获取所有媒体库目录
        """
        return sorted([d for d in self.get_dirs() if d.library_path], key=lambda x: x.priority)

    def get_local_library_dirs(self) -> List[schemas.TransferDirectoryConf]:
        """
        获取所有本地的媒体库目录
        """
        return [d for d in self.get_library_dirs() if d.library_storage == "local"]

    def get_dir(self, media: MediaInfo, include_unsorted: Optional[bool] = False,
                storage: Optional[str] = None, src_path: Path = None,
                target_storage: Optional[str] = None, dest_path: Path = None
                ) -> Optional[schemas.TransferDirectoryConf]:
        """
        根据媒体信息获取下载目录、媒体库目录配置
        :param media: 媒体信息
        :param include_unsorted: 包含不整理目录
        :param storage: 源存储类型
        :param target_storage: 目标存储类型
        :param src_path: 源目录，有值时直接匹配
        :param dest_path: 目标目录，有值时直接匹配
        """
        # 处理类型
        if not media:
            return None
        # 电影/电视剧
        media_type = media.type.value
        dirs = self.get_dirs()

        # 如果存在源目录，并源目录为任一下载目录的子目录时，则进行源目录匹配，否则，允许源目录按同盘优先的逻辑匹配
        matching_dirs = [d for d in dirs if src_path.is_relative_to(d.download_path)] if src_path else []
        # 根据是否有匹配的源目录，决定要考虑的目录集合
        dirs_to_consider = matching_dirs if matching_dirs else dirs

        # 已匹配的目录
        matched_dirs: List[schemas.TransferDirectoryConf] = []
        # 按照配置顺序查找
        for d in dirs_to_consider:
            # 没有启用整理的目录
            if not d.monitor_type and not include_unsorted:
                continue
            # 源存储类型不匹配
            if storage and d.storage != storage:
                continue
            # 目标存储类型不匹配
            if target_storage and d.library_storage != target_storage:
                continue
            # 有目标目录时，目标目录不匹配媒体库目录
            if dest_path and dest_path != Path(d.library_path):
                continue
            # 目录类型为全部的，符合条件
            if not d.media_type:
                matched_dirs.append(d)
                continue
            # 目录类型相等，目录类别为全部，符合条件
            if d.media_type == media_type and not d.media_category:
                matched_dirs.append(d)
                continue
            # 目录类型相等，目录类别相等，符合条件
            if d.media_type == media_type and d.media_category == media.category:
                matched_dirs.append(d)
                continue
        if matched_dirs:
            if src_path:
                # 优先源目录同盘
                for matched_dir in matched_dirs:
                    matched_path = Path(matched_dir.download_path)
                    if SystemUtils.is_same_disk(matched_path, src_path):
                        return matched_dir
            return matched_dirs[0]
        return None

    @staticmethod
    def get_media_root_path(rename_format: str, rename_path: Path) -> Optional[Path]:
        """
        获取重命名后的媒体文件根路径

        :param rename_format: 重命名格式
        :param rename_path: 重命名后的路径
        :return: 媒体文件根路径
        """
        if not rename_format:
            logger.error("重命名格式不能为空")
            return None
        # 计算重命名中的文件夹层数
        rename_list = rename_format.split("/")
        rename_format_level = len(rename_list) - 1
        # 查找标题参数所在层
        for level, name in enumerate(rename_list):
            matchs = JINJA2_VAR_PATTERN.findall(name)
            if not matchs:
                continue
            # 处理特例，有的人重命名的第一层是年份、分辨率
            if any("title" in m for m in matchs):
                # 找出含标题的这一层作为媒体根目录
                rename_format_level -= level
                break
        else:
            # 假定第一层目录是媒体根目录
            logger.warn(f"重命名格式 {rename_format} 缺少标题参数")
        if rename_format_level > len(rename_path.parents):
            # 通常因为路径以/结尾，被Path规范化删除了
            logger.error(f"路径 {rename_path} 不匹配重命名格式 {rename_format}")
            return None
        if rename_format_level <= 0:
            # 所有媒体文件都存在一个目录内的特殊需求
            rename_format_level = 1
        # 媒体根路径
        media_root = rename_path.parents[rename_format_level - 1]
        return media_root
