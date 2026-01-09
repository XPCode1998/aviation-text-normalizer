# 让类型注解以“字符串”形式延迟解析。
# 好处：
# 1) 允许在类型注解里引用尚未定义的类（前向引用），比如 "AviationEntity" 自己或互相引用。
# 2) 在 Python 3.10+ 中能减少一些类型注解带来的运行时开销。
# 3) 避免某些循环导入场景下类型注解触发的 NameError。
from __future__ import annotations

# dataclass：用声明式字段生成 __init__ / __repr__ / __eq__ 等样板代码
from dataclasses import dataclass

# Enum：枚举类型；auto() 自动生成枚举值（无需关心具体整数）
from enum import Enum, auto

# Optional[T] 等价于 Union[T, None]：表示该字段可能为空
from typing import Optional


class EntityType(Enum):
    """Aviation semantic entity types.

    表示“实体的语义类别”，用于给解析结果打标签。
    为什么用 Enum：
    - 可读性强：EntityType.RUNWAY 比 "runway" 更规范
    - 可维护性好：新增实体类型只需在这里追加一个枚举项
    - 更安全：避免字符串拼写错误导致的隐蔽 bug
    """

    # 呼号：例如 CSN6889 / china southern 6889
    CALLSIGN = auto()

    # 跑道：例如 RWY 34L
    RUNWAY = auto()

    # 滑行道：例如 TWY M6
    TAXIWAY = auto()

    # 航向：例如 HDG 270
    HEADING = auto()

    # 飞行高度层：例如 FL330
    FLIGHT_LEVEL = auto()

    # 频率：例如 118.75
    FREQUENCY = auto()

    # QNH 气压：例如 QNH 1013
    QNH = auto()

    # 通用数值+单位：例如 5000 ft / 250 kt
    VALUE = auto()


class RenderMode(str, Enum):
    """Output mode for rendering entities.

    RenderMode 定义“输出形式”的枚举，用于控制最终输出文本是：
    - CODE：规范化/结构化输出（便于存储、检索、后处理）
    - SPOKEN：口语可读输出（更贴近 ATC 读法）

    为什么继承 str：
    - 让枚举值本身就是字符串，便于和命令行参数/配置文件交互
    - 例如 RenderMode("CODE") 直接可用
    """

    # 规范化输出：如 RWY 34L, FL330, HDG 270, QNH 1013
    CODE = "CODE"

    # 口语输出：如 runway three four left, flight level three three zero
    SPOKEN = "SPOKEN"


# dataclass 自动生成构造与对比方法
# frozen=True：实例不可变（immutable），创建后字段不可修改
#   - 好处：线程安全、避免被意外篡改、便于缓存/复用
# slots=True：使用 __slots__ 限制属性集合
#   - 好处：降低内存占用、提升属性访问速度
#   - 代价：不能动态添加新属性（但对实体对象来说是优点：更规范）
@dataclass(frozen=True, slots=True)
class AviationEntity:
    """
    Unified entity representation returned by FSMs.

    这是 FSM 的“统一输出结构”，确保所有解析模块输出格式一致。

    字段约定：
    - raw：从 tokens 拼回来的原始片段（用于 debug/回溯）
    - code：机器友好的规范化形式（用于存储、结构化处理）
    - spoken：人类可读的航空口语形式（用于展示/语音合成等）
    - confidence：置信度，越大越确定（用于冲突消解/排序）
    - note：可选备注（记录额外信息/警告/不确定原因等）
    """

    # 实体类型：强制使用 EntityType 枚举，避免自由字符串带来的不一致
    type: EntityType

    # 原始文本片段（通常是 tokens[index:index+step] 拼接得到）
    # 例如 "runway 34L" 或 "heading two seven zero"
    raw: str

    # 规范化形式：便于后续作为结构化字段
    # 例如：RUNWAY -> "RWY 34L"；HEADING -> "HDG 270"；FREQUENCY -> "118.75"
    code: str

    # 口语形式：展示给用户、或用于 TTS（语音）读法
    # 例如：RUNWAY -> "runway three four left"
    spoken: str

    # 置信度：默认 1.0（完全确定）
    # 实际工程中常用范围 [0,1]，
    confidence: float = 1.0

    # 备注字段：用于保存额外信息，如“该匹配为无前缀低置信度推断”等
    note: Optional[str] = None

    def render(self, mode: RenderMode) -> str:
        """
        根据 mode 返回最终输出字符串。

        - mode == RenderMode.SPOKEN：返回 spoken
        - 否则：返回 code（默认/机器友好）

        这样 Parser 在拼接输出时只需要调用 entity.render(mode)，
        不需要关心实体类型和具体格式，从而保持架构的“单一职责”。
        """
        return self.spoken if mode == RenderMode.SPOKEN else self.code
