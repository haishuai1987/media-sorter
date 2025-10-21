import ast
import asyncio
import concurrent
import concurrent.futures
import importlib.util
import inspect
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Type, Union, Callable, Tuple

from fastapi import HTTPException
from starlette import status
from watchfiles import watch

from app import schemas
from app.core.cache import cached
from app.core.config import settings
from app.core.event import eventmanager, Event
from app.db.plugindata_oper import PluginDataOper
from app.db.systemconfig_oper import SystemConfigOper
from app.helper.plugin import PluginHelper
from app.helper.sites import SitesHelper  # noqa
from app.log import logger
from app.schemas.types import EventType, SystemConfigKey
from app.utils.crypto import RSAUtils
from app.utils.object import ObjectUtils
from app.utils.singleton import Singleton
from app.utils.string import StringUtils
from app.utils.system import SystemUtils


class PluginManager(metaclass=Singleton):
    """
    插件管理器
    """

    def __init__(self):
        # 插件列表
        self._plugins: dict = {}
        # 运行态插件列表
        self._running_plugins: dict = {}
        # 配置Key
        self._config_key: str = "plugin.%s"
        # 监控线程
        self._monitor_thread: Optional[threading.Thread] = None
        # 监控停止事件
        self._stop_monitor_event = threading.Event()
        # 开发者模式监测插件修改
        if settings.DEV or settings.PLUGIN_AUTO_RELOAD:
            self.__start_monitor()

    def init_config(self):
        # 停止已有插件
        self.stop()
        # 启动插件
        self.start()

    def start(self, pid: Optional[str] = None):
        """
        启动加载插件
        :param pid: 插件ID，为空加载所有插件
        """

        def check_module(module: Any):
            """
            检查模块
            """
            if not hasattr(module, 'init_plugin') or not hasattr(module, "plugin_name"):
                return False
            return True

        # 已安装插件
        installed_plugins = SystemConfigOper().get(SystemConfigKey.UserInstalledPlugins) or []
        # 扫描插件目录，只加载符合条件的插件
        plugins = self._load_selective_plugins(pid, installed_plugins, check_module)
        # 排序
        plugins.sort(key=lambda x: x.plugin_order if hasattr(x, "plugin_order") else 0)
        for plugin in plugins:
            plugin_id = plugin.__name__
            if pid and plugin_id != pid:
                continue
            try:
                # 判断插件是否满足认证要求，如不满足则不进行实例化
                if not self.__set_and_check_auth_level(plugin=plugin):
                    # 如果是插件热更新实例，这里则进行替换
                    if plugin_id in self._plugins:
                        self._plugins[plugin_id] = plugin
                    continue
                # 存储Class
                self._plugins[plugin_id] = plugin
                # 生成实例
                plugin_obj = plugin()
                # 生效插件配置
                plugin_obj.init_plugin(self.get_plugin_config(plugin_id))
                # 存储运行实例
                self._running_plugins[plugin_id] = plugin_obj
                logger.info(f"加载插件：{plugin_id} 版本：{plugin_obj.plugin_version}")
                # 启用的插件才设置事件注册状态可用
                if plugin_obj.get_state():
                    eventmanager.enable_event_handler(plugin)
                else:
                    eventmanager.disable_event_handler(plugin)
            except Exception as err:
                logger.error(f"加载插件 {plugin_id} 出错：{str(err)} - {traceback.format_exc()}")

    def init_plugin(self, plugin_id: str, conf: dict):
        """
        初始化插件
        :param plugin_id: 插件ID
        :param conf: 插件配置
        """
        plugin = self._running_plugins.get(plugin_id)
        if not plugin:
            return
        # 初始化插件
        plugin.init_plugin(conf)
        # 检查插件状态并启用/禁用事件处理器
        if plugin.get_state():
            # 启用插件类的事件处理器
            eventmanager.enable_event_handler(type(plugin))
        else:
            # 禁用插件类的事件处理器
            eventmanager.disable_event_handler(type(plugin))

    def stop(self, pid: Optional[str] = None):
        """
        停止插件服务
        :param pid: 插件ID，为空停止所有插件
        """
        # 停止插件
        if pid:
            logger.info(f"正在停止插件 {pid}...")
            plugin_obj = self._running_plugins.get(pid)
            if not plugin_obj:
                logger.debug(f"插件 {pid} 不存在或未加载")
                return
            plugins = {pid: plugin_obj}
        else:
            logger.info("正在停止所有插件...")
            plugins = self._running_plugins
        for plugin_id, plugin in plugins.items():
            eventmanager.disable_event_handler(type(plugin))
            self.__stop_plugin(plugin)
        # 清空对像
        if pid:
            # 清空指定插件
            self._plugins.pop(pid, None)
            self._running_plugins.pop(pid, None)
            # 清除插件模块缓存，包括所有子模块
            self._clear_plugin_modules(pid)
        else:
            # 清空
            self._plugins = {}
            self._running_plugins = {}
            # 清除所有插件模块缓存
            self._clear_plugin_modules()
        logger.info("插件停止完成")

    @staticmethod
    def _load_selective_plugins(pid: Optional[str], installed_plugins: List[str],
                                check_module_func: Callable) -> List[Any]:
        """
        选择性加载插件，只import符合条件的插件
        :param pid: 指定插件ID，为空则加载所有已安装插件
        :param installed_plugins: 已安装插件列表
        :param check_module_func: 模块检查函数
        :return: 插件类列表
        """
        import importlib

        plugins = []
        plugins_dir = settings.ROOT_PATH / "app" / "plugins"

        if not plugins_dir.exists():
            logger.warning(f"插件目录不存在：{plugins_dir}")
            return plugins

        # 确定需要加载的插件目录名称列表
        if pid:
            # 加载指定插件
            target_plugins = [pid.lower()]
        else:
            # 加载已安装插件
            target_plugins = [plugin_id.lower() for plugin_id in installed_plugins]

        if not target_plugins:
            logger.debug("没有需要加载的插件")
            return plugins

        # 扫描plugins目录
        _loaded_modules = set()
        for plugin_dir in plugins_dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith('_'):
                continue

            # 检查是否是需要加载的插件
            if plugin_dir.name not in target_plugins:
                logger.debug(f"跳过插件目录：{plugin_dir.name}（不在加载列表中）")
                continue

            # 检查__init__.py是否存在
            init_file = plugin_dir / "__init__.py"
            if not init_file.exists():
                logger.debug(f"跳过插件目录：{plugin_dir.name}（缺少__init__.py）")
                continue

            try:
                # 构建模块名
                module_name = f"app.plugins.{plugin_dir.name}"
                logger.debug(f"正在导入插件模块：{module_name}")

                # 导入模块
                module = importlib.import_module(module_name)

                # 检查模块中的类
                for name, obj in module.__dict__.items():
                    if name.startswith('_') or not isinstance(obj, type):
                        continue
                    if name in _loaded_modules:
                        continue
                    if check_module_func(obj):
                        _loaded_modules.add(name)
                        plugins.append(obj)
                        logger.debug(f"找到符合条件的插件类：{name}")
                        break

            except Exception as err:
                logger.error(f"加载插件 {plugin_dir.name} 失败：{str(err)} - {traceback.format_exc()}")

        return plugins

    @property
    def running_plugins(self) -> Dict[str, Any]:
        """
        获取运行态插件列表
        :return: 运行态插件列表
        """
        return self._running_plugins

    @property
    def plugins(self) -> Dict[str, Any]:
        """
        获取插件列表
        :return: 插件列表
        """
        return self._plugins

    @eventmanager.register(EventType.ConfigChanged)
    def handle_config_changed(self, event: Event):
        """
        处理配置变更事件
        :param event: 事件对象
        """
        if not event:
            return
        event_data: schemas.ConfigChangeEventData = event.event_data
        if event_data.key not in ['DEV', 'PLUGIN_AUTO_RELOAD']:
            return
        logger.info("配置变更，重新加载插件文件修改监测...")
        self.reload_monitor()

    def reload_monitor(self):
        """
        重新加载插件文件修改监测
        """
        if settings.DEV or settings.PLUGIN_AUTO_RELOAD:
            # 先关闭已有监测，再重新启动
            self.stop_monitor()
            self.__start_monitor()
        else:
            self.stop_monitor()

    def __start_monitor(self):
        """
        启用监测插件文件修改监测
        """
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.info("插件文件修改监测已经在运行中...")
            return

        logger.info("开始监测插件文件修改...")

        # 在启动新线程之前，确保停止事件是清除状态
        self._stop_monitor_event.clear()

        # 创建并启动监控线程
        self._monitor_thread = threading.Thread(
            target=self._run_file_watcher,
            daemon=True
        )
        self._monitor_thread.start()

    def stop_monitor(self):
        """
        停止监测插件文件修改监测
        """
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.info("正在停止插件文件修改监测...")
            self._stop_monitor_event.set()
            self._monitor_thread.join(timeout=5)
            if self._monitor_thread.is_alive():
                logger.warning("插件文件修改监测线程在5秒内未能正常停止。")
            self._monitor_thread = None
            logger.info("插件文件修改监测停止完成")
        else:
            logger.info("未启用插件文件修改监测，无需停止")

    def _run_file_watcher(self):
        """
        运行 watchfiles 监视器的主循环。
        """
        # 监视插件目录
        plugins_path = str(settings.ROOT_PATH / "app" / "plugins")
        logger.info(">>> 监控线程已启动，准备进入watch循环...")
        # 使用 watchfiles 监视目录变化，并响应变化事件
        # Todo: yield_on_timeout = True 时，每秒检查停止事件，会返回空集合；后续可以考虑用来做心跳之类的功能？
        for changes in watch(plugins_path, stop_event=self._stop_monitor_event, rust_timeout=1000,
                             yield_on_timeout=True):
            # 如果收到停止事件，退出循环
            if not changes:
                continue

            # 处理变化事件
            plugins_to_reload = set()
            for _change_type, path_str in changes:
                event_path = Path(path_str)

                # 跳过非 .py 文件以及 pycache 目录中的文件
                if not event_path.name.endswith(".py") or "__pycache__" in event_path.parts:
                    continue

                # 解析插件ID
                pid = self._get_plugin_id_from_path(event_path)
                # 跳过无效插件文件
                if pid:
                    # 收集需要重载的插件ID，自动去重，避免重复重载
                    plugins_to_reload.add(pid)

            # 触发重载
            if plugins_to_reload:
                logger.info(f"检测到插件文件变化，准备重载: {list(plugins_to_reload)}")
                for pid in plugins_to_reload:
                    try:
                        self.reload_plugin(pid)
                    except Exception as e:
                        logger.error(f"插件 {pid} 热重载失败: {e}", exc_info=True)

    @staticmethod
    def _get_plugin_id_from_path(event_path: Path) -> Optional[str]:
        """
        根据文件路径解析出插件的ID。
        :param event_path: 被修改文件的 Path 对象。
        :return: 插件ID字符串，如果不是有效插件文件则返回 None。
        """
        try:
            plugins_root = settings.ROOT_PATH / "app" / "plugins"
            # 确保修改的文件在 plugins 目录下
            if not event_path.is_relative_to(plugins_root):
                return None

            try:
                plugin_dir_name = event_path.relative_to(plugins_root).parts[0]
                plugin_dir = plugins_root / plugin_dir_name
            except (ValueError, IndexError):
                return None

            init_file = plugin_dir / "__init__.py"
            if not init_file.exists():
                return None

            # 读取 __init__.py 文件，查找插件主类名
            with open(init_file, "r", encoding="utf-8") as f:
                source_code = f.read()

            tree = ast.parse(source_code)

            # 遍历AST，查找继承自 _PluginBase 的类
            for node in ast.walk(tree):
                # 检查节点是否为类定义
                if isinstance(node, ast.ClassDef):
                    # 遍历该类的所有基类
                    for base in node.bases:
                        # 检查基类是否是我们寻找的 _PluginBase
                        # ast.Name 用于处理简单的基类名
                        if isinstance(base, ast.Name) and base.id == '_PluginBase':
                            # 返回这个类的名字
                            return node.name

            return None
        except Exception as e:
            logger.error(f"从路径解析插件ID时出错: {e}")
            return None

    @staticmethod
    def __stop_plugin(plugin: Any):
        """
        停止插件
        :param plugin: 插件实例
        """
        try:
            # 关闭数据库
            if hasattr(plugin, "close"):
                plugin.close()
            # 关闭插件
            if hasattr(plugin, "stop_service"):
                plugin.stop_service()
        except Exception as e:
            logger.warn(f"停止插件 {plugin.get_name()} 时发生错误: {str(e)}")

    def remove_plugin(self, plugin_id: str):
        """
        从内存中移除一个插件
        :param plugin_id: 插件ID
        """
        self.stop(plugin_id)

    def reload_plugin(self, plugin_id: str):
        """
        将一个插件重新加载到内存
        :param plugin_id: 插件ID
        """
        # 先移除插件实例
        self.stop(plugin_id)
        # 重新加载
        self.start(plugin_id)
        # 广播事件
        eventmanager.send_event(EventType.PluginReload, data={"plugin_id": plugin_id})

    @staticmethod
    def _clear_plugin_modules(plugin_id: Optional[str] = None):
        """
        清除插件及其所有子模块的缓存
        :param plugin_id: 插件ID
        """

        # 构建插件模块前缀
        if plugin_id:
            plugin_module_prefix = f"app.plugins.{plugin_id.lower()}"
        else:
            plugin_module_prefix = "app.plugins"

        # 收集需要删除的模块名（创建模块名列表的副本以避免迭代时修改字典）
        modules_to_remove = []
        for module_name in list(sys.modules.keys()):
            if module_name == plugin_module_prefix or module_name.startswith(plugin_module_prefix + "."):
                modules_to_remove.append(module_name)

        # 删除模块
        for module_name in modules_to_remove:
            try:
                del sys.modules[module_name]
                logger.debug(f"已清除插件模块缓存：{module_name}")
            except KeyError:
                # 模块可能已经被删除
                pass

        importlib.invalidate_caches()
        logger.debug("已清除查找器的缓存")

        if plugin_id:
            if modules_to_remove:
                logger.info(f"插件 {plugin_id} 共清除 {len(modules_to_remove)} 个模块缓存：{modules_to_remove}")
            else:
                logger.debug(f"插件 {plugin_id} 没有找到需要清除的模块缓存")

    def sync(self) -> List[str]:
        """
        安装本地不存在或需要更新的插件
        """

        def install_plugin(plugin):
            start_time = time.time()
            state, msg = PluginHelper().install(pid=plugin.id, repo_url=plugin.repo_url, force_install=True)
            elapsed_time = time.time() - start_time
            if state:
                logger.info(
                    f"插件 {plugin.plugin_name} 安装成功，版本：{plugin.plugin_version}，耗时：{elapsed_time:.2f} 秒")
                sync_plugins.append(plugin.id)
            else:
                logger.error(
                    f"插件 {plugin.plugin_name} v{plugin.plugin_version} 安装失败：{msg}，耗时：{elapsed_time:.2f} 秒")
                failed_plugins.append(plugin.id)

        if SystemUtils.is_frozen():
            return []

        # 获取已安装插件列表
        install_plugins = SystemConfigOper().get(SystemConfigKey.UserInstalledPlugins) or []
        # 获取在线插件列表
        online_plugins = self.get_online_plugins()
        # 确定需要安装的插件
        plugins_to_install = [
            plugin for plugin in online_plugins
            if plugin.id in install_plugins and not self.is_plugin_exists(plugin.id, plugin.plugin_version)
        ]

        if not plugins_to_install:
            return []
        logger.info("开始安装第三方插件...")
        sync_plugins = []
        failed_plugins = []

        # 使用 ThreadPoolExecutor 进行并发安装
        total_start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(install_plugin, plugin): plugin
                for plugin in plugins_to_install
            }
            for future in as_completed(futures):
                plugin = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    logger.error(f"插件 {plugin.plugin_name} 安装过程中出现异常: {exc}")

        total_elapsed_time = time.time() - total_start_time
        logger.info(
            f"第三方插件安装完成，成功：{len(sync_plugins)} 个，"
            f"失败：{len(failed_plugins)} 个，总耗时：{total_elapsed_time:.2f} 秒"
        )
        return sync_plugins

    @staticmethod
    def install_plugin_missing_dependencies() -> List[str]:
        """
        安装插件中缺失或不兼容的依赖项
        """
        pluginhelper = PluginHelper()
        # 第一步：获取需要安装的依赖项列表
        missing_dependencies = pluginhelper.find_missing_dependencies()
        if not missing_dependencies:
            return missing_dependencies
        logger.debug(f"检测到缺失的依赖项: {missing_dependencies}")
        logger.info(f"开始安装缺失的依赖项，共 {len(missing_dependencies)} 个...")
        # 第二步：安装依赖项并返回结果
        total_start_time = time.time()
        success, message = pluginhelper.install_dependencies(missing_dependencies)
        total_elapsed_time = time.time() - total_start_time
        if success:
            logger.info(f"已完成 {len(missing_dependencies)} 个依赖项安装，总耗时：{total_elapsed_time:.2f} 秒")
        else:
            logger.warning(f"存在缺失依赖项安装失败，请尝试手动安装，总耗时：{total_elapsed_time:.2f} 秒")
        return missing_dependencies

    def get_plugin_config(self, pid: str) -> dict:
        """
        获取插件配置
        :param pid: 插件ID
        """
        if not self._plugins.get(pid):
            return {}
        conf = SystemConfigOper().get(self._config_key % pid)
        if conf:
            # 去掉空Key
            return {k: v for k, v in conf.items() if k}
        return {}

    def save_plugin_config(self, pid: str, conf: dict, force: bool = False) -> bool:
        """
        保存插件配置
        :param pid: 插件ID
        :param conf: 配置
        :param force: 强制保存
        """
        if not force and not self._plugins.get(pid):
            return False
        SystemConfigOper().set(self._config_key % pid, conf)
        return True

    def delete_plugin_config(self, pid: str) -> bool:
        """
        删除插件配置
        :param pid: 插件ID
        """
        if not self._plugins.get(pid):
            return False
        return SystemConfigOper().delete(self._config_key % pid)

    def delete_plugin_data(self, pid: str) -> bool:
        """
        删除插件数据
        :param pid: 插件ID
        """
        if not self._plugins.get(pid):
            return False
        PluginDataOper().del_data(pid)
        return True

    def get_plugin_state(self, pid: str) -> bool:
        """
        获取插件状态
        :param pid: 插件ID
        """
        plugin = self._running_plugins.get(pid)
        return plugin.get_state() if plugin else False

    def get_plugin_commands(self, pid: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取插件命令
        [{
            "cmd": "/xx",
            "event": EventType.xx,
            "desc": "xxxx",
            "data": {},
            "pid": "",
        }]
        """
        ret_commands = []
        # 创建字典快照避免并发修改
        running_plugins_snapshot = dict(self._running_plugins)
        for plugin_id, plugin in running_plugins_snapshot.items():
            if pid and pid != plugin_id:
                continue
            if hasattr(plugin, "get_command") and ObjectUtils.check_method(plugin.get_command):
                try:
                    if not plugin.get_state():
                        continue
                    commands = plugin.get_command() or []
                    for command in commands:
                        command["pid"] = plugin_id
                    ret_commands.extend(commands)
                except Exception as e:
                    logger.error(f"获取插件命令出错：{str(e)}")
        return ret_commands

    def get_plugin_apis(self, pid: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取插件API
        [{
            "path": "/xx",
            "endpoint": self.xxx,
            "methods": ["GET", "POST"],
            "summary": "API名称",
            "description": "API说明",
            "allow_anonymous": false
        }]
        """
        ret_apis = []
        if pid:
            plugins = {pid: self._running_plugins.get(pid)}
        else:
            plugins = self._running_plugins
        for plugin_id, plugin in plugins.items():
            if pid and pid != plugin_id:
                continue
            if hasattr(plugin, "get_api") and ObjectUtils.check_method(plugin.get_api):
                try:
                    apis = plugin.get_api() or []
                    for api in apis:
                        api["path"] = f"/{plugin_id}{api['path']}"
                        if not api.get("auth"):
                            api["auth"] = "apikey"
                    ret_apis.extend(apis)
                except Exception as e:
                    logger.error(f"获取插件 {plugin_id} API出错：{str(e)}")
        return ret_apis

    def get_plugin_services(self, pid: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取插件服务
        [{
            "id": "服务ID",
            "name": "服务名称",
            "trigger": "触发器：cron、interval、date、CronTrigger.from_crontab()",
            "func": self.xxx,
            "kwargs": {} # 定时器参数,
            "func_kwargs": {} # 方法参数
        }]
        """
        ret_services = []
        # 创建字典快照避免并发修改
        running_plugins_snapshot = dict(self._running_plugins)
        for plugin_id, plugin in running_plugins_snapshot.items():
            if pid and pid != plugin_id:
                continue
            if hasattr(plugin, "get_service") and ObjectUtils.check_method(plugin.get_service):
                try:
                    if not plugin.get_state():
                        continue
                    services = plugin.get_service() or []
                    ret_services.extend(services)
                except Exception as e:
                    logger.error(f"获取插件 {plugin_id} 服务出错：{str(e)}")
        return ret_services

    def get_plugin_modules(self, pid: Optional[str] = None) -> Dict[tuple, Dict[str, Any]]:
        """
        获取插件模块
        {
            plugin_id: {
                method: function
            }
        }
        """
        ret_modules = {}
        # 创建字典快照避免并发修改
        running_plugins_snapshot = dict(self._running_plugins)
        for plugin_id, plugin in running_plugins_snapshot.items():
            if pid and pid != plugin_id:
                continue
            if hasattr(plugin, "get_module") and ObjectUtils.check_method(plugin.get_module):
                try:
                    if not plugin.get_state():
                        continue
                    plugin_module = plugin.get_module() or []
                    ret_modules[(plugin_id, plugin.get_name())] = plugin_module
                except Exception as e:
                    logger.error(f"获取插件 {plugin_id} 模块出错：{str(e)}")
        return ret_modules

    def get_plugin_actions(self, pid: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取插件动作
        [{
            "id": "动作ID",
            "name": "动作名称",
            "func": self.xxx,
            "kwargs": {} # 需要附加传递的参数
        }]
        """
        ret_actions = []
        # 创建字典快照避免并发修改
        running_plugins_snapshot = dict(self._running_plugins)
        for plugin_id, plugin in running_plugins_snapshot.items():
            if pid and pid != plugin_id:
                continue
            if hasattr(plugin, "get_actions") and ObjectUtils.check_method(plugin.get_actions):
                try:
                    if not plugin.get_state():
                        continue
                    actions = plugin.get_actions()
                    if actions:
                        ret_actions.append({
                            "plugin_id": plugin_id,
                            "plugin_name": plugin.plugin_name,
                            "actions": actions
                        })
                except Exception as e:
                    logger.error(f"获取插件 {plugin_id} 动作出错：{str(e)}")
        return ret_actions

    @staticmethod
    def get_plugin_remote_entry(plugin_id: str, dist_path: str) -> str:
        """
        获取插件的远程入口地址
        :param plugin_id: 插件 ID
        :param dist_path: 插件的分发路径
        :return: 远程入口地址
        """
        if dist_path.startswith("/"):
            dist_path = dist_path[1:]
        if dist_path.endswith("/"):
            dist_path = dist_path[:-1]
        return f"/plugin/file/{plugin_id.lower()}/{dist_path}/remoteEntry.js"

    def get_plugin_remotes(self, pid: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取插件联邦组件列表
        """
        remotes = []
        # 创建字典快照避免并发修改
        running_plugins_snapshot = dict(self._running_plugins)
        for plugin_id, plugin in running_plugins_snapshot.items():
            if pid and pid != plugin_id:
                continue
            if hasattr(plugin, "get_render_mode"):
                render_mode, dist_path = plugin.get_render_mode()
                if render_mode != "vue":
                    continue
                remotes.append({
                    "id": plugin_id,
                    "url": self.get_plugin_remote_entry(plugin_id, dist_path),
                    "name": plugin.plugin_name,
                })
        return remotes

    def get_plugin_dashboard_meta(self) -> List[Dict[str, str]]:
        """
        获取所有插件仪表盘元信息
        """
        dashboard_meta = []
        # 创建字典快照避免并发修改
        running_plugins_snapshot = dict(self._running_plugins)
        for plugin_id, plugin in running_plugins_snapshot.items():
            if not hasattr(plugin, "get_dashboard") or not ObjectUtils.check_method(plugin.get_dashboard):
                continue
            try:
                if not plugin.get_state():
                    continue
                # 如果是多仪表盘实现
                if hasattr(plugin, "get_dashboard_meta") and ObjectUtils.check_method(plugin.get_dashboard_meta):
                    meta = plugin.get_dashboard_meta()
                    if meta:
                        dashboard_meta.extend([{
                            "id": plugin_id,
                            "name": m.get("name"),
                            "key": m.get("key"),
                        } for m in meta if m])
                else:
                    dashboard_meta.append({
                        "id": plugin_id,
                        "name": plugin.plugin_name,
                        "key": "",
                    })
            except Exception as e:
                logger.error(f"获取插件[{plugin_id}]仪表盘元数据出错：{str(e)}")
        return dashboard_meta

    def get_plugin_dashboard(self, pid: str, key: str, user_agent: str = None) -> schemas.PluginDashboard:
        """
        获取插件仪表盘
        """

        def __get_params_count(func: Callable):
            """
            获取函数的参数信息
            """
            signature = inspect.signature(func)
            return len(signature.parameters)

        # 获取插件实例
        plugin_instance = self.running_plugins.get(pid)
        if not plugin_instance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"插件 {pid} 不存在或未加载")

        # 渲染模式
        render_mode, _ = plugin_instance.get_render_mode()
        # 获取插件仪表板
        try:
            # 检查方法的参数个数
            params_count = __get_params_count(plugin_instance.get_dashboard)
            if params_count > 1:
                dashboard: Tuple = plugin_instance.get_dashboard(key=key, user_agent=user_agent)
            elif params_count > 0:
                dashboard: Tuple = plugin_instance.get_dashboard(user_agent=user_agent)
            else:
                dashboard: Tuple = plugin_instance.get_dashboard()
        except Exception as e:
            logger.error(f"插件 {pid} 调用方法 get_dashboard 出错: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"插件 {pid} 调用方法 get_dashboard 出错: {str(e)}")
        cols, attrs, elements = dashboard
        return schemas.PluginDashboard(
            id=pid,
            name=plugin_instance.plugin_name,
            key=key,
            render_mode=render_mode,
            cols=cols or {},
            attrs=attrs or {},
            elements=elements
        )

    def get_plugin_attr(self, pid: str, attr: str) -> Any:
        """
        获取插件属性
        :param pid: 插件ID
        :param attr: 属性名
        """
        plugin = self._running_plugins.get(pid)
        if not plugin:
            return None
        if not hasattr(plugin, attr):
            return None
        return getattr(plugin, attr)

    def run_plugin_method(self, pid: str, method: str, *args, **kwargs) -> Any:
        """
        运行插件方法
        :param pid: 插件ID
        :param method: 方法名
        :param args: 参数
        :param kwargs: 关键字参数
        """
        plugin = self._running_plugins.get(pid)
        if not plugin:
            return None
        if not hasattr(plugin, method):
            return None
        return getattr(plugin, method)(*args, **kwargs)

    async def async_run_plugin_method(self, pid: str, method: str, *args, **kwargs) -> Any:
        """
        异步运行插件方法
        :param pid: 插件ID
        :param method: 方法名
        :param args: 参数
        :param kwargs: 关键字参数
        """
        plugin = self._running_plugins.get(pid)
        if not plugin:
            return None
        if not hasattr(plugin, method):
            return None
        method_func = getattr(plugin, method)
        if asyncio.iscoroutinefunction(method_func):
            return await method_func(*args, **kwargs)
        else:
            return method_func(*args, **kwargs)

    def get_plugin_ids(self) -> List[str]:
        """
        获取所有插件ID
        """
        return list(self._plugins.keys())

    def get_running_plugin_ids(self) -> List[str]:
        """
        获取所有运行态插件ID
        """
        return list(self._running_plugins.keys())

    @cached(maxsize=1, ttl=1800)
    def get_online_plugins(self, force: bool = False) -> List[schemas.Plugin]:
        """
        获取所有在线插件信息
        """
        if force:
            self.get_online_plugins.cache_clear()

        if not settings.PLUGIN_MARKET:
            return []

        # 用于存储高于 v1 版本的插件（如 v2, v3 等）
        higher_version_plugins = []
        # 用于存储 v1 版本插件
        base_version_plugins = []

        # 使用多线程获取线上插件
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures_to_version = {}
            for m in settings.PLUGIN_MARKET.split(","):
                if not m:
                    continue
                # 提交任务获取 v1 版本插件，存储 future 到 version 的映射
                base_future = executor.submit(self.get_plugins_from_market, m, None, force)
                futures_to_version[base_future] = "base_version"

                # 提交任务获取高版本插件（如 v2、v3），存储 future 到 version 的映射
                if settings.VERSION_FLAG:
                    higher_version_future = executor.submit(self.get_plugins_from_market, m,
                                                            settings.VERSION_FLAG, force)
                    futures_to_version[higher_version_future] = "higher_version"

            # 按照完成顺序处理结果
            for future in concurrent.futures.as_completed(futures_to_version):
                plugins = future.result()
                version = futures_to_version[future]

                if plugins:
                    if version == "higher_version":
                        higher_version_plugins.extend(plugins)  # 收集高版本插件
                    else:
                        base_version_plugins.extend(plugins)  # 收集 v1 版本插件

        return self._process_plugins_list(higher_version_plugins, base_version_plugins)

    def get_local_plugins(self) -> List[schemas.Plugin]:
        """
        获取所有本地已下载的插件信息
        """
        # 返回值
        plugins = []
        # 已安装插件
        installed_apps = SystemConfigOper().get(SystemConfigKey.UserInstalledPlugins) or []
        for pid, plugin_class in self._plugins.items():
            # 运行状插件
            plugin_obj = self._running_plugins.get(pid)
            # 基本属性
            plugin = schemas.Plugin()
            # ID
            plugin.id = pid
            # 安装状态
            if pid in installed_apps:
                plugin.installed = True
            else:
                plugin.installed = False
            # 运行状态
            if plugin_obj and hasattr(plugin_obj, "get_state"):
                try:
                    state = plugin_obj.get_state()
                except Exception as e:
                    logger.error(f"获取插件 {pid} 状态出错：{str(e)}")
                    state = False
                plugin.state = state
            else:
                plugin.state = False
            # 是否有详情页面
            if hasattr(plugin_class, "get_page"):
                if ObjectUtils.check_method(plugin_class.get_page):
                    plugin.has_page = True
                else:
                    plugin.has_page = False
            # 公钥
            if hasattr(plugin_class, "plugin_public_key"):
                plugin.plugin_public_key = plugin_class.plugin_public_key
            # 权限
            if not self.__set_and_check_auth_level(plugin=plugin, source=plugin_class):
                continue
            # 名称
            if hasattr(plugin_class, "plugin_name"):
                plugin.plugin_name = plugin_class.plugin_name
            # 描述
            if hasattr(plugin_class, "plugin_desc"):
                plugin.plugin_desc = plugin_class.plugin_desc
            # 版本
            if hasattr(plugin_class, "plugin_version"):
                plugin.plugin_version = plugin_class.plugin_version
            # 图标
            if hasattr(plugin_class, "plugin_icon"):
                plugin.plugin_icon = plugin_class.plugin_icon
            # 作者
            if hasattr(plugin_class, "plugin_author"):
                plugin.plugin_author = plugin_class.plugin_author
            # 作者链接
            if hasattr(plugin_class, "author_url"):
                plugin.author_url = plugin_class.author_url
            # 加载顺序
            if hasattr(plugin_class, "plugin_order"):
                plugin.plugin_order = plugin_class.plugin_order
            # 是否需要更新
            plugin.has_update = False
            # 本地标志
            plugin.is_local = True
            # 汇总
            plugins.append(plugin)
        # 根据加载排序重新排序
        plugins.sort(key=lambda x: x.plugin_order if hasattr(x, "plugin_order") else 0)
        return plugins

    @staticmethod
    def is_plugin_exists(pid: str, version: str = None) -> bool:
        """
        判断插件是否存在，并满足版本要求(有传入version时)
        :param pid: 插件ID
        :param version: 插件版本
        """
        if not pid:
            return False
        try:
            # 构建包名
            package_name = f"app.plugins.{pid.lower()}"
            # 检查包是否存在
            spec = importlib.util.find_spec(package_name)
            package_exists = spec is not None and spec.origin is not None
            logger.debug(f"{pid} exists: {package_exists}")
            if not package_exists:
                return False

            local_version = PluginManager().get_plugin_attr(pid=pid, attr="plugin_version")
            if not local_version:
                return False

            if version and not StringUtils.compare_version(local_version, ">=", version):
                logger.warn(f"Plugin {pid} version: {local_version} (older than version: {version})")
                return False

            return True
        except Exception as e:
            logger.debug(f"获取插件是否在本地包中存在失败，{e}")
            return False

    def get_plugins_from_market(self, market: str,
                                package_version: Optional[str] = None,
                                force: bool = False) -> Optional[List[schemas.Plugin]]:
        """
        从指定的市场获取插件信息
        :param market: 市场的 URL 或标识
        :param package_version: 首选插件版本 (如 "v2", "v3")，如果不指定则获取 v1 版本
        :param force: 是否强制刷新（忽略缓存）
        :return: 返回插件的列表，若获取失败返回 []
        """
        if not market:
            return []
        # 已安装插件
        installed_apps = SystemConfigOper().get(SystemConfigKey.UserInstalledPlugins) or []
        # 获取在线插件
        online_plugins = PluginHelper().get_plugins(market, package_version, force)
        if online_plugins is None:
            logger.warning(
                f"获取{package_version if package_version else ''}插件库失败：{market}，请检查 GitHub 网络连接")
            return []
        ret_plugins = []
        add_time = len(online_plugins)
        for pid, plugin_info in online_plugins.items():
            plugin = self._process_plugin_info(pid, plugin_info, market, installed_apps, add_time, package_version)
            if plugin:
                ret_plugins.append(plugin)
            add_time -= 1

        return ret_plugins

    @staticmethod
    def _process_plugins_list(higher_version_plugins: List[schemas.Plugin],
                              base_version_plugins: List[schemas.Plugin]) -> List[schemas.Plugin]:
        """
        处理插件列表：合并、去重、排序、保留最高版本
        :param higher_version_plugins: 高版本插件列表
        :param base_version_plugins: 基础版本插件列表
        :return: 处理后的插件列表
        """
        # 优先处理高版本插件
        all_plugins = []
        all_plugins.extend(higher_version_plugins)
        # 将未出现在高版本插件列表中的 v1 插件加入 all_plugins
        higher_plugin_ids = {f"{p.id}{p.plugin_version}" for p in higher_version_plugins}
        all_plugins.extend([p for p in base_version_plugins if f"{p.id}{p.plugin_version}" not in higher_plugin_ids])
        # 去重
        all_plugins = list({f"{p.id}{p.plugin_version}": p for p in all_plugins}.values())
        # 所有插件按 repo 在设置中的顺序排序
        all_plugins.sort(
            key=lambda x: settings.PLUGIN_MARKET.split(",").index(x.repo_url) if x.repo_url else 0
        )
        # 相同 ID 的插件保留版本号最大的版本
        max_versions = {}
        for p in all_plugins:
            if p.id not in max_versions or StringUtils.compare_version(p.plugin_version, ">", max_versions[p.id]):
                max_versions[p.id] = p.plugin_version
        result = [p for p in all_plugins if p.plugin_version == max_versions[p.id]]
        logger.info(f"共获取到 {len(result)} 个线上插件")
        return result

    def _process_plugin_info(self, pid: str, plugin_info: dict, market: str,
                             installed_apps: List[str], add_time: int,
                             package_version: Optional[str] = None) -> Optional[schemas.Plugin]:
        """
        处理单个插件信息，创建 schemas.Plugin 对象
        :param pid: 插件ID
        :param plugin_info: 插件信息字典
        :param market: 市场URL
        :param installed_apps: 已安装插件列表
        :param add_time: 添加顺序
        :param package_version: 包版本
        :return: 创建的插件对象，如果验证失败返回None
        """
        if not isinstance(plugin_info, dict):
            return None

        # 如 package_version 为空，则需要判断插件是否兼容当前版本
        if not package_version:
            if plugin_info.get(settings.VERSION_FLAG) is not True:
                # 插件当前版本不兼容
                return None

        # 运行状插件
        plugin_obj = self._running_plugins.get(pid)
        # 非运行态插件
        plugin_static = self._plugins.get(pid)
        # 基本属性
        plugin = schemas.Plugin()
        # ID
        plugin.id = pid
        # 安装状态
        if pid in installed_apps and plugin_static:
            plugin.installed = True
        else:
            plugin.installed = False
        # 是否有新版本
        plugin.has_update = False
        if plugin_static:
            installed_version = getattr(plugin_static, "plugin_version")
            if StringUtils.compare_version(installed_version, "<", plugin_info.get("version")):
                # 需要更新
                plugin.has_update = True
        # 运行状态
        if plugin_obj and hasattr(plugin_obj, "get_state"):
            try:
                state = plugin_obj.get_state()
            except Exception as e:
                logger.error(f"获取插件 {pid} 状态出错：{str(e)}")
                state = False
            plugin.state = state
        else:
            plugin.state = False
        # 是否有详情页面
        plugin.has_page = False
        if plugin_obj and hasattr(plugin_obj, "get_page"):
            if ObjectUtils.check_method(plugin_obj.get_page):
                plugin.has_page = True
        # 公钥
        if plugin_info.get("key"):
            plugin.plugin_public_key = plugin_info.get("key")
        # 权限
        if not self.__set_and_check_auth_level(plugin=plugin, source=plugin_info):
            return None
        # 名称
        if plugin_info.get("name"):
            plugin.plugin_name = plugin_info.get("name")
        # 描述
        if plugin_info.get("description"):
            plugin.plugin_desc = plugin_info.get("description")
        # 版本
        if plugin_info.get("version"):
            plugin.plugin_version = plugin_info.get("version")
        # 图标
        if plugin_info.get("icon"):
            plugin.plugin_icon = plugin_info.get("icon")
        # 标签
        if plugin_info.get("labels"):
            plugin.plugin_label = plugin_info.get("labels")
        # 作者
        if plugin_info.get("author"):
            plugin.plugin_author = plugin_info.get("author")
        # 更新历史
        if plugin_info.get("history"):
            plugin.history = plugin_info.get("history")
        # 仓库链接
        plugin.repo_url = market
        # 本地标志
        plugin.is_local = False
        # 添加顺序
        plugin.add_time = add_time

        return plugin

    @cached(maxsize=1, ttl=1800)
    async def async_get_online_plugins(self, force: bool = False) -> List[schemas.Plugin]:
        """
        异步获取所有在线插件信息
        :param force: 是否强制刷新（忽略缓存）
        """
        if force:
            await self.async_get_online_plugins.cache_clear()

        if not settings.PLUGIN_MARKET:
            return []

        # 用于存储高于 v1 版本的插件（如 v2, v3 等）
        higher_version_plugins = []
        # 用于存储 v1 版本插件
        base_version_plugins = []

        # 使用异步并发获取线上插件
        import asyncio
        tasks = []
        task_to_version = {}

        for m in settings.PLUGIN_MARKET.split(","):
            if not m:
                continue
            # 创建任务获取 v1 版本插件
            base_task = asyncio.create_task(self.async_get_plugins_from_market(m, None, force))
            tasks.append(base_task)
            task_to_version[base_task] = "base_version"

            # 创建任务获取高版本插件（如 v2、v3）
            if settings.VERSION_FLAG:
                higher_version_task = asyncio.create_task(
                    self.async_get_plugins_from_market(m, settings.VERSION_FLAG, force))
                tasks.append(higher_version_task)
                task_to_version[higher_version_task] = "higher_version"

        # 并发执行所有任务
        if tasks:
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(completed_tasks):
                task = tasks[i]
                version = task_to_version[task]

                # 检查是否有异常
                if isinstance(result, Exception):
                    logger.error(f"获取插件市场数据失败：{str(result)}")
                    continue

                plugins = result
                if plugins:
                    if version == "higher_version":
                        higher_version_plugins.extend(plugins)  # 收集高版本插件
                    else:
                        base_version_plugins.extend(plugins)  # 收集 v1 版本插件

        return self._process_plugins_list(higher_version_plugins, base_version_plugins)

    async def async_get_plugins_from_market(self, market: str,
                                            package_version: Optional[str] = None,
                                            force: bool = False) -> Optional[List[schemas.Plugin]]:
        """
        异步从指定的市场获取插件信息
        :param market: 市场的 URL 或标识
        :param package_version: 首选插件版本 (如 "v2", "v3")，如果不指定则获取 v1 版本
        :param force: 是否强制刷新（忽略缓存）
        :return: 返回插件的列表，若获取失败返回 []
        """
        if not market:
            return []
        # 已安装插件
        installed_apps = SystemConfigOper().get(SystemConfigKey.UserInstalledPlugins) or []
        # 获取在线插件
        online_plugins = await PluginHelper().async_get_plugins(market, package_version, force)
        if online_plugins is None:
            logger.warning(
                f"获取{package_version if package_version else ''}插件库失败：{market}，请检查 GitHub 网络连接")
            return []
        ret_plugins = []
        add_time = len(online_plugins)
        for pid, plugin_info in online_plugins.items():
            plugin = self._process_plugin_info(pid, plugin_info, market, installed_apps, add_time, package_version)
            if plugin:
                ret_plugins.append(plugin)
            add_time -= 1

        return ret_plugins

    @staticmethod
    def __set_and_check_auth_level(plugin: Union[schemas.Plugin, Type[Any]],
                                   source: Optional[Union[dict, Type[Any]]] = None) -> bool:
        """
        设置并检查插件的认证级别
        :param plugin: 插件对象或包含 auth_level 属性的对象
        :param source: 可选的字典对象或类对象，可能包含 "level" 或 "auth_level" 键
        :return: 如果插件的认证级别有效且当前环境的认证级别满足要求，返回 True，否则返回 False
        """
        # 检查并赋值 source 中的 level 或 auth_level
        if source:
            if isinstance(source, dict) and "level" in source:
                plugin.auth_level = source.get("level")
            elif hasattr(source, "auth_level"):
                plugin.auth_level = source.auth_level
        # 如果 source 为空且 plugin 本身没有 auth_level，直接返回 True
        elif not hasattr(plugin, "auth_level"):
            return True

        # auth_level 级别说明
        # 1 - 所有用户可见
        # 2 - 站点认证用户可见
        # 3 - 站点&密钥认证可见
        # 99 - 站点&特殊密钥认证可见
        # 如果当前站点认证级别大于 1 且插件级别为 99，并存在插件公钥，说明为特殊密钥认证，通过密钥匹配进行认证
        siteshelper = SitesHelper()
        if siteshelper.auth_level > 1 and plugin.auth_level == 99 and hasattr(plugin, "plugin_public_key"):
            plugin_id = plugin.id if isinstance(plugin, schemas.Plugin) else plugin.__name__
            public_key = plugin.plugin_public_key
            if public_key:
                private_key = PluginManager.__get_plugin_private_key(plugin_id)
                verify = RSAUtils.verify_rsa_keys(public_key=public_key, private_key=private_key)
                return verify
        # 如果当前站点认证级别小于插件级别，则返回 False
        if siteshelper.auth_level < plugin.auth_level:
            return False
        return True

    @staticmethod
    def __get_plugin_private_key(plugin_id: str) -> Optional[str]:
        """
        根据插件标识获取对应的私钥
        :param plugin_id: 插件标识
        :return: 对应的插件私钥，如果未找到则返回 None
        """
        try:
            # 将插件标识转换为大写并构建环境变量名称
            env_var_name = f"PLUGIN_{plugin_id.upper()}_PRIVATE_KEY"
            private_key = os.environ.get(env_var_name)
            return private_key
        except Exception as e:
            logger.debug(f"获取插件 {plugin_id} 的私钥时发生错误：{e}")
            return None

    def clone_plugin(self, plugin_id: str, suffix: str, name: str, description: str,
                     version: str = None, icon: str = None) -> Tuple[bool, str]:
        """
        创建插件分身
        :param plugin_id: 原插件ID
        :param suffix: 分身后缀
        :param name: 分身名称
        :param description: 分身描述
        :param version: 自定义版本号
        :param icon: 自定义图标URL
        :return: (是否成功, 错误信息)
        """
        try:
            # 验证参数
            if not plugin_id or not suffix:
                return False, "插件ID和分身后缀不能为空"

            # 检查原插件是否存在
            if plugin_id not in self._plugins:
                return False, f"原插件 {plugin_id} 不存在"

            # 生成分身插件ID
            clone_id = f"{plugin_id}{suffix.lower()}"

            # 检查分身插件是否已存在
            if self.is_plugin_exists(clone_id):
                return False, f"分身插件 {clone_id} 已存在"

            # 获取原插件目录
            original_plugin_dir = Path(settings.ROOT_PATH) / "app" / "plugins" / plugin_id.lower()
            if not original_plugin_dir.exists():
                return False, f"原插件目录 {original_plugin_dir} 不存在"

            # 创建分身插件目录
            clone_plugin_dir = Path(settings.ROOT_PATH) / "app" / "plugins" / clone_id.lower()

            # 复制插件目录
            import shutil
            shutil.copytree(original_plugin_dir, clone_plugin_dir)
            logger.info(f"已复制插件目录：{original_plugin_dir} -> {clone_plugin_dir}")

            # 修改插件文件内容
            success, msg = self._modify_plugin_files(
                plugin_dir=clone_plugin_dir,
                original_id=plugin_id,
                suffix=suffix.lower(),
                name=name,
                description=description,
                version=version,
                icon=icon
            )

            if not success:
                # 如果修改失败，清理已创建的目录
                if clone_plugin_dir.exists():
                    shutil.rmtree(clone_plugin_dir)
                return False, msg

            # 将分身插件添加到已安装列表
            systemconfig = SystemConfigOper()
            installed_plugins = systemconfig.get(SystemConfigKey.UserInstalledPlugins) or []
            if clone_id not in installed_plugins:
                installed_plugins.append(clone_id)
                systemconfig.set(SystemConfigKey.UserInstalledPlugins, installed_plugins)

            # 为分身插件创建初始配置（从原插件复制配置）
            logger.info(f"正在为分身插件 {clone_id} 创建初始配置...")
            original_config = self.get_plugin_config(plugin_id)
            if original_config:
                # 复制原插件配置作为分身插件的初始配置
                clone_config = original_config.copy()
                # 可以在这里修改一些默认值，比如禁用分身插件
                # 默认禁用分身插件，让用户手动配置
                clone_config['enable'] = False
                clone_config['enabled'] = False
                self.save_plugin_config(clone_id, clone_config, force=True)
                logger.info(f"已为分身插件 {clone_id} 设置初始配置")
            else:
                logger.info(f"原插件 {plugin_id} 没有配置，分身插件 {clone_id} 将使用默认配置")

            # 注册分身插件的API和服务
            logger.info(f"正在注册分身插件 {clone_id} ...")
            PluginManager().reload_plugin(clone_id)
            # 确保分身插件正确初始化配置
            if clone_id in self._running_plugins:
                clone_instance = self._running_plugins[clone_id]
                clone_config = self.get_plugin_config(clone_id)
                if clone_config:
                    logger.info(f"正在为分身插件 {clone_id} 重新初始化配置...")
                    clone_instance.init_plugin(clone_config)
                    logger.info(f"分身插件 {clone_id} 配置重新初始化完成")

            logger.info(f"插件分身 {clone_id} 创建成功")
            return True, clone_id

        except Exception as e:
            logger.error(f"创建插件分身失败：{str(e)}")
            return False, f"创建插件分身失败：{str(e)}"

    def _modify_plugin_files(self, plugin_dir: Path, original_id: str, suffix: str,
                             name: str, description: str, version: str = None,
                             icon: str = None) -> Tuple[bool, str]:
        """
        修改插件文件中的类名和相关信息
        :param plugin_dir: 插件目录
        :param original_id: 原插件ID
        :param suffix: 分身后缀
        :param name: 分身名称
        :param description: 分身描述
        :param version: 自定义版本号
        :param icon: 自定义图标URL
        :return: (是否成功, 错误信息)
        """
        try:
            # 获取原插件类
            original_plugin_class = self._plugins.get(original_id)
            if not original_plugin_class:
                return False, f"无法获取原插件类 {original_id}"

            # 获取原类名
            original_class_name = original_plugin_class.__name__
            clone_class_name = f"{original_class_name}{suffix}"

            # 修改 __init__.py 文件
            init_file = plugin_dir / "__init__.py"
            if init_file.exists():
                success, msg = self._modify_python_file(
                    file_path=init_file,
                    original_class_name=original_class_name,
                    clone_class_name=clone_class_name,
                    name=name,
                    description=description,
                    version=version,
                    icon=icon
                )
                if not success:
                    return False, msg

            # 检查是否为联邦插件（存在dist目录）
            dist_dir = plugin_dir / "dist"
            if dist_dir.exists():
                success, msg = self._modify_federation_files(
                    dist_dir=dist_dir,
                    original_class_name=original_class_name,
                    clone_class_name=clone_class_name
                )
                if not success:
                    return False, msg

            return True, "文件修改成功"

        except Exception as e:
            logger.error(f"修改插件文件失败：{str(e)}")
            return False, f"修改插件文件失败：{str(e)}"

    @staticmethod
    def _modify_python_file(file_path: Path, original_class_name: str,
                            clone_class_name: str, name: str, description: str,
                            version: str = None, icon: str = None) -> Tuple[bool, str]:
        """
        修改Python文件中的类名和插件信息
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 替换类名
            content = content.replace(f"class {original_class_name}", f"class {clone_class_name}")

            # 替换插件名称和描述
            import re

            # 替换 plugin_name
            if name:
                content = re.sub(
                    r'plugin_name\s*=\s*["\'][^"\']*["\']',
                    f'plugin_name = "{name}"',
                    content
                )

            # 替换 plugin_desc
            if description:
                content = re.sub(
                    r'plugin_desc\s*=\s*["\'][^"\']*["\']',
                    f'plugin_desc = "{description}"',
                    content
                )

            # 替换 plugin_config_prefix（如果存在）
            content = re.sub(
                r'plugin_config_prefix\s*=\s*["\'][^"\']*["\']',
                f'plugin_config_prefix = "{clone_class_name.lower()}_"',
                content
            )

            # 替换 plugin_version（如果提供了自定义版本）
            if version:
                content = re.sub(
                    r'plugin_version\s*=\s*["\'][^"\']*["\']',
                    f'plugin_version = "{version}"',
                    content
                )

            # 替换 plugin_icon（如果提供了自定义图标）
            if icon and icon.strip():
                old_content = content
                content = re.sub(
                    r'plugin_icon\s*=\s*["\'][^"\']*["\']',
                    f'plugin_icon = "{icon}"',
                    content
                )
                if old_content != content:
                    logger.info(f"已替换插件图标为: {icon}")
                else:
                    logger.warning(f"插件图标替换失败，未找到匹配的图标设置")
            else:
                logger.info("未提供自定义图标，保持原插件图标")

            # 添加分身标志
            if "def init_plugin(self" in content:
                init_index = content.index("def init_plugin(self")
                # 在 def init_plugin(self 前添加 is_clone = True
                content = content[:init_index] + "is_clone = True\n\n    " + content[init_index:]

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.debug(f"已修改Python文件：{file_path}")
            return True, "Python文件修改成功"

        except Exception as e:
            logger.error(f"修改Python文件失败：{str(e)}")
            return False, f"修改Python文件失败：{str(e)}"

    def _modify_federation_files(self, dist_dir: Path, original_class_name: str,
                                 clone_class_name: str) -> Tuple[bool, str]:
        """
        修改联邦插件的前端文件
        """
        try:
            # 获取原始插件名（从类名推导）
            original_plugin_name = original_class_name
            clone_plugin_name = clone_class_name

            # 遍历dist目录下的所有文件
            for file_path in dist_dir.rglob("*"):
                if not file_path.is_file():
                    continue

                # 处理JS文件
                if file_path.suffix == '.js':
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # 替换类名引用（精确匹配）
                        content = content.replace(original_class_name, clone_class_name)
                        # 替换插件名引用（如果存在）
                        content = content.replace(f'"{original_plugin_name}"', f'"{clone_plugin_name}"')
                        content = content.replace(f"'{original_plugin_name}'", f"'{clone_plugin_name}'")
                        # 替换CSS key中的类名（联邦插件特有）
                        content = content.replace(f'css__{original_class_name}__', f'css__{clone_class_name}__')
                        # 替换可能的小写类名引用
                        content = content.replace(original_class_name.lower(), clone_class_name.lower())

                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)

                        logger.debug(f"已修改联邦插件JS文件：{file_path}")

                    except Exception as e:
                        logger.warning(f"修改联邦插件文件 {file_path} 失败：{str(e)}")
                        continue

                # 处理CSS文件
                elif file_path.suffix == '.css':
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # 替换CSS中可能的类名引用
                        content = content.replace(original_class_name.lower(),
                                                  clone_class_name.lower()).replace(original_class_name,
                                                                                    clone_class_name)

                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)

                        logger.debug(f"已修改联邦插件CSS文件：{file_path}")

                    except Exception as e:
                        logger.warning(f"修改联邦插件CSS文件 {file_path} 失败：{str(e)}")
                        continue

            # 重命名构建文件（如果需要）
            self._rename_federation_assets(dist_dir, original_class_name, clone_class_name)

            return True, "联邦插件文件修改完成"

        except Exception as e:
            logger.error(f"修改联邦插件文件失败：{str(e)}")
            return False, f"修改联邦插件文件失败：{str(e)}"

    @staticmethod
    def _rename_federation_assets(dist_dir: Path, original_class_name: str, clone_class_name: str):
        """
        重命名联邦插件的资源文件，避免文件名冲突
        """
        try:
            # 查找包含原类名的文件并重命名
            for file_path in dist_dir.glob("*"):
                if not file_path.is_file():
                    continue

                file_name = file_path.name
                # 如果文件名包含原类名，则重命名
                if original_class_name.lower() in file_name.lower():
                    new_name = file_name.replace(
                        original_class_name.lower(),
                        clone_class_name.lower()
                    )
                    new_path = file_path.parent / new_name

                    # 避免重命名冲突
                    if not new_path.exists():
                        file_path.rename(new_path)
                        logger.debug(f"重命名联邦插件文件：{file_name} -> {new_name}")

        except Exception as e:
            # 重命名失败不影响整体流程
            logger.warning(f"重命名联邦插件资源文件失败：{str(e)}")
