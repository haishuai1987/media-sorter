import re
import threading
import uuid
from pathlib import Path
from threading import Event
from typing import Optional, List, Dict, Callable
from urllib.parse import urljoin

import telebot
from telebot import apihelper
from telebot.types import InputFile, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import InputMediaPhoto

from app.core.config import settings
from app.core.context import MediaInfo, Context
from app.core.metainfo import MetaInfo
from app.log import logger
from app.utils.common import retry
from app.utils.http import RequestUtils
from app.utils.string import StringUtils


class RetryException(Exception):
    pass


class Telegram:
    _ds_url = f"http://127.0.0.1:{settings.PORT}/api/v1/message?token={settings.API_TOKEN}"
    _event = Event()
    _bot: telebot.TeleBot = None
    _callback_handlers: Dict[str, Callable] = {}  # 存储回调处理器
    _user_chat_mapping: Dict[str, str] = {}  # userid -> chat_id mapping for reply targeting
    _bot_username: Optional[str] = None  # Bot username for mention detection
    _escape_chars = r'_*[]()~`>#+-=|{}.!' # Telegram MarkdownV2
    _markdown_escape_pattern = re.compile(f'([{re.escape(_escape_chars)}])') #Telegram MarkdownV2 规则转义特殊字符正则pattern
    def __init__(self, TELEGRAM_TOKEN: Optional[str] = None, TELEGRAM_CHAT_ID: Optional[str] = None, **kwargs):
        """
        初始化参数
        """
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            logger.error("Telegram配置不完整！")
            return
        # Token
        self._telegram_token = TELEGRAM_TOKEN
        # Chat Id
        self._telegram_chat_id = TELEGRAM_CHAT_ID
        # 初始化机器人
        if self._telegram_token and self._telegram_chat_id:
            # telegram bot api 地址，格式：https://api.telegram.org
            if kwargs.get("API_URL"):
                apihelper.API_URL = urljoin(kwargs["API_URL"], '/bot{0}/{1}')
                apihelper.FILE_URL = urljoin(kwargs["API_URL"], '/file/bot{0}/{1}')
            else:
                apihelper.proxy = settings.PROXY
            # bot
            _bot = telebot.TeleBot(self._telegram_token, parse_mode="MarkdownV2")
            # 记录句柄
            self._bot = _bot
            # 获取并存储bot用户名用于@检测
            try:
                bot_info = _bot.get_me()
                self._bot_username = bot_info.username
                logger.info(f"Telegram bot用户名: @{self._bot_username}")
            except Exception as e:
                logger.error(f"获取bot信息失败: {e}")
                self._bot_username = None

            # 标记渠道来源
            if kwargs.get("name"):
                self._ds_url = f"{self._ds_url}&source={kwargs.get('name')}"

            @_bot.message_handler(commands=['start', 'help'])
            def send_welcome(message):
                _bot.reply_to(message, "温馨提示：直接发送名称或`订阅`+名称，搜索或订阅电影、电视剧")

            @_bot.message_handler(func=lambda message: True)
            def echo_all(message):
                # Update user-chat mapping when receiving messages
                self._update_user_chat_mapping(message.from_user.id, message.chat.id)

                # Check if we should process this message
                if self._should_process_message(message):
                    RequestUtils(timeout=15).post_res(self._ds_url, json=message.json)

            @_bot.callback_query_handler(func=lambda call: True)
            def callback_query(call):
                """
                处理按钮点击回调
                """
                try:
                    # Update user-chat mapping for callbacks too
                    self._update_user_chat_mapping(call.from_user.id, call.message.chat.id)

                    # 解析回调数据
                    callback_data = call.data
                    user_id = str(call.from_user.id)

                    logger.info(f"收到按钮回调：{callback_data}，用户：{user_id}")

                    # 发送回调数据给主程序处理
                    callback_json = {
                        "callback_query": {
                            "id": call.id,
                            "from": call.from_user.to_dict(),
                            "message": {
                                "message_id": call.message.message_id,
                                "chat": {
                                    "id": call.message.chat.id,
                                }
                            },
                            "data": callback_data
                        }
                    }

                    # 先确认回调，避免用户看到loading状态
                    _bot.answer_callback_query(call.id)

                    # 发送给主程序处理
                    RequestUtils(timeout=15).post_res(self._ds_url, json=callback_json)

                except Exception as err:
                    logger.error(f"处理按钮回调失败：{str(err)}")
                    _bot.answer_callback_query(call.id, "处理失败，请重试")

            def run_polling():
                """
                定义线程函数来运行 infinity_polling
                """
                try:
                    _bot.infinity_polling(long_polling_timeout=30, logger_level=None)
                except Exception as err:
                    logger.error(f"Telegram消息接收服务异常：{str(err)}")

            # 启动线程来运行 infinity_polling
            self._polling_thread = threading.Thread(target=run_polling, daemon=True)
            self._polling_thread.start()
            logger.info("Telegram消息接收服务启动")

    @property
    def bot_username(self) -> Optional[str]:
        """
        获取Bot用户名
        :return: Bot用户名或None
        """
        return self._bot_username

    def _update_user_chat_mapping(self, userid: int, chat_id: int) -> None:
        """
        更新用户与聊天的映射关系
        :param userid: 用户ID
        :param chat_id: 聊天ID
        """
        if userid and chat_id:
            self._user_chat_mapping[str(userid)] = str(chat_id)

    def _get_user_chat_id(self, userid: str) -> Optional[str]:
        """
        获取用户对应的聊天ID
        :param userid: 用户ID
        :return: 聊天ID或None
        """
        return self._user_chat_mapping.get(str(userid)) if userid else None

    def _should_process_message(self, message) -> bool:
        """
        判断是否应该处理这条消息
        :param message: Telegram消息对象
        :return: 是否处理
        """
        # 私聊消息总是处理
        if message.chat.type == 'private':
            logger.debug(f"处理私聊消息：用户 {message.from_user.id}")
            return True

        # 群聊中的命令消息总是处理（以/开头）
        if message.text and message.text.startswith('/'):
            logger.debug(f"处理群聊命令消息：{message.text[:20]}...")
            return True

        # 群聊中检查是否@了机器人
        if message.chat.type in ['group', 'supergroup']:
            if not self._bot_username:
                # 如果没有获取到bot用户名，为了安全起见处理所有消息
                logger.debug("未获取到bot用户名，处理所有群聊消息")
                return True

            # 检查消息文本中是否包含@bot_username
            if message.text and f"@{self._bot_username}" in message.text:
                logger.debug(f"检测到@{self._bot_username}，处理群聊消息")
                return True

            # 检查消息实体中是否有提及bot
            if message.entities:
                for entity in message.entities:
                    if entity.type == 'mention':
                        mention_text = message.text[entity.offset:entity.offset + entity.length]
                        if mention_text == f"@{self._bot_username}":
                            logger.debug(f"通过实体检测到@{self._bot_username}，处理群聊消息")
                            return True

            # 群聊中没有@机器人，不处理
            logger.debug(f"群聊消息未@机器人，跳过处理：{message.text[:30] if message.text else 'No text'}...")
            return False

        # 其他类型的聊天默认处理
        logger.debug(f"处理其他类型聊天消息：{message.chat.type}")
        return True

    def get_state(self) -> bool:
        """
        获取状态
        """
        return self._bot is not None

    def send_msg(self, title: str, text: Optional[str] = None, image: Optional[str] = None,
                 userid: Optional[str] = None, link: Optional[str] = None,
                 buttons: Optional[List[List[dict]]] = None,
                 original_message_id: Optional[int] = None,
                 original_chat_id: Optional[str] = None) -> Optional[bool]:
        """
        发送Telegram消息
        :param title: 消息标题
        :param text: 消息内容
        :param image: 消息图片地址
        :param userid: 用户ID，如有则只发消息给该用户
        :param link: 跳转链接
        :param buttons: 按钮列表，格式：[[{"text": "按钮文本", "callback_data": "回调数据"}]]
        :param original_message_id: 原消息ID，如果提供则编辑原消息
        :param original_chat_id: 原消息的聊天ID，编辑消息时需要
        :userid: 发送消息的目标用户ID，为空则发给管理员
        """
        if not self._telegram_token or not self._telegram_chat_id:
            return None

        if not title and not text:
            logger.warn("标题和内容不能同时为空")
            return False

        try:
            if title:
                title = self.escape_markdown(title)
            if text:
                # 对text进行Markdown特殊字符转义
                text = self.escape_markdown(text)
                caption = f"*{title}*\n{text}"
            else:
                caption = f"*{title}*"

            if link:
                caption = f"{caption}\n[查看详情]({link})"

            # Determine target chat_id with improved logic using user mapping
            chat_id = self._determine_target_chat_id(userid, original_chat_id)

            # 创建按钮键盘
            reply_markup = None
            if buttons:
                reply_markup = self._create_inline_keyboard(buttons)

            # 判断是编辑消息还是发送新消息
            if original_message_id and original_chat_id:
                # 编辑消息
                return self.__edit_message(original_chat_id, original_message_id, caption, buttons, image)
            else:
                # 发送新消息
                return self.__send_request(userid=chat_id, image=image, caption=caption, reply_markup=reply_markup)

        except Exception as msg_e:
            logger.error(f"发送消息失败：{msg_e}")
            return False

    def _determine_target_chat_id(self, userid: Optional[str] = None,
                                  original_chat_id: Optional[str] = None) -> str:
        """
        确定目标聊天ID，使用用户映射确保回复到正确的聊天
        :param userid: 用户ID
        :param original_chat_id: 原消息的聊天ID
        :return: 目标聊天ID
        """
        # 1. 优先使用原消息的聊天ID (编辑消息场景)
        if original_chat_id:
            return original_chat_id

        # 2. 如果有userid，尝试从映射中获取用户的聊天ID
        if userid:
            mapped_chat_id = self._get_user_chat_id(userid)
            if mapped_chat_id:
                return mapped_chat_id
            # 如果映射中没有，回退到使用userid作为聊天ID (私聊场景)
            return userid

        # 3. 最后使用默认聊天ID
        return self._telegram_chat_id

    def send_medias_msg(self, medias: List[MediaInfo], userid: Optional[str] = None,
                        title: Optional[str] = None, link: Optional[str] = None,
                        buttons: Optional[List[List[Dict]]] = None,
                        original_message_id: Optional[int] = None,
                        original_chat_id: Optional[str] = None) -> Optional[bool]:
        """
        发送媒体列表消息
        :param medias: 媒体信息列表
        :param userid: 用户ID，如有则只发消息给该用户
        :param title: 消息标题
        :param link: 跳转链接
        :param buttons: 按钮列表，格式：[[{"text": "按钮文本", "callback_data": "回调数据"}]]
        :param original_message_id: 原消息ID，如果提供则编辑原消息
        :param original_chat_id: 原消息的聊天ID，编辑消息时需要
        """
        if not self._telegram_token or not self._telegram_chat_id:
            return None

        try:
            index, image, caption = 1, "", "*%s*" % title
            for media in medias:
                if not image:
                    image = media.get_message_image()
                if media.vote_average:
                    caption = "%s\n%s. [%s](%s)\n_%s，%s_" % (caption,
                                                             index,
                                                             media.title_year,
                                                             media.detail_link,
                                                             f"类型：{media.type.value}",
                                                             f"评分：{media.vote_average}")
                else:
                    caption = "%s\n%s. [%s](%s)\n_%s_" % (caption,
                                                          index,
                                                          media.title_year,
                                                          media.detail_link,
                                                          f"类型：{media.type.value}")
                index += 1

            if link:
                caption = f"{caption}\n[查看详情]({link})"

            # Determine target chat_id with improved logic using user mapping
            chat_id = self._determine_target_chat_id(userid, original_chat_id)

            # 创建按钮键盘
            reply_markup = None
            if buttons:
                reply_markup = self._create_inline_keyboard(buttons)

            # 判断是编辑消息还是发送新消息
            if original_message_id and original_chat_id:
                # 编辑消息
                return self.__edit_message(original_chat_id, original_message_id, caption, buttons, image)
            else:
                # 发送新消息
                return self.__send_request(userid=chat_id, image=image, caption=caption, reply_markup=reply_markup)

        except Exception as msg_e:
            logger.error(f"发送消息失败：{msg_e}")
            return False

    def send_torrents_msg(self, torrents: List[Context],
                          userid: Optional[str] = None, title: Optional[str] = None,
                          link: Optional[str] = None, buttons: Optional[List[List[Dict]]] = None,
                          original_message_id: Optional[int] = None,
                          original_chat_id: Optional[str] = None) -> Optional[bool]:
        """
        发送种子列表消息
        :param torrents: 种子信息列表
        :param userid: 用户ID，如有则只发消息给该用户
        :param title: 消息标题
        :param link: 跳转链接
        :param buttons: 按钮列表，格式：[[{"text": "按钮文本", "callback_data": "回调数据"}]]
        :param original_message_id: 原消息ID，如果提供则编辑原消息
        :param original_chat_id: 原消息的聊天ID，编辑消息时需要
        """
        if not self._telegram_token or not self._telegram_chat_id:
            return None

        try:
            index, caption = 1, "*%s*" % title
            image = torrents[0].media_info.get_message_image()
            for context in torrents:
                torrent = context.torrent_info
                site_name = torrent.site_name
                meta = MetaInfo(torrent.title, torrent.description)
                link = torrent.page_url
                title = f"{meta.season_episode} " \
                        f"{meta.resource_term} " \
                        f"{meta.video_term} " \
                        f"{meta.release_group}"
                title = re.sub(r"\s+", " ", title).strip()
                free = torrent.volume_factor
                seeder = f"{torrent.seeders}↑"
                caption = f"{caption}\n{index}.【{site_name}】[{title}]({link}) " \
                          f"{StringUtils.str_filesize(torrent.size)} {free} {seeder}"
                index += 1

            if link:
                caption = f"{caption}\n[查看详情]({link})"

            # Determine target chat_id with improved logic using user mapping
            chat_id = self._determine_target_chat_id(userid, original_chat_id)

            # 创建按钮键盘
            reply_markup = None
            if buttons:
                reply_markup = self._create_inline_keyboard(buttons)

            # 判断是编辑消息还是发送新消息
            if original_message_id and original_chat_id:
                # 编辑消息（种子消息通常没有图片）
                return self.__edit_message(original_chat_id, original_message_id, caption, buttons, image)
            else:
                # 发送新消息
                return self.__send_request(userid=chat_id, image=image, caption=caption, reply_markup=reply_markup)

        except Exception as msg_e:
            logger.error(f"发送消息失败：{msg_e}")
            return False

    @staticmethod
    def _create_inline_keyboard(buttons: List[List[Dict]]) -> InlineKeyboardMarkup:
        """
        创建内联键盘
        :param buttons: 按钮配置，格式：[[{"text": "按钮文本", "callback_data": "回调数据", "url": "链接"}]]
        :return: InlineKeyboardMarkup对象
        """
        keyboard = []
        for row in buttons:
            button_row = []
            for button in row:
                if "url" in button:
                    # URL按钮
                    btn = InlineKeyboardButton(text=button["text"], url=button["url"])
                else:
                    # 回调按钮
                    btn = InlineKeyboardButton(text=button["text"], callback_data=button["callback_data"])
                button_row.append(btn)
            keyboard.append(button_row)
        return InlineKeyboardMarkup(keyboard)

    def answer_callback_query(self, callback_query_id: int, text: Optional[str] = None,
                              show_alert: bool = False) -> Optional[bool]:
        """
        回应回调查询
        """
        if not self._bot:
            return None

        try:
            self._bot.answer_callback_query(callback_query_id, text=text, show_alert=show_alert)
            return True
        except Exception as e:
            logger.error(f"回应回调查询失败：{str(e)}")
            return False

    def delete_msg(self, message_id: int, chat_id: Optional[int] = None) -> Optional[bool]:
        """
        删除Telegram消息
        :param message_id: 消息ID
        :param chat_id: 聊天ID
        :return: 删除是否成功
        """
        if not self._telegram_token or not self._telegram_chat_id:
            return None

        try:
            # 确定要删除消息的聊天ID
            if chat_id:
                target_chat_id = chat_id
            else:
                target_chat_id = self._telegram_chat_id

            # 删除消息
            result = self._bot.delete_message(chat_id=target_chat_id, message_id=int(message_id))
            if result:
                logger.info(f"成功删除Telegram消息: chat_id={target_chat_id}, message_id={message_id}")
                return True
            else:
                logger.error(f"删除Telegram消息失败: chat_id={target_chat_id}, message_id={message_id}")
                return False
        except Exception as e:
            logger.error(f"删除Telegram消息异常: {str(e)}")
            return False

    def __edit_message(self, chat_id: str, message_id: int, text: str,
                       buttons: Optional[List[List[dict]]] = None,
                       image: Optional[str] = None) -> Optional[bool]:
        """
        编辑已发送的消息
        :param chat_id: 聊天ID
        :param message_id: 消息ID
        :param text: 新的消息内容
        :param buttons: 按钮列表
        :param image: 图片URL或路径
        :return: 编辑是否成功
        """
        if not self._bot:
            return None

        try:

            # 创建按钮键盘
            reply_markup = None
            if buttons:
                reply_markup = self._create_inline_keyboard(buttons)

            if image:
                # 如果有图片，使用edit_message_media
                media = InputMediaPhoto(media=image, caption=text, parse_mode="MarkdownV2")
                self._bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=message_id,
                    media=media,
                    reply_markup=reply_markup
                )
            else:
                # 如果没有图片，使用edit_message_text
                self._bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    parse_mode="MarkdownV2",
                    reply_markup=reply_markup
                )
            return True
        except Exception as e:
            logger.error(f"编辑消息失败：{str(e)}")
            return False

    @retry(RetryException, logger=logger)
    def __send_request(self, userid: Optional[str] = None, image="", caption="",
                       reply_markup: Optional[InlineKeyboardMarkup] = None) -> bool:
        """
        向Telegram发送报文
        :param reply_markup: 内联键盘
        """
        if image:
            res = RequestUtils(proxies=settings.PROXY, ua=settings.NORMAL_USER_AGENT).get_res(image)
            if res is None:
                raise Exception("获取图片失败")
            if res.content:
                # 使用随机标识构建图片文件的完整路径，并写入图片内容到文件
                image_file = Path(settings.TEMP_PATH) / "telegram" / str(uuid.uuid4())
                if not image_file.parent.exists():
                    image_file.parent.mkdir(parents=True, exist_ok=True)
                image_file.write_bytes(res.content)
                photo = InputFile(image_file)
                # 发送图片到Telegram
                ret = self._bot.send_photo(chat_id=userid or self._telegram_chat_id,
                                           photo=photo,
                                           caption=caption,
                                           parse_mode="MarkdownV2",
                                           reply_markup=reply_markup)
                if ret is None:
                    raise RetryException("发送图片消息失败")
                return True
        # 按4096分段循环发送消息
        ret = None
        if len(caption) > 4095:
            for i in range(0, len(caption), 4095):
                ret = self._bot.send_message(chat_id=userid or self._telegram_chat_id,
                                             text=caption[i:i + 4095],
                                             parse_mode="MarkdownV2",
                                             reply_markup=reply_markup if i == 0 else None)
        else:
            ret = self._bot.send_message(chat_id=userid or self._telegram_chat_id,
                                         text=caption,
                                         parse_mode="MarkdownV2",
                                         reply_markup=reply_markup)
        if ret is None:
            raise RetryException("发送文本消息失败")
        return True if ret else False

    def register_commands(self, commands: Dict[str, dict]):
        """
        注册菜单命令
        """
        if not self._bot:
            return
        # 设置bot命令
        if commands:
            self._bot.delete_my_commands()
            self._bot.set_my_commands(
                commands=[
                    telebot.types.BotCommand(cmd[1:], str(desc.get("description"))) for cmd, desc in
                    commands.items()
                ]
            )

    def delete_commands(self):
        """
        清理菜单命令
        """
        if not self._bot:
            return
        # 清理菜单命令
        self._bot.delete_my_commands()

    def stop(self):
        """
        停止Telegram消息接收服务
        """
        if self._bot:
            self._bot.stop_polling()
            self._polling_thread.join()
            logger.info("Telegram消息接收服务已停止")

    def escape_markdown(self, text: str) -> str:
        # 按 Telegram MarkdownV2 规则转义特殊字符
        if not isinstance(text, str):
            return str(text) if text is not None else ""
        return self._markdown_escape_pattern.sub(r'\\\1', text)