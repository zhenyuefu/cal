import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler

from ics import Calendar, Container, ContentLine

from api.data import parcours_s1
from api.utils import filter_ue_parcours, handle_get, load_calendar
from api.index_loader import load_index_or_none, build_ics

# -------------- 性能优化 说明 --------------
# 之前实现：每次请求都会重新读取并解析 .ics 文件，
# 然后通过 timeline.start_after 再次迭代事件，导致 I/O 与解析开销大。
# 现在：在模块加载阶段预读所有需要的日历并做日期过滤与缓存，
# 请求阶段仅做字符串匹配与正则过滤，显著降低冷启动后的平均延迟。
# ------------------------------------------

start_date = datetime.fromisoformat("2023-09-04T12:05:23+02:00")

# Lazy + JSON 索引优先：只有请求涉及的专业才加载；若存在索引则避免解析 ICS
CALENDARS: dict[str, Calendar] = {}
FILTERED_EVENTS: dict[str, list] = {}
IS_INDEX_MODE: dict[str, bool] = {}


def _ensure_parcour_loaded(parcour: str):
    if parcour in FILTERED_EVENTS:
        return
    # 尝试加载 JSON 索引
    indexed = load_index_or_none("M1", parcour)
    if indexed is not None:
        FILTERED_EVENTS[parcour] = indexed  # list[dict]
        IS_INDEX_MODE[parcour] = True
        return
    # 回退解析 ICS
    cal = load_calendar(parcour)
    CALENDARS[parcour] = cal
    FILTERED_EVENTS[parcour] = list(cal.timeline.start_after(start_date))
    IS_INDEX_MODE[parcour] = False


def _iter_events_for_parcour(parcour: str):
    _ensure_parcour_loaded(parcour)
    return FILTERED_EVENTS.get(parcour, [])


def filter_cours(ue_group: dict, majour: str):
    # 如果所有涉及 parcours 都走 JSON 索引，可以直接构建原始 ICS 文本

    parcours_ue = filter_ue_parcours(ue_group, parcours_s1)

    # 预编译每个 UE 的排除模式，避免在事件循环中重复编译
    compiled_patterns: dict[str, re.Pattern] = {}
    for ue_name, group_code in ue_group.items():
        # 仅用于非索引 (ICS) 场景回退；索引场景用 groups 集合判断
        try:
            compiled_patterns[ue_name] = re.compile(rf"T\w{{1,2}}(?=\d)(?!{group_code})")
        except re.error:
            compiled_patterns[ue_name] = re.compile(r"^$")

    collected_index_events: list[dict] = []

    # 尝试快速路径：全部 parcours 使用索引 -> 不实例化 Calendar
    all_index = True
    for parcour in parcours_ue.keys():
        _ensure_parcour_loaded(parcour)
        if not IS_INDEX_MODE.get(parcour):
            all_index = False
            break

    if not all_index:
        # 回退使用 ics.Calendar
        cal = Calendar()
        cal.extra = Container(
            "VCALENDAR", [ContentLine("X-WR-CALNAME", value="M1 " + majour)]
        )
    else:
        cal = None  # type: ignore

    for parcour in parcours_ue.keys():
        for event in _iter_events_for_parcour(parcour):
            if IS_INDEX_MODE.get(parcour):
                summary = event.get("summary", "")  # type: ignore
            else:
                summary = getattr(event, "summary", "") or ""

            # 忽略英语课
            if "anglais" in summary or "Anglais" in summary:
                continue

            # 本专业公共课：包含专业名（与原逻辑一致）
            if majour == parcour and parcour in summary:
                if IS_INDEX_MODE.get(parcour):
                    collected_index_events.append(event)  # type: ignore
                else:
                    cal.events.add(event)  # type: ignore
                continue

            # 针对该 parcours 下的各 UE 做匹配
            for ue in parcours_ue[parcour]:
                if ue in summary:
                    if IS_INDEX_MODE.get(parcour):
                        # 索引模式使用预计算 groups
                        groups = event.get("groups", [])  # type: ignore
                        target = ue_group.get(ue)
                        if groups and not (set(groups) == {target}):
                            # 存在组且并非全部为目标组 -> 排除
                            continue
                        collected_index_events.append(event)  # type: ignore
                    else:
                        pattern = compiled_patterns.get(ue)
                        if pattern and pattern.search(summary):
                            continue
                        cal.events.add(event)  # type: ignore
                    break

    if cal is not None:
        return cal

    # 仅索引模式：根据过滤后事件列表生成 ICS 文本（放入一个伪 Calendar 容器兼容 handle_get）
    # 需要确保事件字段为 dtstart/dtend；过滤掉不相关的索引字段
    ics_text = build_ics("M1 " + majour, collected_index_events)
    # 用最小的包装对象，提供 serialize()
    class _Wrapper:
        def __init__(self, text: str):
            self._t = text

        def serialize(self):
            return self._t

    return _Wrapper(ics_text)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        handle_get(self, filter_cours)
