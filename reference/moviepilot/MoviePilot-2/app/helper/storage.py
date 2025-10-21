from typing import List, Optional

from app import schemas
from app.db.systemconfig_oper import SystemConfigOper
from app.schemas.types import SystemConfigKey


class StorageHelper:
    """
    存储帮助类
    """

    @staticmethod
    def get_storagies() -> List[schemas.StorageConf]:
        """
        获取所有存储设置
        """
        storage_confs: List[dict] = SystemConfigOper().get(SystemConfigKey.Storages)
        if not storage_confs:
            return []
        return [schemas.StorageConf(**s) for s in storage_confs]

    def get_storage(self, storage: str) -> Optional[schemas.StorageConf]:
        """
        获取指定存储配置
        """
        storagies = self.get_storagies()
        for s in storagies:
            if s.type == storage:
                return s
        return None

    def set_storage(self, storage: str, conf: dict):
        """
        设置存储配置
        """
        storagies = self.get_storagies()
        if not storagies:
            storagies = [
                schemas.StorageConf(
                    type=storage,
                    config=conf
                )
            ]
        else:
            for s in storagies:
                if s.type == storage:
                    s.config = conf
                    break
        SystemConfigOper().set(SystemConfigKey.Storages, [s.dict() for s in storagies])

    def add_storage(self, storage: str, name: str, conf: dict):
        """
        添加存储配置
        """
        storagies = self.get_storagies()
        if not storagies:
            storagies = [
                schemas.StorageConf(
                    type=storage,
                    name=name,
                    config=conf
                )
            ]
        else:
            storagies.append(schemas.StorageConf(
                type=storage,
                name=name,
                config=conf
            ))
        SystemConfigOper().set(SystemConfigKey.Storages, [s.dict() for s in storagies])

    def reset_storage(self, storage: str):
        """
        重置存储配置
        """
        storagies = self.get_storagies()
        for s in storagies:
            if s.type == storage:
                s.config = {}
                break
        SystemConfigOper().set(SystemConfigKey.Storages, [s.dict() for s in storagies])
