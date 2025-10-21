import traceback
from typing import Generator, Optional, Tuple, Any, Union, List

from app.core.config import settings
from app.core.event import eventmanager
from app.helper.module import ModuleHelper
from app.log import logger
from app.schemas.types import EventType, ModuleType, DownloaderType, MediaServerType, MessageChannel, StorageSchema, \
    OtherModulesType
from app.utils.object import ObjectUtils
from app.utils.singleton import Singleton


class ModuleManager(metaclass=Singleton):
    """
    模块管理器
    """

    # 子模块类型集合
    SubType = Union[DownloaderType, MediaServerType, MessageChannel, StorageSchema, OtherModulesType]

    def __init__(self):
        # 模块列表
        self._modules: dict = {}
        # 运行态模块列表
        self._running_modules: dict = {}
        self.load_modules()

    def load_modules(self):
        """
        加载所有模块
        """
        # 扫描模块目录
        modules = ModuleHelper.load(
            "app.modules",
            filter_func=lambda _, obj: hasattr(obj, 'init_module') and hasattr(obj, 'init_setting')
        )
        self._running_modules = {}
        self._modules = {}
        for module in modules:
            module_id = module.__name__
            self._modules[module_id] = module
            try:
                # 生成实例
                _module = module()
                # 初始化模块
                if self.check_setting(_module.init_setting()):
                    # 通过模板开关控制加载
                    _module.init_module()
                    self._running_modules[module_id] = _module
                    logger.debug(f"Moudle Loaded：{module_id}")
            except Exception as err:
                logger.error(f"Load Moudle Error：{module_id}，{str(err)} - {traceback.format_exc()}", exc_info=True)

    def stop(self):
        """
        停止所有模块
        """
        logger.info("正在停止所有模块...")
        for module_id, module in self._running_modules.items():
            if hasattr(module, "stop"):
                try:
                    module.stop()
                    logger.debug(f"Moudle Stoped：{module_id}")
                except Exception as err:
                    logger.error(f"Stop Moudle Error：{module_id}，{str(err)} - {traceback.format_exc()}", exc_info=True)
        logger.info("所有模块停止完成")

    def reload(self):
        """
        重新加载所有模块
        """
        self.stop()
        self.load_modules()
        eventmanager.send_event(etype=EventType.ModuleReload, data={})

    def test(self, modleid: str) -> Tuple[bool, str]:
        """
        测试模块
        """
        if modleid not in self._running_modules:
            return False, ""
        module = self._running_modules[modleid]
        if hasattr(module, "test") \
                and ObjectUtils.check_method(getattr(module, "test")):
            result = module.test()
            if not result:
                return False, ""
            return result
        return True, "模块不支持测试"

    @staticmethod
    def check_setting(setting: Optional[tuple]) -> bool:
        """
        检查开关是否己打开，开关使用,分隔多个值，符合其中即代表开启
        """
        if not setting:
            return True
        switch, value = setting
        option = getattr(settings, switch)
        if not option:
            return False
        if option and value is True:
            return True
        if value in option:
            return True
        return False

    def get_running_module(self, module_id: str) -> Any:
        """
        根据模块id获取模块运行实例
        """
        if not module_id:
            return None
        if not self._running_modules:
            return None
        return self._running_modules.get(module_id)

    def get_running_modules(self, method: str) -> Generator:
        """
        获取实现了同一方法的模块列表
        """
        if not self._running_modules:
            return
        for _, module in self._running_modules.items():
            if hasattr(module, method) \
                    and ObjectUtils.check_method(getattr(module, method)):
                yield module

    def get_running_type_modules(self, module_type: ModuleType) -> Generator:
        """
        获取指定类型的模块列表
        """
        if not self._running_modules:
            return
        for _, module in self._running_modules.items():
            if hasattr(module, 'get_type') \
                    and module.get_type() == module_type:
                yield module

    def get_running_subtype_module(self, module_subtype: SubType) -> Generator:
        """
        获取指定子类型的模块
        """
        if not self._running_modules:
            return
        for _, module in self._running_modules.items():
            if hasattr(module, 'get_subtype') \
                    and module.get_subtype() == module_subtype:
                yield module

    def get_module(self, module_id: str) -> Any:
        """
        根据模块id获取模块
        """
        if not module_id:
            return None
        if not self._modules:
            return None
        return self._modules.get(module_id)

    def get_modules(self) -> dict:
        """
        获取模块列表
        """
        return self._modules

    def get_module_ids(self) -> List[str]:
        """
        获取模块id列表
        """
        return list(self._modules.keys())
