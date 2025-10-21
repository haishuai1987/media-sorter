from typing import List, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks

from app import schemas
from app.api.endpoints.plugin import register_plugin_api
from app.chain.site import SiteChain
from app.chain.torrents import TorrentsChain
from app.command import Command
from app.core.event import eventmanager
from app.core.plugin import PluginManager
from app.core.security import verify_token
from app.db import get_db, get_async_db
from app.db.models import User
from app.db.models.site import Site
from app.db.models.siteicon import SiteIcon
from app.db.models.sitestatistic import SiteStatistic
from app.db.models.siteuserdata import SiteUserData
from app.db.site_oper import SiteOper
from app.db.systemconfig_oper import SystemConfigOper
from app.db.user_oper import get_current_active_superuser, get_current_active_superuser_async
from app.helper.sites import SitesHelper  # noqa
from app.scheduler import Scheduler
from app.schemas.types import SystemConfigKey, EventType
from app.utils.string import StringUtils

router = APIRouter()


@router.get("/", summary="所有站点", response_model=List[schemas.Site])
async def read_sites(db: AsyncSession = Depends(get_async_db),
                     _: User = Depends(get_current_active_superuser)) -> List[dict]:
    """
    获取站点列表
    """
    return await Site.async_list_order_by_pri(db)


@router.post("/", summary="新增站点", response_model=schemas.Response)
async def add_site(
        *,
        db: AsyncSession = Depends(get_async_db),
        site_in: schemas.Site,
        _: User = Depends(get_current_active_superuser)
) -> Any:
    """
    新增站点
    """
    if not site_in.url:
        return schemas.Response(success=False, message="站点地址不能为空")
    if SitesHelper().auth_level < 2:
        return schemas.Response(success=False, message="用户未通过认证，无法使用站点功能！")
    domain = StringUtils.get_url_domain(site_in.url)
    site_info = await SitesHelper().async_get_indexer(domain)
    if not site_info:
        return schemas.Response(success=False, message="该站点不支持，请检查站点域名是否正确")
    if await Site.async_get_by_domain(db, domain):
        return schemas.Response(success=False, message=f"{domain} 站点己存在")
    # 保存站点信息
    site_in.domain = domain
    # 校正地址格式
    _scheme, _netloc = StringUtils.get_url_netloc(site_in.url)
    site_in.url = f"{_scheme}://{_netloc}/"
    site_in.name = site_info.get("name")
    site_in.id = None
    site_in.public = 1 if site_info.get("public") else 0
    site = Site(**site_in.dict())
    site.create(db)
    # 通知站点更新
    await eventmanager.async_send_event(EventType.SiteUpdated, {
        "domain": domain
    })
    return schemas.Response(success=True)


@router.put("/", summary="更新站点", response_model=schemas.Response)
async def update_site(
        *,
        db: AsyncSession = Depends(get_async_db),
        site_in: schemas.Site,
        _: User = Depends(get_current_active_superuser)
) -> Any:
    """
    更新站点信息
    """
    site = await Site.async_get(db, site_in.id)
    if not site:
        return schemas.Response(success=False, message="站点不存在")
    # 校正地址格式
    _scheme, _netloc = StringUtils.get_url_netloc(site_in.url)
    site_in.url = f"{_scheme}://{_netloc}/"
    await site.async_update(db, site_in.dict())
    # 通知站点更新
    await eventmanager.async_send_event(EventType.SiteUpdated, {
        "domain": site_in.domain
    })
    return schemas.Response(success=True)


@router.get("/cookiecloud", summary="CookieCloud同步", response_model=schemas.Response)
async def cookie_cloud_sync(background_tasks: BackgroundTasks,
                            _: User = Depends(get_current_active_superuser_async)) -> Any:
    """
    运行CookieCloud同步站点信息
    """
    background_tasks.add_task(Scheduler().start, job_id="cookiecloud")
    return schemas.Response(success=True, message="CookieCloud同步任务已启动！")


@router.get("/reset", summary="重置站点", response_model=schemas.Response)
def reset(db: AsyncSession = Depends(get_db),
          _: User = Depends(get_current_active_superuser)) -> Any:
    """
    清空所有站点数据并重新同步CookieCloud站点信息
    """
    Site.reset(db)
    SystemConfigOper().set(SystemConfigKey.IndexerSites, [])
    SystemConfigOper().set(SystemConfigKey.RssSites, [])
    # 启动定时服务
    Scheduler().start("cookiecloud", manual=True)
    # 插件站点删除
    eventmanager.send_event(EventType.SiteDeleted,
                            {
                                "site_id": "*"
                            })
    return schemas.Response(success=True, message="站点已重置！")


@router.post("/priorities", summary="批量更新站点优先级", response_model=schemas.Response)
async def update_sites_priority(
        priorities: List[dict],
        db: AsyncSession = Depends(get_async_db),
        _: User = Depends(get_current_active_superuser_async)) -> Any:
    """
    批量更新站点优先级
    """
    for priority in priorities:
        site = await Site.async_get(db, priority.get("id"))
        if site:
            await site.async_update(db, {"pri": priority.get("pri")})
    return schemas.Response(success=True)


@router.get("/cookie/{site_id}", summary="更新站点Cookie&UA", response_model=schemas.Response)
def update_cookie(
        site_id: int,
        username: str,
        password: str,
        code: Optional[str] = None,
        db: Session = Depends(get_db),
        _: User = Depends(get_current_active_superuser)) -> Any:
    """
    使用用户密码更新站点Cookie
    """
    # 查询站点
    site_info = Site.get(db, site_id)
    if not site_info:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {site_id} 不存在！",
        )
    # 更新Cookie
    state, message = SiteChain().update_cookie(site_info=site_info,
                                               username=username,
                                               password=password,
                                               two_step_code=code)
    return schemas.Response(success=state, message=message)


@router.post("/userdata/{site_id}", summary="更新站点用户数据", response_model=schemas.Response)
def refresh_userdata(
        site_id: int,
        db: Session = Depends(get_db),
        _: User = Depends(get_current_active_superuser)) -> Any:
    """
    刷新站点用户数据
    """
    site = Site.get(db, site_id)
    if not site:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {site_id} 不存在",
        )
    indexer = SitesHelper().get_indexer(site.domain)
    if not indexer:
        return schemas.Response(success=False, message="站点不支持索引或未通过用户认证！")
    user_data = SiteChain().refresh_userdata(site=indexer) or {}
    return schemas.Response(success=True, data=user_data)


@router.get("/userdata/latest", summary="查询所有站点最新用户数据", response_model=List[schemas.SiteUserData])
async def read_userdata_latest(
        db: AsyncSession = Depends(get_async_db),
        _: User = Depends(get_current_active_superuser_async)) -> Any:
    """
    查询所有站点最新用户数据
    """
    user_datas = await SiteUserData.async_get_latest(db)
    if not user_datas:
        return []
    return [user_data.to_dict() for user_data in user_datas]


@router.get("/userdata/{site_id}", summary="查询某站点用户数据", response_model=schemas.Response)
async def read_userdata(
        site_id: int,
        workdate: Optional[str] = None,
        db: AsyncSession = Depends(get_async_db),
        _: User = Depends(get_current_active_superuser_async)) -> Any:
    """
    查询站点用户数据
    """
    site = await Site.async_get(db, site_id)
    if not site:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {site_id} 不存在",
        )
    user_data = await SiteUserData.async_get_by_domain(db, domain=site.domain, workdate=workdate)
    if not user_data:
        return schemas.Response(success=False, data=[])
    return schemas.Response(success=True, data=user_data)


@router.get("/test/{site_id}", summary="连接测试", response_model=schemas.Response)
def test_site(site_id: int,
              db: Session = Depends(get_db),
              _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    测试站点是否可用
    """
    site = Site.get(db, site_id)
    if not site:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {site_id} 不存在",
        )
    status, message = SiteChain().test(site.domain)
    return schemas.Response(success=status, message=message)


@router.get("/icon/{site_id}", summary="站点图标", response_model=schemas.Response)
async def site_icon(site_id: int,
                    db: AsyncSession = Depends(get_async_db),
                    _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    获取站点图标：base64或者url
    """
    site = await Site.async_get(db, site_id)
    if not site:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {site_id} 不存在",
        )
    icon = await SiteIcon.async_get_by_domain(db, site.domain)
    if not icon:
        return schemas.Response(success=False, message="站点图标不存在！")
    return schemas.Response(success=True, data={
        "icon": icon.base64 if icon.base64 else icon.url
    })


@router.get("/category/{site_id}", summary="站点分类", response_model=List[schemas.SiteCategory])
async def site_category(site_id: int,
                        db: AsyncSession = Depends(get_async_db),
                        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    获取站点分类
    """
    site = await Site.async_get(db, site_id)
    if not site:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {site_id} 不存在",
        )
    indexer = await SitesHelper().async_get_indexer(site.domain)
    if not indexer:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {site.domain} 不支持",
        )
    category: Dict[str, List[dict]] = indexer.get('category') or []
    if not category:
        return []
    result = []
    for cats in category.values():
        for cat in cats:
            if cat not in result:
                result.append(cat)
    return result


@router.get("/resource/{site_id}", summary="站点资源", response_model=List[schemas.TorrentInfo])
async def site_resource(site_id: int,
                        keyword: Optional[str] = None,
                        cat: Optional[str] = None,
                        page: Optional[int] = 0,
                        db: AsyncSession = Depends(get_async_db),
                        _: User = Depends(get_current_active_superuser_async)) -> Any:
    """
    浏览站点资源
    """
    site = await Site.async_get(db, site_id)
    if not site:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {site_id} 不存在",
        )
    torrents = await TorrentsChain().async_browse(domain=site.domain, keyword=keyword, cat=cat, page=page)
    if not torrents:
        return []
    return [torrent.to_dict() for torrent in torrents]


@router.get("/domain/{site_url}", summary="站点详情", response_model=schemas.Site)
async def read_site_by_domain(
        site_url: str,
        db: AsyncSession = Depends(get_async_db),
        _: schemas.TokenPayload = Depends(verify_token)
) -> Any:
    """
    通过域名获取站点信息
    """
    domain = StringUtils.get_url_domain(site_url)
    site = await Site.async_get_by_domain(db, domain)
    if not site:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {domain} 不存在",
        )
    return site


@router.get("/statistic/{site_url}", summary="特定站点统计信息", response_model=schemas.SiteStatistic)
async def read_statistic_by_domain(
        site_url: str,
        db: AsyncSession = Depends(get_async_db),
        _: schemas.TokenPayload = Depends(verify_token)
) -> Any:
    """
    通过域名获取站点统计信息
    """
    domain = StringUtils.get_url_domain(site_url)
    sitestatistic = await SiteStatistic.async_get_by_domain(db, domain)
    if sitestatistic:
        return sitestatistic
    return schemas.SiteStatistic(domain=domain)


@router.get("/statistic", summary="所有站点统计信息", response_model=List[schemas.SiteStatistic])
async def read_statistics(
        db: AsyncSession = Depends(get_async_db),
        _: schemas.TokenPayload = Depends(verify_token)
) -> Any:
    """
    获取所有站点统计信息
    """
    return await SiteStatistic.async_list(db)


@router.get("/rss", summary="所有订阅站点", response_model=List[schemas.Site])
async def read_rss_sites(db: AsyncSession = Depends(get_async_db),
                         _: schemas.TokenPayload = Depends(verify_token)) -> List[dict]:
    """
    获取站点列表
    """
    # 选中的rss站点
    selected_sites = SystemConfigOper().get(SystemConfigKey.RssSites) or []

    # 所有站点
    all_site = await Site.async_list_order_by_pri(db)
    if not selected_sites:
        return all_site

    # 选中的rss站点
    rss_sites = [site for site in all_site if site and site.id in selected_sites]
    return rss_sites


@router.get("/auth", summary="查询认证站点", response_model=dict)
async def read_auth_sites(_: schemas.TokenPayload = Depends(verify_token)) -> dict:
    """
    获取可认证站点列表
    """
    return SitesHelper().get_authsites()


@router.post("/auth", summary="用户站点认证", response_model=schemas.Response)
def auth_site(
        auth_info: schemas.SiteAuth,
        _: User = Depends(get_current_active_superuser)
) -> Any:
    """
    用户站点认证
    """
    if not auth_info or not auth_info.site or not auth_info.params:
        return schemas.Response(success=False, message="请输入认证站点和认证参数")
    status, msg = SitesHelper().check_user(auth_info.site, auth_info.params)
    SystemConfigOper().set(SystemConfigKey.UserSiteAuthParams, auth_info.dict())
    # 认证成功后，重新初始化插件
    PluginManager().init_config()
    Scheduler().init_plugin_jobs()
    Command().init_commands()
    register_plugin_api()
    return schemas.Response(success=status, message=msg)


@router.get("/mapping", summary="获取站点域名到名称的映射", response_model=schemas.Response)
async def site_mapping(_: User = Depends(get_current_active_superuser_async)):
    """
    获取站点域名到名称的映射关系
    """
    try:
        sites = await SiteOper().async_list()
        mapping = {}
        for site in sites:
            mapping[site.domain] = site.name
        return schemas.Response(success=True, data=mapping)
    except Exception as e:
        return schemas.Response(success=False, message=f"获取映射失败：{str(e)}")


@router.get("/supporting", summary="获取支持的站点列表", response_model=dict)
async def support_sites(_: User = Depends(get_current_active_superuser_async)):
    """
    获取支持的站点列表
    """
    return SitesHelper().get_indexsites()


@router.get("/{site_id}", summary="站点详情", response_model=schemas.Site)
async def read_site(
        site_id: int,
        db: AsyncSession = Depends(get_async_db),
        _: User = Depends(get_current_active_superuser_async)
) -> Any:
    """
    通过ID获取站点信息
    """
    site = await Site.async_get(db, site_id)
    if not site:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {site_id} 不存在",
        )
    return site


@router.delete("/{site_id}", summary="删除站点", response_model=schemas.Response)
async def delete_site(
        site_id: int,
        db: AsyncSession = Depends(get_async_db),
        _: User = Depends(get_current_active_superuser_async)
) -> Any:
    """
    删除站点
    """
    await Site.async_delete(db, site_id)
    # 插件站点删除
    await eventmanager.async_send_event(EventType.SiteDeleted,
                                        {
                                            "site_id": site_id
                                        })
    return schemas.Response(success=True)
