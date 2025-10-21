from typing import Optional

from sqlalchemy.orm import Session

from app.db import DbOper
from app.db.models.mediaserver import MediaServerItem


class MediaServerOper(DbOper):
    """
    媒体服务器数据管理
    """

    def __init__(self, db: Session = None):
        super().__init__(db)

    def add(self, **kwargs) -> bool:
        """
        新增媒体服务器数据
        """
        # MediaServerItem中没有的属性剔除
        kwargs = {k: v for k, v in kwargs.items() if hasattr(MediaServerItem, k)}
        item = MediaServerItem(**kwargs)
        if not item.get_by_itemid(self._db, kwargs.get("item_id")):
            item.create(self._db)
            return True
        return False

    def empty(self, server: Optional[str] = None):
        """
        清空媒体服务器数据
        """
        MediaServerItem.empty(self._db, server)

    def exists(self, **kwargs) -> Optional[MediaServerItem]:
        """
        判断媒体服务器数据是否存在
        """
        if kwargs.get("tmdbid"):
            # 优先按TMDBID查
            item = MediaServerItem.exist_by_tmdbid(self._db, tmdbid=kwargs.get("tmdbid"),
                                                   mtype=kwargs.get("mtype"))
        elif kwargs.get("title"):
            # 按标题、类型、年份查
            item = MediaServerItem.exists_by_title(self._db, title=kwargs.get("title"),
                                                   mtype=kwargs.get("mtype"), year=kwargs.get("year"))
        else:
            return None
        if not item:
            return None

        if kwargs.get("season"):
            # 判断季是否存在
            if not item.seasoninfo:
                return None
            seasoninfo = item.seasoninfo or {}
            if kwargs.get("season") not in seasoninfo.keys():
                return None
        return item

    async def async_exists(self, **kwargs) -> Optional[MediaServerItem]:
        """
        异步判断媒体服务器数据是否存在
        """
        if kwargs.get("tmdbid"):
            # 优先按TMDBID查
            item = await MediaServerItem.async_exist_by_tmdbid(self._db, tmdbid=kwargs.get("tmdbid"),
                                                               mtype=kwargs.get("mtype"))
        elif kwargs.get("title"):
            # 按标题、类型、年份查
            item = await MediaServerItem.async_exists_by_title(self._db, title=kwargs.get("title"),
                                                               mtype=kwargs.get("mtype"), year=kwargs.get("year"))
        else:
            return None
        if not item:
            return None

        if kwargs.get("season"):
            # 判断季是否存在
            if not item.seasoninfo:
                return None
            seasoninfo = item.seasoninfo or {}
            if kwargs.get("season") not in seasoninfo.keys():
                return None
        return item

    def get_item_id(self, **kwargs) -> Optional[str]:
        """
        获取媒体服务器数据ID
        """
        item = self.exists(**kwargs)
        if not item:
            return None
        return str(item.item_id)

    async def async_get_item_id(self, **kwargs) -> Optional[str]:
        """
        异步获取媒体服务器数据ID
        """
        item = await self.async_exists(**kwargs)
        if not item:
            return None
        return str(item.item_id)
