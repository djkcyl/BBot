from datetime import datetime
from typing import Union
from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    DateTimeField,
    IntegerField,
    BooleanField,
)


db = SqliteDatabase("data/history.db")


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
    statu = BooleanField()
    push_groups = IntegerField()
    push_time = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "live_push"


db.create_tables([DynamicPush, LivePush], safe=True)


def insert_dynamic_push(
    uid: Union[str, int],
    uname: str,
    dyn_id: Union[str, int],
    dyn_type,
    dyn_text: str,
    push_groups: int,
):
    "在动态推送表中插入一条记录"
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
    statu: bool,
    push_groups: int,
    room_name: str = None,
    room_area_parent: str = None,
    room_area: str = None,
):
    "在直播推送表中插入一条记录"
    LivePush(
        uid=uid,
        room_name=room_name,
        room_area_parent=room_area_parent,
        room_area=room_area,
        statu=statu,
        push_groups=push_groups,
    ).save()


def is_dyn_pushed(pushid: Union[str, int]) -> bool:
    "查询某个动态是否推送过"
    return bool(DynamicPush.select().where(DynamicPush.dyn_id == str(pushid)).exists())
