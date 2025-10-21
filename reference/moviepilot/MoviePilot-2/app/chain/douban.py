from typing import Optional, List

from app import schemas
from app.chain import ChainBase
from app.core.context import MediaInfo
from app.schemas import MediaType


class DoubanChain(ChainBase):
    """
    豆瓣处理链
    """

    def person_detail(self, person_id: int) -> Optional[schemas.MediaPerson]:
        """
        根据人物ID查询豆瓣人物详情
        :param person_id:  人物ID
        """
        return self.run_module("douban_person_detail", person_id=person_id)

    def person_credits(self, person_id: int, page: Optional[int] = 1) -> List[MediaInfo]:
        """
        根据人物ID查询人物参演作品
        :param person_id:  人物ID
        :param page:  页码
        """
        return self.run_module("douban_person_credits", person_id=person_id, page=page)

    def movie_top250(self, page: Optional[int] = 1, count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        获取豆瓣电影TOP250
        :param page:  页码
        :param count:  每页数量
        """
        return self.run_module("movie_top250", page=page, count=count)

    def movie_showing(self, page: Optional[int] = 1, count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        获取正在上映的电影
        """
        return self.run_module("movie_showing", page=page, count=count)

    def tv_weekly_chinese(self, page: Optional[int] = 1, count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        获取本周中国剧集榜
        """
        return self.run_module("tv_weekly_chinese", page=page, count=count)

    def tv_weekly_global(self, page: Optional[int] = 1, count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        获取本周全球剧集榜
        """
        return self.run_module("tv_weekly_global", page=page, count=count)

    def douban_discover(self, mtype: MediaType, sort: str, tags: str,
                        page: Optional[int] = 0, count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        发现豆瓣电影、剧集
        :param mtype:  媒体类型
        :param sort:  排序方式
        :param tags:  标签
        :param page:  页码
        :param count:  数量
        :return: 媒体信息列表
        """
        return self.run_module("douban_discover", mtype=mtype, sort=sort, tags=tags,
                               page=page, count=count)

    def tv_animation(self, page: Optional[int] = 1, count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        获取动画剧集
        """
        return self.run_module("tv_animation", page=page, count=count)

    def movie_hot(self, page: Optional[int] = 1, count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        获取热门电影
        """
        return self.run_module("movie_hot", page=page, count=count)

    def tv_hot(self, page: Optional[int] = 1, count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        获取热门剧集
        """
        return self.run_module("tv_hot", page=page, count=count)

    def movie_credits(self, doubanid: str) -> Optional[List[schemas.MediaPerson]]:
        """
        根据TMDBID查询电影演职人员
        :param doubanid:  豆瓣ID
        """
        return self.run_module("douban_movie_credits", doubanid=doubanid)

    def tv_credits(self, doubanid: str) -> Optional[List[schemas.MediaPerson]]:
        """
        根据TMDBID查询电视剧演职人员
        :param doubanid:  豆瓣ID
        """
        return self.run_module("douban_tv_credits", doubanid=doubanid)

    def movie_recommend(self, doubanid: str) -> List[MediaInfo]:
        """
        根据豆瓣ID查询推荐电影
        :param doubanid:  豆瓣ID
        """
        return self.run_module("douban_movie_recommend", doubanid=doubanid)

    def tv_recommend(self, doubanid: str) -> List[MediaInfo]:
        """
        根据豆瓣ID查询推荐电视剧
        :param doubanid:  豆瓣ID
        """
        return self.run_module("douban_tv_recommend", doubanid=doubanid)

    async def async_person_detail(self, person_id: int) -> Optional[schemas.MediaPerson]:
        """
        根据人物ID查询豆瓣人物详情（异步版本）
        :param person_id:  人物ID
        """
        return await self.async_run_module("async_douban_person_detail", person_id=person_id)

    async def async_person_credits(self, person_id: int, page: Optional[int] = 1) -> List[MediaInfo]:
        """
        根据人物ID查询人物参演作品（异步版本）
        :param person_id:  人物ID
        :param page:  页码
        """
        return await self.async_run_module("async_douban_person_credits", person_id=person_id, page=page)

    async def async_movie_top250(self, page: Optional[int] = 1,
                                 count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        获取豆瓣电影TOP250（异步版本）
        :param page:  页码
        :param count:  每页数量
        """
        return await self.async_run_module("async_movie_top250", page=page, count=count)

    async def async_movie_showing(self, page: Optional[int] = 1,
                                  count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        获取正在上映的电影（异步版本）
        """
        return await self.async_run_module("async_movie_showing", page=page, count=count)

    async def async_tv_weekly_chinese(self, page: Optional[int] = 1,
                                      count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        获取本周中国剧集榜（异步版本）
        """
        return await self.async_run_module("async_tv_weekly_chinese", page=page, count=count)

    async def async_tv_weekly_global(self, page: Optional[int] = 1,
                                     count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        获取本周全球剧集榜（异步版本）
        """
        return await self.async_run_module("async_tv_weekly_global", page=page, count=count)

    async def async_douban_discover(self, mtype: MediaType, sort: str, tags: str,
                                    page: Optional[int] = 0, count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        发现豆瓣电影、剧集（异步版本）
        :param mtype:  媒体类型
        :param sort:  排序方式
        :param tags:  标签
        :param page:  页码
        :param count:  数量
        :return: 媒体信息列表
        """
        return await self.async_run_module("async_douban_discover", mtype=mtype, sort=sort, tags=tags,
                                           page=page, count=count)

    async def async_tv_animation(self, page: Optional[int] = 1,
                                 count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        获取动画剧集（异步版本）
        """
        return await self.async_run_module("async_tv_animation", page=page, count=count)

    async def async_movie_hot(self, page: Optional[int] = 1,
                              count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        获取热门电影（异步版本）
        """
        return await self.async_run_module("async_movie_hot", page=page, count=count)

    async def async_tv_hot(self, page: Optional[int] = 1,
                           count: Optional[int] = 30) -> Optional[List[MediaInfo]]:
        """
        获取热门剧集（异步版本）
        """
        return await self.async_run_module("async_tv_hot", page=page, count=count)

    async def async_movie_credits(self, doubanid: str) -> Optional[List[schemas.MediaPerson]]:
        """
        根据TMDBID查询电影演职人员（异步版本）
        :param doubanid:  豆瓣ID
        """
        return await self.async_run_module("async_douban_movie_credits", doubanid=doubanid)

    async def async_tv_credits(self, doubanid: str) -> Optional[List[schemas.MediaPerson]]:
        """
        根据TMDBID查询电视剧演职人员（异步版本）
        :param doubanid:  豆瓣ID
        """
        return await self.async_run_module("async_douban_tv_credits", doubanid=doubanid)

    async def async_movie_recommend(self, doubanid: str) -> List[MediaInfo]:
        """
        根据豆瓣ID查询推荐电影（异步版本）
        :param doubanid:  豆瓣ID
        """
        return await self.async_run_module("async_douban_movie_recommend", doubanid=doubanid)

    async def async_tv_recommend(self, doubanid: str) -> List[MediaInfo]:
        """
        根据豆瓣ID查询推荐电视剧（异步版本）
        :param doubanid:  豆瓣ID
        """
        return await self.async_run_module("async_douban_tv_recommend", doubanid=doubanid)
