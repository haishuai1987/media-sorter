from typing import List, Optional, Tuple, Union

from app import schemas
from app.core.config import settings
from app.core.context import MediaInfo
from app.core.meta import MetaBase
from app.log import logger
from app.modules import _ModuleBase
from app.modules.bangumi.bangumi import BangumiApi
from app.schemas.types import ModuleType, MediaRecognizeType
from app.utils.http import RequestUtils


class BangumiModule(_ModuleBase):
    bangumiapi: BangumiApi = None

    def init_module(self) -> None:
        self.bangumiapi = BangumiApi()

    def stop(self):
        self.bangumiapi.close()

    def test(self) -> Tuple[bool, str]:
        """
        测试模块连接性
        """
        ret = RequestUtils().get_res("https://api.bgm.tv/")
        if ret and ret.status_code == 200:
            return True, ""
        elif ret:
            return False, f"无法连接Bangumi，错误码：{ret.status_code}"
        return False, "Bangumi网络连接失败"

    def init_setting(self) -> Tuple[str, Union[str, bool]]:
        pass

    @staticmethod
    def get_name() -> str:
        return "Bangumi"

    @staticmethod
    def get_type() -> ModuleType:
        """
        获取模块类型
        """
        return ModuleType.MediaRecognize

    @staticmethod
    def get_subtype() -> MediaRecognizeType:
        """
        获取模块子类型
        """
        return MediaRecognizeType.Bangumi

    @staticmethod
    def get_priority() -> int:
        """
        获取模块优先级，数字越小优先级越高，只有同一接口下优先级才生效
        """
        return 3

    def recognize_media(self, bangumiid: int = None,
                        **kwargs) -> Optional[MediaInfo]:
        """
        识别媒体信息
        :param bangumiid: 识别的Bangumi ID
        :return: 识别的媒体信息，包括剧集信息
        """
        if not bangumiid:
            return None

        # 直接查询详情
        info = self.bangumi_info(bangumiid=bangumiid)
        if info:
            # 赋值TMDB信息并返回
            mediainfo = MediaInfo(bangumi_info=info)
            logger.info(f"{bangumiid} Bangumi识别结果：{mediainfo.type.value} "
                        f"{mediainfo.title_year}")
            return mediainfo
        else:
            logger.info(f"{bangumiid} 未匹配到Bangumi媒体信息")

        return None

    async def async_recognize_media(self, bangumiid: int = None,
                                    **kwargs) -> Optional[MediaInfo]:
        """
        识别媒体信息（异步版本）
        :param bangumiid: 识别的Bangumi ID
        :return: 识别的媒体信息，包括剧集信息
        """
        if not bangumiid:
            return None

        # 直接查询详情
        info = await self.async_bangumi_info(bangumiid=bangumiid)
        if info:
            # 赋值TMDB信息并返回
            mediainfo = MediaInfo(bangumi_info=info)
            logger.info(f"{bangumiid} Bangumi识别结果：{mediainfo.type.value} "
                        f"{mediainfo.title_year}")
            return mediainfo
        else:
            logger.info(f"{bangumiid} 未匹配到Bangumi媒体信息")

        return None

    def search_medias(self, meta: MetaBase) -> Optional[List[MediaInfo]]:
        """
        搜索媒体信息
        :param meta:  识别的元数据
        :reutrn: 媒体信息
        """
        if settings.SEARCH_SOURCE and "bangumi" not in settings.SEARCH_SOURCE:
            return None
        if not meta.name:
            return []
        infos = self.bangumiapi.search(meta.name)
        if infos:
            return [MediaInfo(bangumi_info=info) for info in infos
                    if meta.name.lower() in str(info.get("name")).lower()
                    or meta.name.lower() in str(info.get("name_cn")).lower()]
        return []

    async def async_search_medias(self, meta: MetaBase) -> Optional[List[MediaInfo]]:
        """
        搜索媒体信息（异步版本）
        :param meta:  识别的元数据
        :reutrn: 媒体信息
        """
        if settings.SEARCH_SOURCE and "bangumi" not in settings.SEARCH_SOURCE:
            return None
        if not meta.name:
            return []
        infos = await self.bangumiapi.async_search(meta.name)
        if infos:
            return [MediaInfo(bangumi_info=info) for info in infos
                    if meta.name.lower() in str(info.get("name")).lower()
                    or meta.name.lower() in str(info.get("name_cn")).lower()]
        return []

    def bangumi_info(self, bangumiid: int) -> Optional[dict]:
        """
        获取Bangumi信息
        :param bangumiid: BangumiID
        :return: Bangumi信息
        """
        if not bangumiid:
            return None
        logger.info(f"开始获取Bangumi信息：{bangumiid} ...")
        return self.bangumiapi.detail(bangumiid)

    async def async_bangumi_info(self, bangumiid: int) -> Optional[dict]:
        """
        获取Bangumi信息（异步版本）
        :param bangumiid: BangumiID
        :return: Bangumi信息
        """
        if not bangumiid:
            return None
        logger.info(f"开始获取Bangumi信息：{bangumiid} ...")
        return await self.bangumiapi.async_detail(bangumiid)

    def bangumi_calendar(self) -> Optional[List[MediaInfo]]:
        """
        获取Bangumi每日放送
        """
        infos = self.bangumiapi.calendar()
        if infos:
            return [MediaInfo(bangumi_info=info) for info in infos]
        return []

    async def async_bangumi_calendar(self) -> Optional[List[MediaInfo]]:
        """
        获取Bangumi每日放送（异步版本）
        """
        infos = await self.bangumiapi.async_calendar()
        if infos:
            return [MediaInfo(bangumi_info=info) for info in infos]
        return []

    def bangumi_credits(self, bangumiid: int) -> List[schemas.MediaPerson]:
        """
        根据TMDBID查询电影演职员表
        :param bangumiid:  BangumiID
        """
        persons = self.bangumiapi.credits(bangumiid)
        if persons:
            return [schemas.MediaPerson(source='bangumi', **person) for person in persons]
        return []

    async def async_bangumi_credits(self, bangumiid: int) -> List[schemas.MediaPerson]:
        """
        根据TMDBID查询电影演职员表（异步版本）
        :param bangumiid:  BangumiID
        """
        persons = await self.bangumiapi.async_credits(bangumiid)
        if persons:
            return [schemas.MediaPerson(source='bangumi', **person) for person in persons]
        return []

    def bangumi_recommend(self, bangumiid: int) -> List[MediaInfo]:
        """
        根据BangumiID查询推荐电影
        :param bangumiid:  BangumiID
        """
        subjects = self.bangumiapi.subjects(bangumiid)
        if subjects:
            return [MediaInfo(bangumi_info=subject) for subject in subjects]
        return []

    async def async_bangumi_recommend(self, bangumiid: int) -> List[MediaInfo]:
        """
        根据BangumiID查询推荐电影（异步版本）
        :param bangumiid:  BangumiID
        """
        subjects = await self.bangumiapi.async_subjects(bangumiid)
        if subjects:
            return [MediaInfo(bangumi_info=subject) for subject in subjects]
        return []

    def bangumi_person_detail(self, person_id: int) -> Optional[schemas.MediaPerson]:
        """
        获取人物详细信息
        :param person_id:  豆瓣人物ID
        """
        personinfo = self.bangumiapi.person_detail(person_id)
        if personinfo:
            return schemas.MediaPerson(source='bangumi', **{
                "id": personinfo.get("id"),
                "name": personinfo.get("name"),
                "images": personinfo.get("images"),
                "biography": personinfo.get("summary"),
                "birthday": personinfo.get("birth_day"),
                "gender": personinfo.get("gender")
            })
        return None

    async def async_bangumi_person_detail(self, person_id: int) -> Optional[schemas.MediaPerson]:
        """
        获取人物详细信息（异步版本）
        :param person_id:  豆瓣人物ID
        """
        personinfo = await self.bangumiapi.async_person_detail(person_id)
        if personinfo:
            return schemas.MediaPerson(source='bangumi', **{
                "id": personinfo.get("id"),
                "name": personinfo.get("name"),
                "images": personinfo.get("images"),
                "biography": personinfo.get("summary"),
                "birthday": personinfo.get("birth_day"),
                "gender": personinfo.get("gender")
            })
        return None

    def bangumi_person_credits(self, person_id: int) -> List[MediaInfo]:
        """
        根据TMDBID查询人物参演作品
        :param person_id:  人物ID
        """
        credits_info = self.bangumiapi.person_credits(person_id=person_id)
        if credits_info:
            return [MediaInfo(bangumi_info=credit) for credit in credits_info]
        return []

    async def async_bangumi_person_credits(self, person_id: int) -> List[MediaInfo]:
        """
        根据TMDBID查询人物参演作品（异步版本）
        :param person_id:  人物ID
        """
        credits_info = await self.bangumiapi.async_person_credits(person_id=person_id)
        if credits_info:
            return [MediaInfo(bangumi_info=credit) for credit in credits_info]
        return []

    def bangumi_discover(self, **kwargs) -> Optional[List[MediaInfo]]:
        """
        发现Bangumi番剧
        """
        infos = self.bangumiapi.discover(**kwargs)
        if infos:
            return [MediaInfo(bangumi_info=info) for info in infos]
        return []

    async def async_bangumi_discover(self, **kwargs) -> Optional[List[MediaInfo]]:
        """
        发现Bangumi番剧（异步版本）
        """
        infos = await self.bangumiapi.async_discover(**kwargs)
        if infos:
            return [MediaInfo(bangumi_info=info) for info in infos]
        return []
