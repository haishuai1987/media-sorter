from typing import Any, List, Optional

from fastapi import APIRouter, Depends

from app import schemas
from app.chain.recommend import RecommendChain
from app.core.event import eventmanager
from app.core.security import verify_token
from app.schemas import RecommendSourceEventData
from app.schemas.types import ChainEventType

router = APIRouter()


@router.get("/source", summary="获取推荐数据源", response_model=List[schemas.RecommendMediaSource])
def source(_: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    获取推荐数据源
    """
    # 广播事件，请示额外的推荐数据源支持
    event_data = RecommendSourceEventData()
    event = eventmanager.send_event(ChainEventType.RecommendSource, event_data)
    # 使用事件返回的上下文数据
    if event and event.event_data:
        event_data: RecommendSourceEventData = event.event_data
        if event_data.extra_sources:
            return event_data.extra_sources
    return []


@router.get("/bangumi_calendar", summary="Bangumi每日放送", response_model=List[schemas.MediaInfo])
async def bangumi_calendar(page: Optional[int] = 1,
                           count: Optional[int] = 30,
                           _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    浏览Bangumi每日放送
    """
    return await RecommendChain().async_bangumi_calendar(page=page, count=count)


@router.get("/douban_showing", summary="豆瓣正在热映", response_model=List[schemas.MediaInfo])
async def douban_showing(page: Optional[int] = 1,
                         count: Optional[int] = 30,
                         _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    浏览豆瓣正在热映
    """
    return await RecommendChain().async_douban_movie_showing(page=page, count=count)


@router.get("/douban_movies", summary="豆瓣电影", response_model=List[schemas.MediaInfo])
async def douban_movies(sort: Optional[str] = "R",
                        tags: Optional[str] = "",
                        page: Optional[int] = 1,
                        count: Optional[int] = 30,
                        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    浏览豆瓣电影信息
    """
    return await RecommendChain().async_douban_movies(sort=sort, tags=tags, page=page, count=count)


@router.get("/douban_tvs", summary="豆瓣剧集", response_model=List[schemas.MediaInfo])
async def douban_tvs(sort: Optional[str] = "R",
                     tags: Optional[str] = "",
                     page: Optional[int] = 1,
                     count: Optional[int] = 30,
                     _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    浏览豆瓣剧集信息
    """
    return await RecommendChain().async_douban_tvs(sort=sort, tags=tags, page=page, count=count)


@router.get("/douban_movie_top250", summary="豆瓣电影TOP250", response_model=List[schemas.MediaInfo])
async def douban_movie_top250(page: Optional[int] = 1,
                              count: Optional[int] = 30,
                              _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    浏览豆瓣剧集信息
    """
    return await RecommendChain().async_douban_movie_top250(page=page, count=count)


@router.get("/douban_tv_weekly_chinese", summary="豆瓣国产剧集周榜", response_model=List[schemas.MediaInfo])
async def douban_tv_weekly_chinese(page: Optional[int] = 1,
                                   count: Optional[int] = 30,
                                   _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    中国每周剧集口碑榜
    """
    return await RecommendChain().async_douban_tv_weekly_chinese(page=page, count=count)


@router.get("/douban_tv_weekly_global", summary="豆瓣全球剧集周榜", response_model=List[schemas.MediaInfo])
async def douban_tv_weekly_global(page: Optional[int] = 1,
                                  count: Optional[int] = 30,
                                  _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    全球每周剧集口碑榜
    """
    return await RecommendChain().async_douban_tv_weekly_global(page=page, count=count)


@router.get("/douban_tv_animation", summary="豆瓣动画剧集", response_model=List[schemas.MediaInfo])
async def douban_tv_animation(page: Optional[int] = 1,
                              count: Optional[int] = 30,
                              _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    热门动画剧集
    """
    return await RecommendChain().async_douban_tv_animation(page=page, count=count)


@router.get("/douban_movie_hot", summary="豆瓣热门电影", response_model=List[schemas.MediaInfo])
async def douban_movie_hot(page: Optional[int] = 1,
                           count: Optional[int] = 30,
                           _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    热门电影
    """
    return await RecommendChain().async_douban_movie_hot(page=page, count=count)


@router.get("/douban_tv_hot", summary="豆瓣热门电视剧", response_model=List[schemas.MediaInfo])
async def douban_tv_hot(page: Optional[int] = 1,
                        count: Optional[int] = 30,
                        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    热门电视剧
    """
    return await RecommendChain().async_douban_tv_hot(page=page, count=count)


@router.get("/tmdb_movies", summary="TMDB电影", response_model=List[schemas.MediaInfo])
async def tmdb_movies(sort_by: Optional[str] = "popularity.desc",
                      with_genres: Optional[str] = "",
                      with_original_language: Optional[str] = "",
                      with_keywords: Optional[str] = "",
                      with_watch_providers: Optional[str] = "",
                      vote_average: Optional[float] = 0.0,
                      vote_count: Optional[int] = 0,
                      release_date: Optional[str] = "",
                      page: Optional[int] = 1,
                      _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    浏览TMDB电影信息
    """
    return await RecommendChain().async_tmdb_movies(sort_by=sort_by,
                                                    with_genres=with_genres,
                                                    with_original_language=with_original_language,
                                                    with_keywords=with_keywords,
                                                    with_watch_providers=with_watch_providers,
                                                    vote_average=vote_average,
                                                    vote_count=vote_count,
                                                    release_date=release_date,
                                                    page=page)


@router.get("/tmdb_tvs", summary="TMDB剧集", response_model=List[schemas.MediaInfo])
async def tmdb_tvs(sort_by: Optional[str] = "popularity.desc",
                   with_genres: Optional[str] = "",
                   with_original_language: Optional[str] = "",
                   with_keywords: Optional[str] = "",
                   with_watch_providers: Optional[str] = "",
                   vote_average: Optional[float] = 0.0,
                   vote_count: Optional[int] = 0,
                   release_date: Optional[str] = "",
                   page: Optional[int] = 1,
                   _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    浏览TMDB剧集信息
    """
    return await RecommendChain().async_tmdb_tvs(sort_by=sort_by,
                                                 with_genres=with_genres,
                                                 with_original_language=with_original_language,
                                                 with_keywords=with_keywords,
                                                 with_watch_providers=with_watch_providers,
                                                 vote_average=vote_average,
                                                 vote_count=vote_count,
                                                 release_date=release_date,
                                                 page=page)


@router.get("/tmdb_trending", summary="TMDB流行趋势", response_model=List[schemas.MediaInfo])
async def tmdb_trending(page: Optional[int] = 1,
                        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    TMDB流行趋势
    """
    return await RecommendChain().async_tmdb_trending(page=page)
