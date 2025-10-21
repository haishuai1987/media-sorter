from typing import Optional, List

from pydantic import BaseModel, Field

from app.schemas.context import Context, MediaInfo
from app.schemas.download import DownloadTask
from app.schemas.file import FileItem
from app.schemas.site import Site
from app.schemas.subscribe import Subscribe


class Workflow(BaseModel):
    """
    工作流信息
    """
    id: Optional[int] = Field(default=None, description="工作流ID")
    name: Optional[str] = Field(default=None, description="工作流名称")
    description: Optional[str] = Field(default=None, description="工作流描述")
    timer: Optional[str] = Field(default=None, description="定时器")
    trigger_type: Optional[str] = Field(default='timer', description="触发类型：timer-定时触发 event-事件触发 manual-手动触发")
    event_type: Optional[str] = Field(default=None, description="事件类型（当trigger_type为event时使用）")
    event_conditions: Optional[dict] = Field(default={}, description="事件条件（JSON格式，用于过滤事件）")
    state: Optional[str] = Field(default=None, description="状态")
    current_action: Optional[str] = Field(default=None, description="已执行动作")
    result: Optional[str] = Field(default=None, description="任务执行结果")
    run_count: Optional[int] = Field(default=0, description="已执行次数")
    actions: Optional[list] = Field(default=[], description="任务列表")
    flows: Optional[list] = Field(default=[], description="任务流")
    add_time: Optional[str] = Field(default=None, description="创建时间")
    last_time: Optional[str] = Field(default=None, description="最后执行时间")

    class Config:
        orm_mode = True


class ActionParams(BaseModel):
    """
    动作基础参数
    """
    loop: Optional[bool] = Field(default=False, description="是否需要循环")
    loop_interval: Optional[int] = Field(default=0, description="循环间隔 (秒)")


class Action(BaseModel):
    """
    动作信息
    """
    id: Optional[str] = Field(default=None, description="动作ID")
    type: Optional[str] = Field(default=None, description="动作类型 (类名)")
    name: Optional[str] = Field(default=None, description="动作名称")
    description: Optional[str] = Field(default=None, description="动作描述")
    position: Optional[dict] = Field(default={}, description="位置")
    data: Optional[dict] = Field(default={}, description="参数")


class ActionExecution(BaseModel):
    """
    动作执行情况
    """
    action: Optional[str] = Field(default=None, description="当前动作（名称）")
    result: Optional[bool] = Field(default=None, description="执行结果")
    message: Optional[str] = Field(default=None, description="执行消息")


class ActionContext(BaseModel):
    """
    动作基础上下文，各动作通用数据
    """
    content: Optional[str] = Field(default=None, description="文本类内容")
    torrents: Optional[List[Context]] = Field(default=[], description="资源列表")
    medias: Optional[List[MediaInfo]] = Field(default=[], description="媒体列表")
    fileitems: Optional[List[FileItem]] = Field(default=[], description="文件列表")
    downloads: Optional[List[DownloadTask]] = Field(default=[], description="下载任务列表")
    sites: Optional[List[Site]] = Field(default=[], description="站点列表")
    subscribes: Optional[List[Subscribe]] = Field(default=[], description="订阅列表")
    execute_history: Optional[List[ActionExecution]] = Field(default=[], description="执行历史")
    progress: Optional[int] = Field(default=0, description="执行进度（%）")


class ActionFlow(BaseModel):
    """
    工作流流程
    """
    id: Optional[str] = Field(default=None, description="流程ID")
    source: Optional[str] = Field(default=None, description="源动作")
    target: Optional[str] = Field(default=None, description="目标动作")
    animated: Optional[bool] = Field(default=True, description="是否动画流程")


class WorkflowShare(BaseModel):
    """
    工作流分享信息
    """
    id: Optional[int] = Field(default=None, description="分享ID")
    share_title: Optional[str] = Field(default=None, description="分享标题")
    share_comment: Optional[str] = Field(default=None, description="分享说明")
    share_user: Optional[str] = Field(default=None, description="分享人")
    share_uid: Optional[str] = Field(default=None, description="分享人唯一ID")
    name: Optional[str] = Field(default=None, description="工作流名称")
    description: Optional[str] = Field(default=None, description="工作流描述")
    timer: Optional[str] = Field(default=None, description="定时器")
    trigger_type: Optional[str] = Field(default=None, description="触发类型")
    event_type: Optional[str] = Field(default=None, description="事件类型")
    event_conditions: Optional[str] = Field(default=None, description="事件条件")
    actions: Optional[str] = Field(default=None, description="任务列表(JSON字符串)")
    flows: Optional[str] = Field(default=None, description="任务流(JSON字符串)")
    context: Optional[str] = Field(default=None, description="执行上下文(JSON字符串)")
    date: Optional[str] = Field(default=None, description="分享时间")
    count: Optional[int] = Field(default=0, description="复用人次")

    class Config:
        orm_mode = True
