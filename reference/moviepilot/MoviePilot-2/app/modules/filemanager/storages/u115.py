import base64
import hashlib
import secrets
import threading
import time
from pathlib import Path
from typing import List, Optional, Tuple, Union

import oss2
import requests
from oss2 import SizedFileAdapter, determine_part_size
from oss2.models import PartInfo

from app import schemas
from app.core.config import settings, global_vars
from app.log import logger
from app.modules.filemanager import StorageBase
from app.modules.filemanager.storages import transfer_process
from app.schemas.types import StorageSchema
from app.utils.singleton import WeakSingleton
from app.utils.string import StringUtils

lock = threading.Lock()


class NoCheckInException(Exception):
    pass


class U115Pan(StorageBase, metaclass=WeakSingleton):
    """
    115相关操作
    """

    # 存储类型
    schema = StorageSchema.U115

    # 支持的整理方式
    transtype = {
        "move": "移动",
        "copy": "复制"
    }
    # 基础url
    base_url = "https://proapi.115.com"

    # 文件块大小，默认10MB
    chunk_size = 10 * 1024 * 1024

    # 流控重试间隔时间
    retry_delay = 70

    def __init__(self):
        super().__init__()
        self._auth_state = {}
        self.session = requests.Session()
        self._init_session()

    def _init_session(self):
        """
        初始化带速率限制的会话
        """
        self.session.headers.update({
            "User-Agent": "W115Storage/2.0",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/x-www-form-urlencoded"
        })

    def _check_session(self):
        """
        检查会话是否过期
        """
        if not self.access_token:
            raise NoCheckInException("【115】请先扫码登录！")

    @property
    def access_token(self) -> Optional[str]:
        """
        访问token
        """
        with lock:
            tokens = self.get_conf()
            refresh_token = tokens.get("refresh_token")
            if not refresh_token:
                return None
            expires_in = tokens.get("expires_in", 0)
            refresh_time = tokens.get("refresh_time", 0)
            if expires_in and refresh_time + expires_in < int(time.time()):
                tokens = self.__refresh_access_token(refresh_token)
                if tokens:
                    self.set_config({
                        "refresh_time": int(time.time()),
                        **tokens
                    })
                else:
                    return None
            access_token = tokens.get("access_token")
            if access_token:
                self.session.headers.update({"Authorization": f"Bearer {access_token}"})
            return access_token

    def generate_qrcode(self) -> Tuple[dict, str]:
        """
        实现PKCE规范的设备授权二维码生成
        """
        # 生成PKCE参数
        code_verifier = secrets.token_urlsafe(96)[:128]
        code_challenge = base64.b64encode(
            hashlib.sha256(code_verifier.encode("utf-8")).digest()
        ).decode("utf-8")
        # 请求设备码
        resp = self.session.post(
            "https://passportapi.115.com/open/authDeviceCode",
            data={
                "client_id": settings.U115_APP_ID,
                "code_challenge": code_challenge,
                "code_challenge_method": "sha256"
            }
        )
        if resp is None:
            return {}, "网络错误"
        result = resp.json()
        if result.get("code") != 0:
            return {}, result.get("message")
        # 持久化验证参数
        self._auth_state = {
            "code_verifier": code_verifier,
            "uid": result["data"]["uid"],
            "time": result["data"]["time"],
            "sign": result["data"]["sign"]
        }

        # 生成二维码内容
        return {
            "codeContent": result['data']['qrcode']
        }, ""

    def check_login(self) -> Optional[Tuple[dict, str]]:
        """
        改进的带PKCE校验的登录状态检查
        """
        if not self._auth_state:
            return {}, "生成二维码失败"
        try:
            resp = self.session.get(
                "https://qrcodeapi.115.com/get/status/",
                params={
                    "uid": self._auth_state["uid"],
                    "time": self._auth_state["time"],
                    "sign": self._auth_state["sign"]
                }
            )
            if resp is None:
                return {}, "网络错误"
            result = resp.json()
            if result.get("code") != 0 or not result.get("data"):
                return {}, result.get("message")
            if result["data"]["status"] == 2:
                tokens = self.__get_access_token()
                self.set_config({
                    "refresh_time": int(time.time()),
                    **tokens
                })
            return {"status": result["data"]["status"], "tip": result["data"]["msg"]}, ""
        except Exception as e:
            return {}, str(e)

    def __get_access_token(self) -> dict:
        """
        确认登录后，获取相关token
        """
        if not self._auth_state:
            raise Exception("【115】请先生成二维码")
        resp = self.session.post(
            "https://passportapi.115.com/open/deviceCodeToToken",
            data={
                "uid": self._auth_state["uid"],
                "code_verifier": self._auth_state["code_verifier"]
            }
        )
        if resp is None:
            raise Exception("获取 access_token 失败")
        result = resp.json()
        if result.get("code") != 0:
            raise Exception(result.get("message"))
        return result["data"]

    def __refresh_access_token(self, refresh_token: str) -> Optional[dict]:
        """
        刷新access_token
        """
        resp = self.session.post(
            "https://passportapi.115.com/open/refreshToken",
            data={
                "refresh_token": refresh_token
            }
        )
        if resp is None:
            logger.error(f"【115】刷新 access_token 失败：refresh_token={refresh_token}")
            return None
        result = resp.json()
        if result.get("code") != 0:
            logger.warn(f"【115】刷新 access_token 失败：{result.get('code')} - {result.get('message')}！")
            return None
        return result.get("data")

    def _request_api(self, method: str, endpoint: str,
                     result_key: Optional[str] = None, **kwargs) -> Optional[Union[dict, list]]:
        """
        带错误处理和速率限制的API请求
        """
        # 检查会话
        self._check_session()

        # 错误日志标志
        no_error_log = kwargs.pop("no_error_log", False)
        # 重试次数
        retry_times = kwargs.pop("retry_limit", 5)

        try:
            resp = self.session.request(
                method, f"{self.base_url}{endpoint}",
                **kwargs
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"【115】{method} 请求 {endpoint} 网络错误: {str(e)}")
            return None

        if resp is None:
            logger.warn(f"【115】{method} 请求 {endpoint} 失败！")
            return None

        kwargs["retry_limit"] = retry_times

        # 处理速率限制
        if resp.status_code == 429:
            reset_time = 5 + int(resp.headers.get("X-RateLimit-Reset", 60))
            logger.debug(
                f"【115】{method} 请求 {endpoint} 限流，等待{reset_time}秒后重试"
            )
            time.sleep(reset_time)
            return self._request_api(method, endpoint, result_key, **kwargs)

        # 处理请求错误
        resp.raise_for_status()

        # 返回数据
        ret_data = resp.json()
        if ret_data.get("code") != 0:
            error_msg = ret_data.get("message")
            if not no_error_log:
                logger.warn(f"【115】{method} 请求 {endpoint} 出错：{error_msg}")
            if "已达到当前访问上限" in error_msg:
                if retry_times <= 0:
                    logger.error(f"【115】{method} 请求 {endpoint} 达到访问上限，重试次数用尽！")
                    return None
                kwargs["retry_limit"] = retry_times - 1
                logger.info(f"【115】{method} 请求 {endpoint} 达到访问上限，等待 {self.retry_delay} 秒后重试...")
                time.sleep(self.retry_delay)
                return self._request_api(method, endpoint, result_key, **kwargs)
            return None

        if result_key:
            return ret_data.get(result_key)
        return ret_data

    @staticmethod
    def _calc_sha1(filepath: Path, size: Optional[int] = None) -> str:
        """
        计算文件SHA1（符合115规范）
        size: 前多少字节
        """
        sha1 = hashlib.sha1()
        with open(filepath, 'rb') as f:
            if size:
                chunk = f.read(size)
                sha1.update(chunk)
            else:
                while chunk := f.read(8192):
                    sha1.update(chunk)
        return sha1.hexdigest()

    def _delay_get_item(self, path: Path) -> Optional[schemas.FileItem]:
        """
        自动延迟重试 get_item 模块
        """
        for i in range(1, 4):
            time.sleep(2 ** i)
            fileitem = self.get_item(path)
            if fileitem:
                return fileitem
        return None

    def init_storage(self):
        pass

    def list(self, fileitem: schemas.FileItem) -> List[schemas.FileItem]:
        """
        目录遍历实现
        """

        if fileitem.type == "file":
            item = self.detail(fileitem)
            if item:
                return [item]
            return []
        if fileitem.path == "/":
            cid = '0'
        else:
            cid = fileitem.fileid
            if not cid:
                _fileitem = self.get_item(Path(fileitem.path))
                if not _fileitem:
                    logger.warn(f"【115】获取目录 {fileitem.path} 失败！")
                    return []
                cid = _fileitem.fileid

        items = []
        offset = 0

        while True:
            resp = self._request_api(
                "GET",
                "/open/ufile/files",
                "data",
                params={"cid": int(cid), "limit": 1000, "offset": offset, "cur": True, "show_dir": 1}
            )
            if resp is None:
                raise FileNotFoundError(f"【115】{fileitem.path} 检索出错！")
            if not resp:
                break
            for item in resp:
                # 更新缓存
                path = f"{fileitem.path}{item['fn']}"
                file_path = path + ("/" if item["fc"] == "0" else "")
                items.append(schemas.FileItem(
                    storage=self.schema.value,
                    fileid=str(item["fid"]),
                    parent_fileid=cid,
                    name=item["fn"],
                    basename=Path(item["fn"]).stem,
                    extension=item["ico"] if item["fc"] == "1" else None,
                    type="dir" if item["fc"] == "0" else "file",
                    path=file_path,
                    size=item["fs"] if item["fc"] == "1" else None,
                    modify_time=item["upt"],
                    pickcode=item["pc"]
                ))

            if len(resp) < 1000:
                break
            offset += len(resp)

        return items

    def create_folder(self, parent_item: schemas.FileItem, name: str) -> Optional[schemas.FileItem]:
        """
        创建目录
        """
        new_path = Path(parent_item.path) / name
        resp = self._request_api(
            "POST",
            "/open/folder/add",
            data={
                "pid": int(parent_item.fileid or "0"),
                "file_name": name
            }
        )
        if not resp:
            return None
        if not resp.get("state"):
            if resp.get("code") == 20004:
                # 目录已存在
                return self.get_item(new_path)
            logger.warn(f"【115】创建目录失败: {resp.get('error')}")
            return None
        return schemas.FileItem(
            storage=self.schema.value,
            fileid=str(resp["data"]["file_id"]),
            path=str(new_path) + "/",
            name=name,
            basename=name,
            type="dir",
            modify_time=int(time.time())
        )

    def upload(self, target_dir: schemas.FileItem, local_path: Path,
               new_name: Optional[str] = None) -> Optional[schemas.FileItem]:
        """
        实现带秒传、断点续传和二次认证的文件上传
        """

        def encode_callback(cb: str) -> str:
            return oss2.utils.b64encode_as_string(cb)

        target_name = new_name or local_path.name
        target_path = Path(target_dir.path) / target_name
        # 计算文件特征值
        file_size = local_path.stat().st_size
        file_sha1 = self._calc_sha1(local_path)
        file_preid = self._calc_sha1(local_path, 128 * 1024 * 1024)

        # 获取目标目录CID
        target_cid = target_dir.fileid
        target_param = f"U_1_{target_cid}"

        # Step 1: 初始化上传
        init_data = {
            "file_name": target_name,
            "file_size": file_size,
            "target": target_param,
            "fileid": file_sha1,
            "preid": file_preid
        }
        init_resp = self._request_api(
            "POST",
            "/open/upload/init",
            data=init_data
        )
        if not init_resp:
            return None
        if not init_resp.get("state"):
            logger.warn(f"【115】初始化上传失败: {init_resp.get('error')}")
            return None
        # 结果
        init_result = init_resp.get("data")
        logger.debug(f"【115】上传 Step 1 初始化结果: {init_result}")
        # 回调信息
        bucket_name = init_result.get("bucket")
        object_name = init_result.get("object")
        callback = init_result.get("callback")
        # 二次认证信息
        sign_check = init_result.get("sign_check")
        pick_code = init_result.get("pick_code")
        sign_key = init_result.get("sign_key")

        # Step 2: 处理二次认证
        if init_result.get("code") in [700, 701] and sign_check:
            sign_checks = sign_check.split("-")
            start = int(sign_checks[0])
            end = int(sign_checks[1])
            # 计算指定区间的SHA1
            # sign_check （用下划线隔开,截取上传文内容的sha1）(单位是byte): "2392148-2392298"
            with open(local_path, "rb") as f:
                # 取2392148-2392298之间的内容(包含2392148、2392298)的sha1
                f.seek(start)
                chunk = f.read(end - start + 1)
                sign_val = hashlib.sha1(chunk).hexdigest().upper()
            # 重新初始化请求
            # sign_key，sign_val(根据sign_check计算的值大写的sha1值)
            init_data.update({
                "pick_code": pick_code,
                "sign_key": sign_key,
                "sign_val": sign_val
            })
            init_resp = self._request_api(
                "POST",
                "/open/upload/init",
                data=init_data
            )
            if not init_resp:
                return None
            if not init_resp.get("state"):
                logger.warn(f"【115】上传二次认证失败: {init_resp.get('error')}")
                return None
            # 二次认证结果
            init_result = init_resp.get("data")
            logger.debug(f"【115】上传 Step 2 二次认证结果: {init_result}")
            if not pick_code:
                pick_code = init_result.get("pick_code")
            if not bucket_name:
                bucket_name = init_result.get("bucket")
            if not object_name:
                object_name = init_result.get("object")
            if not callback:
                callback = init_result.get("callback")

        # Step 3: 秒传
        if init_result.get("status") == 2:
            logger.info(f"【115】{target_name} 秒传成功")
            file_id = init_result.get("file_id", None)
            if file_id:
                logger.debug(f"【115】{target_name} 使用秒传返回ID获取文件信息")
                time.sleep(2)
                info_resp = self._request_api(
                    "GET",
                    "/open/folder/get_info",
                    "data",
                    params={
                        "file_id": int(file_id)
                    }
                )
                if info_resp:
                    return schemas.FileItem(
                        storage=self.schema.value,
                        fileid=str(info_resp["file_id"]),
                        path=str(target_path) + ("/" if info_resp["file_category"] == "0" else ""),
                        type="file" if info_resp["file_category"] == "1" else "dir",
                        name=info_resp["file_name"],
                        basename=Path(info_resp["file_name"]).stem,
                        extension=Path(info_resp["file_name"]).suffix[1:] if info_resp[
                                                                                 "file_category"] == "1" else None,
                        pickcode=info_resp["pick_code"],
                        size=StringUtils.num_filesize(info_resp['size']) if info_resp["file_category"] == "1" else None,
                        modify_time=info_resp["utime"]
                    )
            return self._delay_get_item(target_path)

        # Step 4: 获取上传凭证
        token_resp = self._request_api(
            "GET",
            "/open/upload/get_token",
            "data"
        )
        if not token_resp:
            logger.warn("【115】获取上传凭证失败")
            return None
        logger.debug(f"【115】上传 Step 4 获取上传凭证结果: {token_resp}")
        # 上传凭证
        endpoint = token_resp.get("endpoint")
        AccessKeyId = token_resp.get("AccessKeyId")
        AccessKeySecret = token_resp.get("AccessKeySecret")
        SecurityToken = token_resp.get("SecurityToken")

        # Step 5: 断点续传
        resume_resp = self._request_api(
            "POST",
            "/open/upload/resume",
            "data",
            data={
                "file_size": file_size,
                "target": target_param,
                "fileid": file_sha1,
                "pick_code": pick_code
            }
        )
        if resume_resp:
            logger.debug(f"【115】上传 Step 5 断点续传结果: {resume_resp}")
            if resume_resp.get("callback"):
                callback = resume_resp["callback"]

        # Step 6: 对象存储上传
        auth = oss2.StsAuth(
            access_key_id=AccessKeyId,
            access_key_secret=AccessKeySecret,
            security_token=SecurityToken
        )
        bucket = oss2.Bucket(auth, endpoint, bucket_name)  # noqa
        # determine_part_size方法用于确定分片大小，设置分片大小为 10M
        part_size = determine_part_size(file_size, preferred_size=10 * 1024 * 1024)

        # 初始化进度条
        logger.info(f"【115】开始上传: {local_path} -> {target_path}，分片大小：{StringUtils.str_filesize(part_size)}")
        progress_callback = transfer_process(local_path.as_posix())

        # 初始化分片
        upload_id = bucket.init_multipart_upload(object_name,
                                                 params={
                                                     "encoding-type": "url",
                                                     "sequential": ""
                                                 }).upload_id
        parts = []
        # 逐个上传分片
        with open(local_path, 'rb') as fileobj:
            part_number = 1
            offset = 0
            while offset < file_size:
                if global_vars.is_transfer_stopped(local_path.as_posix()):
                    logger.info(f"【115】{local_path} 上传已取消！")
                    return None
                num_to_upload = min(part_size, file_size - offset)
                # 调用SizedFileAdapter(fileobj, size)方法会生成一个新的文件对象，重新计算起始追加位置。
                logger.info(f"【115】开始上传 {target_name} 分片 {part_number}: {offset} -> {offset + num_to_upload}")
                result = bucket.upload_part(object_name, upload_id, part_number,
                                            data=SizedFileAdapter(fileobj, num_to_upload))
                parts.append(PartInfo(part_number, result.etag))
                logger.info(f"【115】{target_name} 分片 {part_number} 上传完成")
                offset += num_to_upload
                part_number += 1
                # 更新进度
                progress = (offset * 100) / file_size
                progress_callback(progress)

        # 完成上传
        progress_callback(100)

        # 请求头
        headers = {
            'X-oss-callback': encode_callback(callback["callback"]),
            'x-oss-callback-var': encode_callback(callback["callback_var"]),
            'x-oss-forbid-overwrite': 'false'
        }
        try:
            result = bucket.complete_multipart_upload(object_name, upload_id, parts,
                                                      headers=headers)
            if result.status == 200:
                logger.debug(f"【115】上传 Step 6 回调结果：{result.resp.response.json()}")
                logger.info(f"【115】{target_name} 上传成功")
            else:
                logger.warn(f"【115】{target_name} 上传失败，错误码: {result.status}")
                return None
        except oss2.exceptions.OssError as e:
            if e.code == "FileAlreadyExists":
                logger.warn(f"【115】{target_name} 已存在")
            else:
                logger.error(f"【115】{target_name} 上传失败: {e.status}, 错误码: {e.code}, 详情: {e.message}")
                return None
        # 返回结果
        return self._delay_get_item(target_path)

    def download(self, fileitem: schemas.FileItem, path: Path = None) -> Optional[Path]:
        """
        带实时进度显示的下载
        """
        detail = self.get_item(Path(fileitem.path))
        if not detail:
            logger.error(f"【115】获取文件详情失败: {fileitem.name}")
            return None

        download_info = self._request_api(
            "POST",
            "/open/ufile/downurl",
            "data",
            data={
                "pick_code": detail.pickcode
            }
        )
        if not download_info:
            logger.error(f"【115】获取下载链接失败: {fileitem.name}")
            return None

        download_url = list(download_info.values())[0].get("url", {}).get("url")
        if not download_url:
            logger.error(f"【115】下载链接为空: {fileitem.name}")
            return None

        local_path = path or settings.TEMP_PATH / fileitem.name

        # 获取文件大小
        file_size = detail.size

        # 初始化进度条
        logger.info(f"【115】开始下载: {fileitem.name} -> {local_path}")
        progress_callback = transfer_process(Path(fileitem.path).as_posix())

        try:
            with self.session.get(download_url, stream=True) as r:
                r.raise_for_status()
                downloaded_size = 0

                with open(local_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=self.chunk_size):
                        if global_vars.is_transfer_stopped(fileitem.path):
                            logger.info(f"【115】{fileitem.path} 下载已取消！")
                            return None
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            # 更新进度
                            if file_size:
                                progress = (downloaded_size * 100) / file_size
                                progress_callback(progress)

                # 完成下载
                progress_callback(100)
                logger.info(f"【115】下载完成: {fileitem.name}")

        except requests.exceptions.RequestException as e:
            logger.error(f"【115】下载网络错误: {fileitem.name} - {str(e)}")
            # 删除可能部分下载的文件
            if local_path.exists():
                local_path.unlink()
            return None
        except Exception as e:
            logger.error(f"【115】下载失败: {fileitem.name} - {str(e)}")
            # 删除可能部分下载的文件
            if local_path.exists():
                local_path.unlink()
            return None

        return local_path

    def check(self) -> bool:
        return self.access_token is not None

    def delete(self, fileitem: schemas.FileItem) -> bool:
        """
        删除文件/目录
        """
        try:
            self._request_api(
                "POST",
                "/open/ufile/delete",
                data={
                    "file_ids": int(fileitem.fileid)
                }
            )
            return True
        except requests.exceptions.HTTPError:
            return False

    def rename(self, fileitem: schemas.FileItem, name: str) -> bool:
        """
        重命名文件/目录
        """
        resp = self._request_api(
            "POST",
            "/open/ufile/update",
            data={
                "file_id": int(fileitem.fileid),
                "file_name": name
            }
        )
        if not resp:
            return False
        if resp["state"]:
            return True
        return False

    def get_item(self, path: Path) -> Optional[schemas.FileItem]:
        """
        获取指定路径的文件/目录项
        """
        try:
            resp = self._request_api(
                "POST",
                "/open/folder/get_info",
                "data",
                data={
                    "path": path.as_posix()
                },
                no_error_log=True
            )
            if not resp:
                return None
            return schemas.FileItem(
                storage=self.schema.value,
                fileid=str(resp["file_id"]),
                path=path.as_posix() + ("/" if resp["file_category"] == "0" else ""),
                type="file" if resp["file_category"] == "1" else "dir",
                name=resp["file_name"],
                basename=Path(resp["file_name"]).stem,
                extension=Path(resp["file_name"]).suffix[1:] if resp["file_category"] == "1" else None,
                pickcode=resp["pick_code"],
                size=resp['size_byte'] if resp["file_category"] == "1" else None,
                modify_time=resp["utime"]
            )
        except Exception as e:
            logger.debug(f"【115】获取文件信息失败: {str(e)}")
            return None

    def get_folder(self, path: Path) -> Optional[schemas.FileItem]:
        """
        获取指定路径的文件夹，如不存在则创建
        """

        def __find_dir(_fileitem: schemas.FileItem, _name: str) -> Optional[schemas.FileItem]:
            """
            查找下级目录中匹配名称的目录
            """
            for sub_folder in self.list(_fileitem):
                if sub_folder.type != "dir":
                    continue
                if sub_folder.name == _name:
                    return sub_folder
            return None

        # 是否已存在
        folder = self.get_item(path)
        if folder:
            return folder
        # 逐级查找和创建目录
        fileitem = schemas.FileItem(storage=self.schema.value, path="/")
        for part in path.parts[1:]:
            dir_file = __find_dir(fileitem, part)
            if dir_file:
                fileitem = dir_file
            else:
                dir_file = self.create_folder(fileitem, part)
                if not dir_file:
                    logger.warn(f"【115】创建目录 {fileitem.path}{part} 失败！")
                    return None
                fileitem = dir_file
        return fileitem

    def detail(self, fileitem: schemas.FileItem) -> Optional[schemas.FileItem]:
        """
        获取文件/目录详细信息
        """
        return self.get_item(Path(fileitem.path))

    def copy(self, fileitem: schemas.FileItem, path: Path, new_name: str) -> bool:
        """
        企业级复制实现（支持目录递归复制）
        """
        if fileitem.fileid is None:
            fileitem = self.get_item(Path(fileitem.path))
            if not fileitem:
                logger.warn(f"【115】获取文件 {fileitem.path} 失败！")
                return False
        dest_fileitem = self.get_item(path)
        if not dest_fileitem or dest_fileitem.type != "dir":
            logger.warn(f"【115】目标路径 {path} 不是一个有效的目录！")
            return False

        resp = self._request_api(
            "POST",
            "/open/ufile/copy",
            data={
                "file_id": int(fileitem.fileid),
                "pid": int(dest_fileitem.fileid),
            }
        )
        if not resp:
            return False
        if resp["state"]:
            new_path = Path(path) / fileitem.name
            new_item = self._delay_get_item(new_path)
            if not new_item:
                return False
            if self.rename(new_item, new_name):
                return True
        return False

    def move(self, fileitem: schemas.FileItem, path: Path, new_name: str) -> bool:
        """
        原子性移动操作实现
        """
        if fileitem.fileid is None:
            fileitem = self.get_item(Path(fileitem.path))
            if not fileitem:
                logger.warn(f"【115】获取文件 {fileitem.path} 失败！")
                return False
        dest_fileitem = self.get_item(path)
        if not dest_fileitem or dest_fileitem.type != "dir":
            logger.warn(f"【115】目标路径 {path} 不是一个有效的目录！")
            return False
        resp = self._request_api(
            "POST",
            "/open/ufile/move",
            data={
                "file_ids": int(fileitem.fileid),
                "to_cid": int(dest_fileitem.fileid),
            }
        )
        if not resp:
            return False
        if resp["state"]:
            new_path = Path(path) / fileitem.name
            new_file = self._delay_get_item(new_path)
            if not new_file:
                return False
            if self.rename(new_file, new_name):
                return True
        return False

    def link(self, fileitem: schemas.FileItem, target_file: Path) -> bool:
        pass

    def softlink(self, fileitem: schemas.FileItem, target_file: Path) -> bool:
        pass

    def usage(self) -> Optional[schemas.StorageUsage]:
        """
        获取带有企业级配额信息的存储使用情况
        """
        try:
            resp = self._request_api(
                "GET",
                "/open/user/info",
                "data"
            )
            if not resp:
                return None
            space = resp["rt_space_info"]
            return schemas.StorageUsage(
                total=space["all_total"]["size"],
                available=space["all_remain"]["size"]
            )
        except NoCheckInException:
            return None
