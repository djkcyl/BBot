import sys


def detect_package():
    try:
        if __nuitka_binary_dir is not None:  # type: ignore
            return "nuitka"
    except NameError:
        return (
            "pyinstaller"
            if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
            else False
        )
    return False


is_package = detect_package()

if is_package == "nuitka":
    from creart import add_creator
    from importlib_metadata import EntryPoint

    _entrys = [
        {
            "name": "broadcast",
            "value": "graia.creart.broadcast:BroadcastCreator",
            "group": "creart.creators",
        },
        {
            "name": "broadcast_behaviour",
            "value": "graia.creart.broadcast:BroadcastBehaviourCreator",
            "group": "creart.creators",
        },
        {
            "name": "loop",
            "value": "graia.creart.broadcast:EventLoopCreator",
            "group": "creart.creators",
        },
        {"name": "saya", "value": "graia.creart.saya:SayaCreator", "group": "creart.creators"},
        {
            "name": "scheduler",
            "value": "graia.creart.scheduler:SchedulerCreator",
            "group": "creart.creators",
        },
        {
            "name": "scheduler_behaviour",
            "value": "graia.creart.scheduler:SchedulerBehaviourCreator",
            "group": "creart.creators",
        },
        {
            "name": "commander",
            "value": "graia.ariadne.message.commander.creart:CommanderCreator",
            "group": "creart.creators",
        },
        {
            "name": "commander_behaviour",
            "value": "graia.ariadne.message.commander.creart:CommanderBehaviourCreator",
            "group": "creart.creators",
        },
    ]
    for entry in _entrys:
        try:
            creator = EntryPoint(**entry).load()
            if creator.available():
                add_creator(creator)
        except Exception:
            pass
