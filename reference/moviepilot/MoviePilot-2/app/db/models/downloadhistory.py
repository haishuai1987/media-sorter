import time
from typing import Optional

from sqlalchemy import Column, Integer, String, JSON, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db import db_query, db_update, get_id_column, Base, async_db_query


class DownloadHistory(Base):
    """
    下载历史记录
    """
    id = get_id_column()
    # 保存路径
    path = Column(String, nullable=False, index=True)
    # 类型 电影/电视剧
    type = Column(String, nullable=False)
    # 标题
    title = Column(String, nullable=False)
    # 年份
    year = Column(String)
    tmdbid = Column(Integer, index=True)
    imdbid = Column(String)
    tvdbid = Column(Integer)
    doubanid = Column(String)
    # Sxx
    seasons = Column(String)
    # Exx
    episodes = Column(String)
    # 海报
    image = Column(String)
    # 下载器
    downloader = Column(String)
    # 下载任务Hash
    download_hash = Column(String, index=True)
    # 种子名称
    torrent_name = Column(String)
    # 种子描述
    torrent_description = Column(String)
    # 种子站点
    torrent_site = Column(String)
    # 下载用户
    userid = Column(String)
    # 下载用户名/插件名
    username = Column(String)
    # 下载渠道
    channel = Column(String)
    # 创建时间
    date = Column(String)
    # 附加信息
    note = Column(JSON)
    # 自定义媒体类别
    media_category = Column(String)
    # 剧集组
    episode_group = Column(String)

    @classmethod
    @db_query
    def get_by_hash(cls, db: Session, download_hash: str):
        return db.query(DownloadHistory).filter(DownloadHistory.download_hash == download_hash).order_by(
            DownloadHistory.date.desc()
        ).first()

    @classmethod
    @db_query
    def get_by_mediaid(cls, db: Session, tmdbid: int, doubanid: str):
        if tmdbid:
            return db.query(DownloadHistory).filter(DownloadHistory.tmdbid == tmdbid).all()
        elif doubanid:
            return db.query(DownloadHistory).filter(DownloadHistory.doubanid == doubanid).all()
        return []

    @classmethod
    @db_query
    def list_by_page(cls, db: Session, page: Optional[int] = 1, count: Optional[int] = 30):
        return db.query(DownloadHistory).offset((page - 1) * count).limit(count).all()

    @classmethod
    @async_db_query
    async def async_list_by_page(cls, db: AsyncSession, page: Optional[int] = 1, count: Optional[int] = 30):
        result = await db.execute(
            select(cls).offset((page - 1) * count).limit(count)
        )
        return result.scalars().all()

    @classmethod
    @db_query
    def get_by_path(cls, db: Session, path: str):
        return db.query(DownloadHistory).filter(DownloadHistory.path == path).first()

    @classmethod
    @db_query
    def get_last_by(cls, db: Session, mtype: Optional[str] = None, title: Optional[str] = None,
                    year: Optional[str] = None, season: Optional[str] = None,
                    episode: Optional[str] = None, tmdbid: Optional[int] = None):
        """
        据tmdbid、season、season_episode查询下载记录
        tmdbid + mtype 或 title + year
        """
        # TMDBID + 类型
        if tmdbid and mtype:
            # 电视剧某季某集
            if season and episode:
                return db.query(DownloadHistory).filter(DownloadHistory.tmdbid == tmdbid,
                                                        DownloadHistory.type == mtype,
                                                        DownloadHistory.seasons == season,
                                                        DownloadHistory.episodes == episode).order_by(
                    DownloadHistory.id.desc()).all()
            # 电视剧某季
            elif season:
                return db.query(DownloadHistory).filter(DownloadHistory.tmdbid == tmdbid,
                                                        DownloadHistory.type == mtype,
                                                        DownloadHistory.seasons == season).order_by(
                    DownloadHistory.id.desc()).all()
            else:
                # 电视剧所有季集/电影
                return db.query(DownloadHistory).filter(DownloadHistory.tmdbid == tmdbid,
                                                        DownloadHistory.type == mtype).order_by(
                    DownloadHistory.id.desc()).all()
        # 标题 + 年份
        elif title and year:
            # 电视剧某季某集
            if season and episode:
                return db.query(DownloadHistory).filter(DownloadHistory.title == title,
                                                        DownloadHistory.year == year,
                                                        DownloadHistory.seasons == season,
                                                        DownloadHistory.episodes == episode).order_by(
                    DownloadHistory.id.desc()).all()
            # 电视剧某季
            elif season:
                return db.query(DownloadHistory).filter(DownloadHistory.title == title,
                                                        DownloadHistory.year == year,
                                                        DownloadHistory.seasons == season).order_by(
                    DownloadHistory.id.desc()).all()
            else:
                # 电视剧所有季集/电影
                return db.query(DownloadHistory).filter(DownloadHistory.title == title,
                                                        DownloadHistory.year == year).order_by(
                    DownloadHistory.id.desc()).all()

        return []

    @classmethod
    @db_query
    def list_by_user_date(cls, db: Session, date: str, username: Optional[str] = None):
        """
        查询某用户某时间之后的下载历史
        """
        if username:
            return db.query(DownloadHistory).filter(DownloadHistory.date < date,
                                                    DownloadHistory.username == username).order_by(
                DownloadHistory.id.desc()).all()
        else:
            return db.query(DownloadHistory).filter(DownloadHistory.date < date).order_by(
                DownloadHistory.id.desc()).all()

    @classmethod
    @db_query
    def list_by_date(cls, db: Session, date: str, type: str, tmdbid: str, seasons: Optional[str] = None):
        """
        查询某时间之后的下载历史
        """
        if seasons:
            return db.query(DownloadHistory).filter(DownloadHistory.date > date,
                                                    DownloadHistory.type == type,
                                                    DownloadHistory.tmdbid == tmdbid,
                                                    DownloadHistory.seasons == seasons).order_by(
                DownloadHistory.id.desc()).all()
        else:
            return db.query(DownloadHistory).filter(DownloadHistory.date > date,
                                                    DownloadHistory.type == type,
                                                    DownloadHistory.tmdbid == tmdbid).order_by(
                DownloadHistory.id.desc()).all()

    @classmethod
    @db_query
    def list_by_type(cls, db: Session, mtype: str, days: int):
        return db.query(DownloadHistory) \
            .filter(DownloadHistory.type == mtype,
                    DownloadHistory.date >= time.strftime("%Y-%m-%d %H:%M:%S",
                                                          time.localtime(time.time() - 86400 * int(days)))
                    ).all()


class DownloadFiles(Base):
    """
    下载文件记录
    """
    id = get_id_column()
    # 下载器
    downloader = Column(String)
    # 下载任务Hash
    download_hash = Column(String, index=True)
    # 完整路径
    fullpath = Column(String, index=True)
    # 保存路径
    savepath = Column(String, index=True)
    # 文件相对路径/名称
    filepath = Column(String)
    # 种子名称
    torrentname = Column(String)
    # 状态 0-已删除 1-正常
    state = Column(Integer, nullable=False, default=1)

    @classmethod
    @db_query
    def get_by_hash(cls, db: Session, download_hash: str, state: Optional[int] = None):
        if state:
            return db.query(cls).filter(cls.download_hash == download_hash,
                                        cls.state == state).all()
        else:
            return db.query(cls).filter(cls.download_hash == download_hash).all()

    @classmethod
    @db_query
    def get_by_fullpath(cls, db: Session, fullpath: str, all_files: bool = False):
        if not all_files:
            return db.query(cls).filter(cls.fullpath == fullpath).order_by(
                cls.id.desc()).first()
        else:
            return db.query(cls).filter(cls.fullpath == fullpath).order_by(
                cls.id.desc()).all()

    @classmethod
    @db_query
    def get_by_savepath(cls, db: Session, savepath: str):
        return db.query(cls).filter(cls.savepath == savepath).all()

    @classmethod
    @db_update
    def delete_by_fullpath(cls, db: Session, fullpath: str):
        db.query(cls).filter(cls.fullpath == fullpath,
                             cls.state == 1).update(
            {
                "state": 0
            }
        )
