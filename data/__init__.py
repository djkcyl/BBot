from typing import Any, Union
from loguru import logger
from datetime import datetime, timedelta
from peewee import (
    Cast,
    Model,
    CharField,
    IntegerField,
    BooleanField,
    DateTimeField,
    SqliteDatabase,
)


data_version = 2
db = SqliteDatabase("data/data.db")


class BaseModel(Model):
    class Meta:
        database = db


class DynamicPush(BaseModel):
    """动态推送记录"""

    uid = CharField()
    uname = CharField()
    dyn_id = CharField(unique=True)
    dyn_type = CharField()
    dyn_text = CharField(null=True)
    push_groups = IntegerField()
    push_time = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "dynamic_push"


class LivePush(BaseModel):
    """直播推送记录"""

    uid = CharField()
    room_name = CharField(null=True)
    room_area_parent = CharField(null=True)
    room_area = CharField(null=True)
    status = BooleanField()
    push_groups = IntegerField()
    push_time = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "live_push"


class SubList(BaseModel):
    """订阅列表"""

    uid = CharField()
    uname = CharField()
    nick = CharField(null=True)
    group = CharField()
    atall = BooleanField(default=False)
    live = BooleanField(default=True)
    dynamic = BooleanField(default=True)

    class Meta:
        table_name = "sub_list"


class TalkCount(BaseModel):
    """消息统计"""

    time = DateTimeField()
    count = IntegerField()

    class Meta:
        table_name = "talk_count"


class DataVersion(BaseModel):
    """数据库版本记录"""

    version = IntegerField()

    class Meta:
        table_name = "data_version"


db.create_tables([DynamicPush, LivePush, SubList, TalkCount, DataVersion], safe=True)


if not DataVersion.select().exists():
    logger.warning(f"数据库版本记录不存在，正在创建，当前版本：{data_version}")
    DataVersion(version=2).save()
elif DataVersion.get().version != data_version:
    logger.warning(f"数据库版本不匹配，当前版本：{data_version}，数据库版本：{DataVersion.get().version}，正在更新")
    while DataVersion.get().version != data_version:
        if DataVersion.get().version == 1:
            logger.warning("当前数据版本为 1，正在更新至 2")
            # 将 LivePush 表中的 statu 字段改为 status
            db.execute_sql("ALTER TABLE live_push RENAME COLUMN statu TO status")
            DataVersion.update(version=2).execute()

    logger.success("数据库更新完成")


def insert_dynamic_push(
    uid: Union[str, int],
    uname: str,
    dyn_id: Union[str, int],
    dyn_type,
    dyn_text: str,
    push_groups: int,
):
    """在动态推送表中插入一条记录"""
    DynamicPush(
        uid=str(uid),
        uname=uname,
        dyn_id=str(dyn_id),
        dyn_type=dyn_type,
        dyn_text=dyn_text,
        push_groups=push_groups,
    ).save()


def insert_live_push(
    uid: Union[str, int],
    status: bool,
    push_groups: int,
    room_name: str = "",
    room_area_parent: str = "",
    room_area: str = "",
):
    """在直播推送表中插入一条记录"""
    LivePush(
        uid=uid,
        room_name=room_name,
        room_area_parent=room_area_parent,
        room_area=room_area,
        status=status,
        push_groups=push_groups,
    ).save()


def is_dyn_pushed(pushid: Union[str, int]) -> bool:
    """查询某个动态是否推送过"""
    return bool(DynamicPush.select().where(DynamicPush.dyn_id == str(pushid)).exists())


def add_sub(uid: Union[str, int], uname: str, group: Union[str, int]):
    """添加订阅"""
    SubList(uid=str(uid), uname=uname, group=group).save()


def get_all_uid() -> list[str]:
    """获取所有uid"""
    return [i.uid for i in SubList.select(SubList.uid).distinct()]


def get_sub_by_group(group: Union[str, int]) -> list[SubList]:
    """根据群组获取订阅列表"""
    return list(
        SubList.select().where(SubList.group == group).order_by(Cast(SubList.uid, "int"))
    )


def get_sub_by_uid(uid: Union[str, int]) -> list[SubList]:
    """根据uid获取订阅该uid的群"""
    return list(SubList.select().where(SubList.uid == str(uid)).order_by(SubList.group))


def get_sub_data(uid: Union[str, int], group: Union[str, int]) -> SubList:
    """获取订阅数据"""
    return SubList.get(SubList.uid == str(uid), SubList.group == str(group))


def set_uid_name(uid: Union[str, int], uname: str):
    """设置用户名"""
    SubList.update(uname=uname).where(SubList.uid == str(uid)).execute()


def uid_exists(uid: Union[str, int]) -> bool:
    """检查uid是否存在数据库中"""
    return bool(SubList.select().where(SubList.uid == str(uid)).exists())


def uid_in_group(uid: Union[str, int], group: Union[str, int]) -> bool:
    """检查uid是否在该群订阅中"""
    return bool(
        SubList.select().where(SubList.uid == str(uid), SubList.group == str(group)).exists()
    )


def unsub_uid_by_group(uid: Union[str, int], group: Union[str, int]):
    """取消该uid在该群的订阅"""
    SubList.delete().where(SubList.uid == str(uid), SubList.group == str(group)).execute()


def delete_sub_by_uid(uid: Union[str, int]):
    """删除该uid的所有订阅"""
    SubList.delete().where(SubList.uid == str(uid)).execute()


def add_talk_count():
    """添加聊天计数"""
    now_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    # 如果当前时间已经存在记录，则计数加一，否则新建一条记录
    if TalkCount.select().where(TalkCount.time == now_time).exists():
        TalkCount.update(count=TalkCount.count + 1).where(TalkCount.time == now_time).execute()
    else:
        TalkCount(time=now_time, count=1).save()


def get_talk_count(from_time: datetime, to_time: datetime) -> list[dict[str, Any]]:
    """获取并返回指定范围内每小时的聊天计数"""
    return [
        {"time": i.time, "count": i.count}
        for i in TalkCount.select().where(
            TalkCount.time >= from_time, TalkCount.time <= to_time
        )
    ]


def get_push_count(from_time: datetime, to_time: datetime) -> int:
    """获取并返回指定范围内的推送计数"""
    return (
        DynamicPush.select()
        .where(DynamicPush.push_time >= from_time, DynamicPush.push_time <= to_time)
        .count()
    )


print(get_talk_count(datetime.now() - timedelta(days=1), datetime.now() + timedelta(days=1)))
