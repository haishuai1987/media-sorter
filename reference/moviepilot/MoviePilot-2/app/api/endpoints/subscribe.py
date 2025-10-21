from typing import List, Any, Annotated, Optional

import cn2an
from fastapi import APIRouter, Request, BackgroundTasks, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app import schemas
from app.chain.subscribe import SubscribeChain
from app.core.config import settings
from app.core.context import MediaInfo
from app.core.event import eventmanager
from app.core.metainfo import MetaInfo
from app.core.security import verify_token, verify_apitoken
from app.db import get_async_db, get_db
from app.db.models.subscribe import Subscribe
from app.db.models.subscribehistory import SubscribeHistory
from app.db.models.user import User
from app.db.systemconfig_oper import SystemConfigOper
from app.db.user_oper import get_current_active_user_async
from app.helper.subscribe import SubscribeHelper
from app.scheduler import Scheduler
from app.schemas.types import MediaType, EventType, SystemConfigKey

router = APIRouter()


def start_subscribe_add(title: str, year: str,
                        mtype: MediaType, tmdbid: int, season: int, username: str):
    """
    启动订阅任务
    """
    SubscribeChain().add(title=title, year=year,
                         mtype=mtype, tmdbid=tmdbid, season=season, username=username)


@router.get("/", summary="查询所有订阅", response_model=List[schemas.Subscribe])
async def read_subscribes(
        db: AsyncSession = Depends(get_async_db),
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    查询所有订阅
    """
    return await Subscribe.async_list(db)


@router.get("/list", summary="查询所有订阅（API_TOKEN）", response_model=List[schemas.Subscribe])
async def list_subscribes(_: Annotated[str, Depends(verify_apitoken)]) -> Any:
    """
    查询所有订阅 API_TOKEN认证（?token=xxx）
    """
    return await read_subscribes()


@router.post("/", summary="新增订阅", response_model=schemas.Response)
async def create_subscribe(
        *,
        subscribe_in: schemas.Subscribe,
        current_user: User = Depends(get_current_active_user_async),
) -> schemas.Response:
    """
    新增订阅
    """
    # 类型转换
    if subscribe_in.type:
        mtype = MediaType(subscribe_in.type)
    else:
        mtype = None
    # 豆瓣标理
    if subscribe_in.doubanid or subscribe_in.bangumiid:
        meta = MetaInfo(subscribe_in.name)
        subscribe_in.name = meta.name
        subscribe_in.season = meta.begin_season
    # 标题转换
    if subscribe_in.name:
        title = subscribe_in.name
    else:
        title = None
    # 订阅用户
    subscribe_in.username = current_user.name
    # 转化为字典
    subscribe_dict = subscribe_in.dict()
    if subscribe_in.id:
        subscribe_dict.pop("id", None)
    sid, message = await SubscribeChain().async_add(mtype=mtype,
                                                    title=title,
                                                    exist_ok=True,
                                                    **subscribe_dict)
    return schemas.Response(
        success=bool(sid), message=message, data={"id": sid}
    )


@router.put("/", summary="更新订阅", response_model=schemas.Response)
async def update_subscribe(
        *,
        subscribe_in: schemas.Subscribe,
        db: AsyncSession = Depends(get_async_db),
        _: schemas.TokenPayload = Depends(verify_token)
) -> Any:
    """
    更新订阅信息
    """
    subscribe = await Subscribe.async_get(db, subscribe_in.id)
    if not subscribe:
        return schemas.Response(success=False, message="订阅不存在")
    # 避免更新缺失集数
    old_subscribe_dict = subscribe.to_dict()
    subscribe_dict = subscribe_in.dict()
    if not subscribe_in.lack_episode:
        # 没有缺失集数时，缺失集数清空，避免更新为0
        subscribe_dict.pop("lack_episode")
    elif subscribe_in.total_episode:
        # 总集数增加时，缺失集数也要增加
        if subscribe_in.total_episode > (subscribe.total_episode or 0):
            subscribe_dict["lack_episode"] = (subscribe.lack_episode
                                              + (subscribe_in.total_episode
                                                 - (subscribe.total_episode or 0)))
    # 是否手动修改过总集数
    if subscribe_in.total_episode != subscribe.total_episode:
        subscribe_dict["manual_total_episode"] = 1
    # 更新到数据库
    await subscribe.async_update(db, subscribe_dict)
    # 重新获取更新后的订阅数据
    updated_subscribe = await Subscribe.async_get(db, subscribe_in.id)
    # 发送订阅调整事件
    await eventmanager.async_send_event(EventType.SubscribeModified, {
        "subscribe_id": subscribe_in.id,
        "old_subscribe_info": old_subscribe_dict,
        "subscribe_info": updated_subscribe.to_dict() if updated_subscribe else {},
    })
    return schemas.Response(success=True)


@router.put("/status/{subid}", summary="更新订阅状态", response_model=schemas.Response)
async def update_subscribe_status(
        subid: int,
        state: str,
        db: AsyncSession = Depends(get_async_db),
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    更新订阅状态
    """
    subscribe = await Subscribe.async_get(db, subid)
    if not subscribe:
        return schemas.Response(success=False, message="订阅不存在")
    valid_states = ["R", "P", "S"]
    if state not in valid_states:
        return schemas.Response(success=False, message="无效的订阅状态")
    old_subscribe_dict = subscribe.to_dict()
    await subscribe.async_update(db, {
        "state": state
    })
    # 重新获取更新后的订阅数据
    updated_subscribe = await Subscribe.async_get(db, subid)
    # 发送订阅调整事件
    await eventmanager.async_send_event(EventType.SubscribeModified, {
        "subscribe_id": subid,
        "old_subscribe_info": old_subscribe_dict,
        "subscribe_info": updated_subscribe.to_dict() if updated_subscribe else {},
    })
    return schemas.Response(success=True)


@router.get("/media/{mediaid}", summary="查询订阅", response_model=schemas.Subscribe)
async def subscribe_mediaid(
        mediaid: str,
        season: Optional[int] = None,
        title: Optional[str] = None,
        db: AsyncSession = Depends(get_async_db),
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    根据 TMDBID/豆瓣ID/BangumiId 查询订阅 tmdb:/douban:
    """
    title_check = False
    if mediaid.startswith("tmdb:"):
        tmdbid = mediaid[5:]
        if not tmdbid or not str(tmdbid).isdigit():
            return Subscribe()
        result = await Subscribe.async_exists(db, tmdbid=int(tmdbid), season=season)
    elif mediaid.startswith("douban:"):
        doubanid = mediaid[7:]
        if not doubanid:
            return Subscribe()
        result = await Subscribe.async_get_by_doubanid(db, doubanid)
        if not result and title:
            title_check = True
    elif mediaid.startswith("bangumi:"):
        bangumiid = mediaid[8:]
        if not bangumiid or not str(bangumiid).isdigit():
            return Subscribe()
        result = await Subscribe.async_get_by_bangumiid(db, int(bangumiid))
        if not result and title:
            title_check = True
    else:
        result = await Subscribe.async_get_by_mediaid(db, mediaid)
        if not result and title:
            title_check = True
    # 使用名称检查订阅
    if title_check and title:
        meta = MetaInfo(title)
        if season:
            meta.begin_season = season
        result = await Subscribe.async_get_by_title(db, title=meta.name, season=meta.begin_season)

    return result if result else Subscribe()


@router.get("/refresh", summary="刷新订阅", response_model=schemas.Response)
def refresh_subscribes(
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    刷新所有订阅
    """
    Scheduler().start("subscribe_refresh")
    return schemas.Response(success=True)


@router.get("/reset/{subid}", summary="重置订阅", response_model=schemas.Response)
async def reset_subscribes(
        subid: int,
        db: AsyncSession = Depends(get_async_db),
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    重置订阅
    """
    subscribe = await Subscribe.async_get(db, subid)
    if subscribe:
        # 在更新之前获取旧数据
        old_subscribe_dict = subscribe.to_dict()
        # 更新订阅
        await subscribe.async_update(db, {
            "note": [],
            "lack_episode": subscribe.total_episode,
            "state": "R"
        })
        # 重新获取更新后的订阅数据
        updated_subscribe = await Subscribe.async_get(db, subid)
        # 发送订阅调整事件
        await eventmanager.async_send_event(EventType.SubscribeModified, {
            "subscribe_id": subid,
            "old_subscribe_info": old_subscribe_dict,
            "subscribe_info": updated_subscribe.to_dict() if updated_subscribe else {},
        })
        return schemas.Response(success=True)
    return schemas.Response(success=False, message="订阅不存在")


@router.get("/check", summary="刷新订阅 TMDB 信息", response_model=schemas.Response)
def check_subscribes(
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    刷新订阅 TMDB 信息
    """
    Scheduler().start("subscribe_tmdb")
    return schemas.Response(success=True)


@router.get("/search", summary="搜索所有订阅", response_model=schemas.Response)
async def search_subscribes(
        background_tasks: BackgroundTasks,
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    搜索所有订阅
    """
    background_tasks.add_task(
        Scheduler().start,
        job_id="subscribe_search",
        **{
            "sid": None,
            "state": 'R',
            "manual": True
        }
    )
    return schemas.Response(success=True)


@router.get("/search/{subscribe_id}", summary="搜索订阅", response_model=schemas.Response)
async def search_subscribe(
        subscribe_id: int,
        background_tasks: BackgroundTasks,
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    根据订阅编号搜索订阅
    """
    background_tasks.add_task(
        Scheduler().start,
        job_id="subscribe_search",
        **{
            "sid": subscribe_id,
            "state": None,
            "manual": True
        }
    )
    return schemas.Response(success=True)


@router.delete("/media/{mediaid}", summary="删除订阅", response_model=schemas.Response)
async def delete_subscribe_by_mediaid(
        mediaid: str,
        season: Optional[int] = None,
        db: AsyncSession = Depends(get_async_db),
        _: schemas.TokenPayload = Depends(verify_token)
) -> Any:
    """
    根据TMDBID或豆瓣ID删除订阅 tmdb:/douban:
    """
    delete_subscribes = []
    if mediaid.startswith("tmdb:"):
        tmdbid = mediaid[5:]
        if not tmdbid or not str(tmdbid).isdigit():
            return schemas.Response(success=False)
        subscribes = await Subscribe.async_get_by_tmdbid(db, int(tmdbid), season)
        delete_subscribes.extend(subscribes)
    elif mediaid.startswith("douban:"):
        doubanid = mediaid[7:]
        if not doubanid:
            return schemas.Response(success=False)
        subscribe = await Subscribe.async_get_by_doubanid(db, doubanid)
        if subscribe:
            delete_subscribes.append(subscribe)
    else:
        subscribe = await Subscribe.async_get_by_mediaid(db, mediaid)
        if subscribe:
            delete_subscribes.append(subscribe)
    for subscribe in delete_subscribes:
        # 在删除之前获取订阅信息
        subscribe_info = subscribe.to_dict()
        subscribe_id = subscribe.id
        await Subscribe.async_delete(db, subscribe_id)
        # 发送事件
        await eventmanager.async_send_event(EventType.SubscribeDeleted, {
            "subscribe_id": subscribe_id,
            "subscribe_info": subscribe_info
        })
    return schemas.Response(success=True)


@router.post("/seerr", summary="OverSeerr/JellySeerr通知订阅", response_model=schemas.Response)
async def seerr_subscribe(request: Request, background_tasks: BackgroundTasks,
                          authorization: Annotated[str | None, Header()] = None) -> Any:
    """
    Jellyseerr/Overseerr网络勾子通知订阅
    """
    if not authorization or authorization != settings.API_TOKEN:
        raise HTTPException(
            status_code=400,
            detail="授权失败",
        )
    req_json = await request.json()
    if not req_json:
        raise HTTPException(
            status_code=500,
            detail="报文内容为空",
        )
    notification_type = req_json.get("notification_type")
    if notification_type not in ["MEDIA_APPROVED", "MEDIA_AUTO_APPROVED"]:
        return schemas.Response(success=False, message="不支持的通知类型")
    subject = req_json.get("subject")
    media_type = MediaType.MOVIE if req_json.get("media", {}).get("media_type") == "movie" else MediaType.TV
    tmdbId = req_json.get("media", {}).get("tmdbId")
    if not media_type or not tmdbId or not subject:
        return schemas.Response(success=False, message="请求参数不正确")
    user_name = req_json.get("request", {}).get("requestedBy_username")
    # 添加订阅
    if media_type == MediaType.MOVIE:
        background_tasks.add_task(start_subscribe_add,
                                  mtype=media_type,
                                  tmdbid=tmdbId,
                                  title=subject,
                                  year="",
                                  season=0,
                                  username=user_name)
    else:
        seasons = []
        for extra in req_json.get("extra", []):
            if extra.get("name") == "Requested Seasons":
                seasons = [int(str(sea).strip()) for sea in extra.get("value").split(", ") if str(sea).isdigit()]
                break
        for season in seasons:
            background_tasks.add_task(start_subscribe_add,
                                      mtype=media_type,
                                      tmdbid=tmdbId,
                                      title=subject,
                                      year="",
                                      season=season,
                                      username=user_name)

    return schemas.Response(success=True)


@router.get("/history/{mtype}", summary="查询订阅历史", response_model=List[schemas.Subscribe])
async def subscribe_history(
        mtype: str,
        page: Optional[int] = 1,
        count: Optional[int] = 30,
        db: AsyncSession = Depends(get_async_db),
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    查询电影/电视剧订阅历史
    """
    return await SubscribeHistory.async_list_by_type(db, mtype=mtype, page=page, count=count)


@router.delete("/history/{history_id}", summary="删除订阅历史", response_model=schemas.Response)
async def delete_subscribe(
        history_id: int,
        db: AsyncSession = Depends(get_async_db),
        _: schemas.TokenPayload = Depends(verify_token)
) -> Any:
    """
    删除订阅历史
    """
    await SubscribeHistory.async_delete(db, history_id)
    return schemas.Response(success=True)


@router.get("/popular", summary="热门订阅（基于用户共享数据）", response_model=List[schemas.MediaInfo])
async def popular_subscribes(
        stype: str,
        page: Optional[int] = 1,
        count: Optional[int] = 30,
        min_sub: Optional[int] = None,
        genre_id: Optional[int] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        sort_type: Optional[str] = None,
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    查询热门订阅
    """
    subscribes = await SubscribeHelper().async_get_statistic(
        stype=stype,
        page=page,
        count=count,
        genre_id=genre_id,
        min_rating=min_rating,
        max_rating=max_rating,
        sort_type=sort_type
    )
    if subscribes:
        ret_medias = []
        for sub in subscribes:
            # 订阅人数
            count = sub.get("count")
            if min_sub and count < min_sub:
                continue
            media = MediaInfo()
            media.type = MediaType(sub.get("type"))
            media.tmdb_id = sub.get("tmdbid")
            # 处理标题
            title = sub.get("name")
            season = sub.get("season")
            if season and int(season) > 1 and media.tmdb_id:
                # 小写数据转大写
                season_str = cn2an.an2cn(season, "low")
                title = f"{title} 第{season_str}季"
            media.title = title
            media.year = sub.get("year")
            media.douban_id = sub.get("doubanid")
            media.bangumi_id = sub.get("bangumiid")
            media.tvdb_id = sub.get("tvdbid")
            media.imdb_id = sub.get("imdbid")
            media.season = sub.get("season")
            media.overview = sub.get("description")
            media.vote_average = sub.get("vote")
            media.poster_path = sub.get("poster")
            media.backdrop_path = sub.get("backdrop")
            media.popularity = count
            ret_medias.append(media)
        return [media.to_dict() for media in ret_medias]
    return []


@router.get("/user/{username}", summary="用户订阅", response_model=List[schemas.Subscribe])
async def user_subscribes(
        username: str,
        db: AsyncSession = Depends(get_async_db),
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    查询用户订阅
    """
    return await Subscribe.async_list_by_username(db, username)


@router.get("/files/{subscribe_id}", summary="订阅相关文件信息", response_model=schemas.SubscrbieInfo)
def subscribe_files(
        subscribe_id: int,
        db: Session = Depends(get_db),
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    订阅相关文件信息
    """
    subscribe = Subscribe.get(db, subscribe_id)
    if subscribe:
        return SubscribeChain().subscribe_files_info(subscribe)
    return schemas.SubscrbieInfo()


@router.post("/share", summary="分享订阅", response_model=schemas.Response)
async def subscribe_share(
        sub: schemas.SubscribeShare,
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    分享订阅
    """
    state, errmsg = await SubscribeHelper().async_sub_share(subscribe_id=sub.subscribe_id,
                                                            share_title=sub.share_title,
                                                            share_comment=sub.share_comment,
                                                            share_user=sub.share_user)
    return schemas.Response(success=state, message=errmsg)


@router.delete("/share/{share_id}", summary="删除分享", response_model=schemas.Response)
async def subscribe_share_delete(
        share_id: int,
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    删除分享
    """
    state, errmsg = await SubscribeHelper().async_share_delete(share_id=share_id)
    return schemas.Response(success=state, message=errmsg)


@router.post("/fork", summary="复用订阅", response_model=schemas.Response)
async def subscribe_fork(
        sub: schemas.SubscribeShare,
        current_user: User = Depends(get_current_active_user_async)) -> Any:
    """
    复用订阅
    """
    sub_dict = sub.dict()
    sub_dict.pop("id")
    for key in list(sub_dict.keys()):
        if not hasattr(schemas.Subscribe(), key):
            sub_dict.pop(key)
    result = await create_subscribe(subscribe_in=schemas.Subscribe(**sub_dict),
                                    current_user=current_user)
    if result.success:
        await SubscribeHelper().async_sub_fork(share_id=sub.id)
    return result


@router.get("/follow", summary="查询已Follow的订阅分享人", response_model=List[str])
async def followed_subscribers(_: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    查询已Follow的订阅分享人
    """
    return SystemConfigOper().get(SystemConfigKey.FollowSubscribers) or []


@router.post("/follow", summary="Follow订阅分享人", response_model=schemas.Response)
async def follow_subscriber(
        share_uid: Optional[str] = None,
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    Follow订阅分享人
    """
    subscribers = SystemConfigOper().get(SystemConfigKey.FollowSubscribers) or []
    if share_uid and share_uid not in subscribers:
        subscribers.append(share_uid)
        await SystemConfigOper().async_set(SystemConfigKey.FollowSubscribers, subscribers)
    return schemas.Response(success=True)


@router.delete("/follow", summary="取消Follow订阅分享人", response_model=schemas.Response)
async def unfollow_subscriber(
        share_uid: Optional[str] = None,
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    取消Follow订阅分享人
    """
    subscribers = SystemConfigOper().get(SystemConfigKey.FollowSubscribers) or []
    if share_uid and share_uid in subscribers:
        subscribers.remove(share_uid)
        await SystemConfigOper().async_set(SystemConfigKey.FollowSubscribers, subscribers)
    return schemas.Response(success=True)


@router.get("/shares", summary="查询分享的订阅", response_model=List[schemas.SubscribeShare])
async def popular_subscribes(
        name: Optional[str] = None,
        page: Optional[int] = 1,
        count: Optional[int] = 30,
        genre_id: Optional[int] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        sort_type: Optional[str] = None,
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    查询分享的订阅
    """
    return await SubscribeHelper().async_get_shares(
        name=name,
        page=page,
        count=count,
        genre_id=genre_id,
        min_rating=min_rating,
        max_rating=max_rating,
        sort_type=sort_type
    )


@router.get("/share/statistics", summary="查询订阅分享统计", response_model=List[schemas.SubscribeShareStatistics])
async def subscribe_share_statistics(_: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    查询订阅分享统计
    返回每个分享人分享的媒体数量以及总的复用人次
    """
    return await SubscribeHelper().async_get_share_statistics()


@router.get("/{subscribe_id}", summary="订阅详情", response_model=schemas.Subscribe)
async def read_subscribe(
        subscribe_id: int,
        db: AsyncSession = Depends(get_async_db),
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    根据订阅编号查询订阅信息
    """
    if not subscribe_id:
        return Subscribe()
    return await Subscribe.async_get(db, subscribe_id)


@router.delete("/{subscribe_id}", summary="删除订阅", response_model=schemas.Response)
async def delete_subscribe(
        subscribe_id: int,
        db: AsyncSession = Depends(get_async_db),
        _: schemas.TokenPayload = Depends(verify_token)
) -> Any:
    """
    删除订阅信息
    """
    subscribe = await Subscribe.async_get(db, subscribe_id)
    if subscribe:
        # 在删除之前获取订阅信息
        subscribe_info = subscribe.to_dict()
        await Subscribe.async_delete(db, subscribe_id)
        # 发送事件
        await eventmanager.async_send_event(EventType.SubscribeDeleted, {
            "subscribe_id": subscribe_id,
            "subscribe_info": subscribe_info
        })
        # 统计订阅
        SubscribeHelper().sub_done_async({
            "tmdbid": subscribe.tmdbid,
            "doubanid": subscribe.doubanid
        })
    return schemas.Response(success=True)
