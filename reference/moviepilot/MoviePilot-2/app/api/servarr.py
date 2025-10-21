from typing import Any, List, Annotated

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app import schemas
from app.chain.media import MediaChain
from app.chain.subscribe import SubscribeChain
from app.chain.tvdb import TvdbChain
from app.core.metainfo import MetaInfo
from app.core.security import verify_apikey
from app.db import get_db, get_async_db
from app.db.models.subscribe import Subscribe
from app.schemas import RadarrMovie, SonarrSeries
from app.schemas.types import MediaType
from version import APP_VERSION

arr_router = APIRouter(tags=['servarr'])


@arr_router.get("/system/status", summary="系统状态")
async def arr_system_status(_: Annotated[str, Depends(verify_apikey)]) -> Any:
    """
    模拟Radarr、Sonarr系统状态
    """
    return {
        "appName": "MoviePilot",
        "instanceName": "moviepilot",
        "version": APP_VERSION,
        "buildTime": "",
        "isDebug": False,
        "isProduction": True,
        "isAdmin": True,
        "isUserInteractive": True,
        "startupPath": "/app",
        "appData": "/config",
        "osName": "debian",
        "osVersion": "",
        "isNetCore": True,
        "isLinux": True,
        "isOsx": False,
        "isWindows": False,
        "isDocker": True,
        "mode": "console",
        "branch": "main",
        "databaseType": "sqLite",
        "databaseVersion": {
            "major": 0,
            "minor": 0,
            "build": 0,
            "revision": 0,
            "majorRevision": 0,
            "minorRevision": 0
        },
        "authentication": "none",
        "migrationVersion": 0,
        "urlBase": "",
        "runtimeVersion": {
            "major": 0,
            "minor": 0,
            "build": 0,
            "revision": 0,
            "majorRevision": 0,
            "minorRevision": 0
        },
        "runtimeName": "",
        "startTime": "",
        "packageVersion": "",
        "packageAuthor": "jxxghp",
        "packageUpdateMechanism": "builtIn",
        "packageUpdateMechanismMessage": ""
    }


@arr_router.get("/qualityProfile", summary="质量配置")
async def arr_qualityProfile(_: Annotated[str, Depends(verify_apikey)]) -> Any:
    """
    模拟Radarr、Sonarr质量配置
    """
    return [
        {
            "id": 1,
            "name": "默认",
            "upgradeAllowed": True,
            "cutoff": 0,
            "items": [
                {
                    "id": 0,
                    "name": "默认",
                    "quality": {
                        "id": 0,
                        "name": "默认",
                        "source": "0",
                        "resolution": 0
                    },
                    "items": [
                        "string"
                    ],
                    "allowed": True
                }
            ],
            "minFormatScore": 0,
            "cutoffFormatScore": 0,
            "formatItems": [
                {
                    "id": 0,
                    "format": 0,
                    "name": "默认",
                    "score": 0
                }
            ]
        }
    ]


@arr_router.get("/rootfolder", summary="根目录")
async def arr_rootfolder(_: Annotated[str, Depends(verify_apikey)]) -> Any:
    """
    模拟Radarr、Sonarr根目录
    """
    return [
        {
            "id": 1,
            "path": "/",
            "accessible": True,
            "freeSpace": 0,
            "unmappedFolders": []
        }
    ]


@arr_router.get("/tag", summary="标签")
async def arr_tag(_: Annotated[str, Depends(verify_apikey)]) -> Any:
    """
    模拟Radarr、Sonarr标签
    """
    return [
        {
            "id": 1,
            "label": "默认"
        }
    ]


@arr_router.get("/languageprofile", summary="语言")
async def arr_languageprofile(_: Annotated[str, Depends(verify_apikey)]) -> Any:
    """
    模拟Radarr、Sonarr语言
    """
    return [{
        "id": 1,
        "name": "默认",
        "upgradeAllowed": True,
        "cutoff": {
            "id": 1,
            "name": "默认"
        },
        "languages": [
            {
                "id": 1,
                "language": {
                    "id": 1,
                    "name": "默认"
                },
                "allowed": True
            }
        ]
    }]


@arr_router.get("/movie", summary="所有订阅电影", response_model=List[schemas.RadarrMovie])
async def arr_movies(_: Annotated[str, Depends(verify_apikey)], db: AsyncSession = Depends(get_async_db)) -> Any:
    """
    查询Rardar电影
    """
    """
    [
      {
        "id": 0,
        "title": "string",
        "originalTitle": "string",
        "originalLanguage": {
          "id": 0,
          "name": "string"
        },
        "secondaryYear": 0,
        "secondaryYearSourceId": 0,
        "sortTitle": "string",
        "sizeOnDisk": 0,
        "status": "tba",
        "overview": "string",
        "inCinemas": "2023-06-13T09:23:41.494Z",
        "physicalRelease": "2023-06-13T09:23:41.494Z",
        "digitalRelease": "2023-06-13T09:23:41.494Z",
        "physicalReleaseNote": "string",
        "images": [
          {
            "coverType": "unknown",
            "url": "string",
            "remoteUrl": "string"
          }
        ],
        "website": "string",
        "remotePoster": "string",
        "year": 0,
        "hasFile": true,
        "youTubeTrailerId": "string",
        "studio": "string",
        "path": "string",
        "qualityProfileId": 0,
        "monitored": true,
        "minimumAvailability": "tba",
        "isAvailable": true,
        "folderName": "string",
        "runtime": 0,
        "cleanTitle": "string",
        "imdbId": "string",
        "tmdbId": 0,
        "titleSlug": "string",
        "rootFolderPath": "string",
        "folder": "string",
        "certification": "string",
        "genres": [
          "string"
        ],
        "tags": [
          0
        ],
        "added": "2023-06-13T09:23:41.494Z",
        "addOptions": {
          "ignoreEpisodesWithFiles": true,
          "ignoreEpisodesWithoutFiles": true,
          "monitor": "movieOnly",
          "searchForMovie": true,
          "addMethod": "manual"
        },
        "popularity": 0
      }
    ]
    """
    # 查询所有电影订阅
    result = []
    subscribes = await Subscribe.async_list(db)
    for subscribe in subscribes:
        if subscribe.type != MediaType.MOVIE.value:
            continue
        result.append(RadarrMovie(
            id=subscribe.id,
            title=subscribe.name,
            year=subscribe.year,
            isAvailable=True,
            monitored=True,
            tmdbId=subscribe.tmdbid,
            imdbId=subscribe.imdbid,
            profileId=1,
            qualityProfileId=1,
            hasFile=False
        ))
    return result


@arr_router.get("/movie/lookup", summary="查询电影", response_model=List[schemas.RadarrMovie])
def arr_movie_lookup(term: str, _: Annotated[str, Depends(verify_apikey)], db: Session = Depends(get_db)) -> Any:
    """
    查询Rardar电影 term: `tmdb:${id}`
    存在和不存在均不能返回错误
    """
    tmdbid = term.replace("tmdb:", "")
    # 查询媒体信息
    mediainfo = MediaChain().recognize_media(mtype=MediaType.MOVIE, tmdbid=int(tmdbid))
    if not mediainfo:
        return [RadarrMovie()]
    # 查询是否已存在
    exists = MediaChain().media_exists(mediainfo=mediainfo)
    if not exists:
        # 文件不存在
        hasfile = False
    else:
        # 文件存在
        hasfile = True
    # 查询是否已订阅
    subscribes = Subscribe.get_by_tmdbid(db, int(tmdbid))
    if subscribes:
        # 订阅ID
        subid = subscribes[0].id
        # 已订阅
        monitored = True
    else:
        subid = None
        monitored = False

    return [RadarrMovie(
        id=subid,
        title=mediainfo.title,
        year=mediainfo.year,
        isAvailable=True,
        monitored=monitored,
        tmdbId=mediainfo.tmdb_id,
        imdbId=mediainfo.imdb_id,
        titleSlug=mediainfo.original_title,
        folderName=mediainfo.title_year,
        profileId=1,
        qualityProfileId=1,
        hasFile=hasfile
    )]


@arr_router.get("/movie/{mid}", summary="电影订阅详情", response_model=schemas.RadarrMovie)
async def arr_movie(mid: int, _: Annotated[str, Depends(verify_apikey)],
                    db: AsyncSession = Depends(get_async_db)) -> Any:
    """
    查询Rardar电影订阅
    """
    subscribe = await Subscribe.async_get(db, mid)
    if subscribe:
        return RadarrMovie(
            id=subscribe.id,
            title=subscribe.name,
            year=subscribe.year,
            isAvailable=True,
            monitored=True,
            tmdbId=subscribe.tmdbid,
            imdbId=subscribe.imdbid,
            profileId=1,
            qualityProfileId=1,
            hasFile=False
        )
    else:
        raise HTTPException(
            status_code=404,
            detail="未找到该电影！"
        )


@arr_router.post("/movie", summary="新增电影订阅")
async def arr_add_movie(_: Annotated[str, Depends(verify_apikey)],
                        movie: RadarrMovie,
                        db: AsyncSession = Depends(get_async_db)
                        ) -> Any:
    """
    新增Rardar电影订阅
    """
    # 检查订阅是否已存在
    subscribe = await Subscribe.async_get_by_tmdbid(db, movie.tmdbId)
    if subscribe:
        return {
            "id": subscribe.id
        }
    # 添加订阅
    sid, message = await SubscribeChain().async_add(title=movie.title,
                                                    year=movie.year,
                                                    mtype=MediaType.MOVIE,
                                                    tmdbid=movie.tmdbId,
                                                    username="Seerr")
    if sid:
        return {
            "id": sid
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"添加订阅失败：{message}"
        )


@arr_router.delete("/movie/{mid}", summary="删除电影订阅", response_model=schemas.Response)
async def arr_remove_movie(mid: int, _: Annotated[str, Depends(verify_apikey)],
                           db: AsyncSession = Depends(get_async_db)) -> Any:
    """
    删除Rardar电影订阅
    """
    subscribe = await Subscribe.async_get(db, mid)
    if subscribe:
        await subscribe.async_delete(db, mid)
        return schemas.Response(success=True)
    else:
        raise HTTPException(
            status_code=404,
            detail="未找到该电影！"
        )


@arr_router.get("/series", summary="所有剧集", response_model=List[schemas.SonarrSeries])
async def arr_series(_: Annotated[str, Depends(verify_apikey)], db: AsyncSession = Depends(get_async_db)) -> Any:
    """
    查询Sonarr剧集
    """
    """
    [
      {
        "id": 0,
        "title": "string",
        "sortTitle": "string",
        "status": "continuing",
        "ended": true,
        "profileName": "string",
        "overview": "string",
        "nextAiring": "2023-06-13T09:08:17.624Z",
        "previousAiring": "2023-06-13T09:08:17.624Z",
        "network": "string",
        "airTime": "string",
        "images": [
          {
            "coverType": "unknown",
            "url": "string",
            "remoteUrl": "string"
          }
        ],
        "originalLanguage": {
          "id": 0,
          "name": "string"
        },
        "remotePoster": "string",
        "seasons": [
          {
            "seasonNumber": 0,
            "monitored": true,
            "statistics": {
              "nextAiring": "2023-06-13T09:08:17.624Z",
              "previousAiring": "2023-06-13T09:08:17.624Z",
              "episodeFileCount": 0,
              "episodeCount": 0,
              "totalEpisodeCount": 0,
              "sizeOnDisk": 0,
              "releaseGroups": [
                "string"
              ],
              "percentOfEpisodes": 0
            },
            "images": [
              {
                "coverType": "unknown",
                "url": "string",
                "remoteUrl": "string"
              }
            ]
          }
        ],
        "year": 0,
        "path": "string",
        "qualityProfileId": 0,
        "seasonFolder": true,
        "monitored": true,
        "useSceneNumbering": true,
        "runtime": 0,
        "tvdbId": 0,
        "tvRageId": 0,
        "tvMazeId": 0,
        "firstAired": "2023-06-13T09:08:17.624Z",
        "seriesType": "standard",
        "cleanTitle": "string",
        "imdbId": "string",
        "titleSlug": "string",
        "rootFolderPath": "string",
        "folder": "string",
        "certification": "string",
        "genres": [
          "string"
        ],
        "tags": [
          0
        ],
        "added": "2023-06-13T09:08:17.624Z",
        "addOptions": {
          "ignoreEpisodesWithFiles": true,
          "ignoreEpisodesWithoutFiles": true,
          "monitor": "unknown",
          "searchForMissingEpisodes": true,
          "searchForCutoffUnmetEpisodes": true
        },
        "ratings": {
          "votes": 0,
          "value": 0
        },
        "statistics": {
          "seasonCount": 0,
          "episodeFileCount": 0,
          "episodeCount": 0,
          "totalEpisodeCount": 0,
          "sizeOnDisk": 0,
          "releaseGroups": [
            "string"
          ],
          "percentOfEpisodes": 0
        },
        "episodesChanged": true
      }
    ]
    """
    # 查询所有电视剧订阅
    result = []
    subscribes = await Subscribe.async_list(db)
    for subscribe in subscribes:
        if subscribe.type != MediaType.TV.value:
            continue
        result.append(SonarrSeries(
            id=subscribe.id,
            title=subscribe.name,
            seasonCount=1,
            seasons=[{
                "seasonNumber": subscribe.season,
                "monitored": True,
            }],
            remotePoster=subscribe.poster,
            year=subscribe.year,
            tmdbId=subscribe.tmdbid,
            tvdbId=subscribe.tvdbid,
            imdbId=subscribe.imdbid,
            profileId=1,
            languageProfileId=1,
            qualityProfileId=1,
            isAvailable=True,
            monitored=True,
            hasFile=False
        ))
    return result


@arr_router.get("/series/lookup", summary="查询剧集")
def arr_series_lookup(term: str, _: Annotated[str, Depends(verify_apikey)], db: Session = Depends(get_db)) -> Any:
    """
    查询Sonarr剧集 term: `tvdb:${id}` title
    """
    # 季信息
    seas: List[int] = []
    # tvdbid 列表
    tvdbids: List[int] = []
    # 获取TVDBID
    if not term.startswith("tvdb:"):
        title = term.replace("+", " ")
        tvdbids = TvdbChain().get_tvdbid_by_name(title=title)
    else:
        tvdbid = int(term.replace("tvdb:", ""))
        tvdbids.append(tvdbid)

    sonarr_series_list = []
    for tvdbid in tvdbids:
        # 查询TVDB信息
        tvdbinfo = MediaChain().tvdb_info(tvdbid=tvdbid)
        if not tvdbinfo:
            continue

        # 季信息(只取默认季类型，排除特别季)
        sea_num = len([season for season in tvdbinfo.get('seasons') if
                       season['type']['id'] == tvdbinfo.get('defaultSeasonType') and season['number'] > 0])
        if sea_num:
            seas = list(range(1, int(sea_num) + 1))

        # 根据TVDB查询媒体信息
        mediainfo = MediaChain().recognize_media(meta=MetaInfo(tvdbinfo.get('name')),
                                                 mtype=MediaType.TV)
        if not mediainfo:
            continue
        # 查询是否存在
        exists = MediaChain().media_exists(mediainfo)
        if exists:
            hasfile = True
        else:
            hasfile = False

        # 查询订阅信息
        seasons: List[dict] = []
        subscribes = Subscribe.get_by_tmdbid(db, mediainfo.tmdb_id)
        if subscribes:
            # 已监控
            monitored = True
            # 已监控季
            sub_seas = [sub.season for sub in subscribes]
            for sea in seas:
                if sea in sub_seas:
                    seasons.append({
                        "seasonNumber": sea,
                        "monitored": True,
                    })
                else:
                    seasons.append({
                        "seasonNumber": sea,
                        "monitored": False,
                    })
            subid = subscribes[-1].id
        else:
            subid = None
            monitored = False
            for sea in seas:
                seasons.append({
                    "seasonNumber": sea,
                    "monitored": False,
                })
        sonarr_series = SonarrSeries(
            id=subid,
            title=mediainfo.title,
            seasonCount=len(seasons),
            seasons=seasons,
            remotePoster=mediainfo.get_poster_image(),
            year=mediainfo.year,
            tmdbId=mediainfo.tmdb_id,
            tvdbId=tvdbid,
            imdbId=mediainfo.imdb_id,
            profileId=1,
            languageProfileId=1,
            monitored=monitored,
            hasFile=hasfile,
        )
        sonarr_series_list.append(sonarr_series)

    return sonarr_series_list if sonarr_series_list else [SonarrSeries()]


@arr_router.get("/series/{tid}", summary="剧集详情")
async def arr_serie(tid: int, _: Annotated[str, Depends(verify_apikey)],
                    db: AsyncSession = Depends(get_async_db)) -> Any:
    """
    查询Sonarr剧集
    """
    subscribe = await Subscribe.async_get(db, tid)
    if subscribe:
        return SonarrSeries(
            id=subscribe.id,
            title=subscribe.name,
            seasonCount=1,
            seasons=[{
                "seasonNumber": subscribe.season,
                "monitored": True,
            }],
            year=subscribe.year,
            remotePoster=subscribe.poster,
            tmdbId=subscribe.tmdbid,
            tvdbId=subscribe.tvdbid,
            imdbId=subscribe.imdbid,
            profileId=1,
            languageProfileId=1,
            qualityProfileId=1,
            isAvailable=True,
            monitored=True,
            hasFile=False
        )
    else:
        raise HTTPException(
            status_code=404,
            detail="未找到该电视剧！"
        )


@arr_router.post("/series", summary="新增剧集订阅")
async def arr_add_series(tv: schemas.SonarrSeries,
                         _: Annotated[str, Depends(verify_apikey)],
                         db: AsyncSession = Depends(get_async_db)) -> Any:
    """
    新增Sonarr剧集订阅
    """
    # 检查订阅是否存在
    left_seasons = []
    for season in tv.seasons:
        subscribe = await Subscribe.async_get_by_tmdbid(db, tmdbid=tv.tmdbId,
                                                        season=season.get("seasonNumber"))
        if subscribe:
            continue
        left_seasons.append(season)
    # 全部已存在订阅
    if not left_seasons:
        return {
            "id": 1
        }
    # 剩下的添加订阅
    sid = 0
    message = ""
    for season in left_seasons:
        if not season.get("monitored"):
            continue
        sid, message = await SubscribeChain().async_add(title=tv.title,
                                                        year=tv.year,
                                                        season=season.get("seasonNumber"),
                                                        tmdbid=tv.tmdbId,
                                                        mtype=MediaType.TV,
                                                        username="Seerr")

    if sid:
        return {
            "id": sid
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"添加订阅失败：{message}"
        )


@arr_router.put("/series", summary="更新剧集订阅")
async def arr_update_series(tv: schemas.SonarrSeries, _: Annotated[str, Depends(verify_apikey)]) -> Any:
    """
    更新Sonarr剧集订阅
    """
    return await arr_add_series(tv)


@arr_router.delete("/series/{tid}", summary="删除剧集订阅")
async def arr_remove_series(tid: int, _: Annotated[str, Depends(verify_apikey)],
                            db: AsyncSession = Depends(get_async_db)) -> Any:
    """
    删除Sonarr剧集订阅
    """
    subscribe = await Subscribe.async_get(db, tid)
    if subscribe:
        await subscribe.async_delete(db, tid)
        return schemas.Response(success=True)
    else:
        raise HTTPException(
            status_code=404,
            detail="未找到该电视剧！"
        )
