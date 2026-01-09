# 启用“延迟注解（Postponed Evaluation of Annotations）”
# -------------------------------------------------------
# 含义：
# - 所有类型注解在运行时会被当作字符串处理，而不是立即求值。
#
# 工程意义：
# 1) 允许在类型注解中引用尚未定义的类型（前向引用），
#    比如 FSM / Parser / Entity 之间的相互引用。
# 2) 减少类型注解在运行时带来的额外开销。
# 3) 在复杂项目中可以有效避免循环导入引发的 NameError。
#
# 在“规则引擎 / FSM / 解析器”这类模块化工程中，几乎是标配。
from __future__ import annotations

# dataclass：用于自动生成 __init__ / __repr__ / __eq__ 等样板代码
# 目的：减少样板代码，突出“数据结构本身”而非构造逻辑
from dataclasses import dataclass

# AviationEntity 是 FSM 识别出的“语义实体”的统一表示
# MatchResult 本质上是对 AviationEntity 的一次“匹配包装”
from aviation_text_normalizer.core.entity import AviationEntity


# frozen=True：
#   - MatchResult 实例一旦创建，不允许修改任何字段
#   - 保证 FSM 的输出是“只读的、确定的”
#   - 防止后续 Parser 或其它组件无意中篡改匹配结果
#
# slots=True：
#   - 使用 __slots__ 限定属性集合
#   - 降低内存占用（FSM/Parser 通常会生成大量 MatchResult）
#   - 提高属性访问速度
#   - 明确对象结构（不允许动态塞新字段）
#
# 这是“高频、短生命周期、小对象”的理想配置
@dataclass(frozen=True, slots=True)
class MatchResult:
    """
    FSM match result.

    MatchResult 表示：
    「某一个 FSM，在 tokens 的某个 index 位置，
     成功匹配出了一个 AviationEntity。」

    它不是语义实体本身，而是：
    - 实体（entity）
    - + 匹配元信息（step / confidence）

    Parser 会在多个 FSM 的 MatchResult 中做：
    - 冲突消解
    - 优先级比较
    - 最终选择
    """

    # FSM 识别出的实体对象
    #
    # - 包含 type / raw / code / spoken / confidence 等语义信息
    # - 这是“识别内容本身”
    #
    # MatchResult 对 entity 不做任何修改，只负责包装和转发
    entity: AviationEntity

    # step 表示：
    # - 当前 FSM 在 tokens[index:] 中消费了多少个 token
    #
    # 例如：
    #   tokens = ["runway", "three", "four", "left"]
    #   FSM.match(...) -> step = 4
    #
    # Parser 依靠 step 来决定：
    # - index 向前跳多少
    # - 哪个 FSM 的匹配“覆盖范围更大”（通常优先）
    #
    # step 是解析流程正确性的关键字段
    step: int

    # confidence 是该次匹配的置信度（默认 1.0）
    #
    # 典型用途：
    # - 多个 FSM 在同一位置都能匹配时，进行冲突消解
    # - 区分：
    #     * 有前缀（runway 34L）→ 高置信度
    #     * 无前缀推断（34L）     → 低置信度
    #
    # 在 Parser 中，常见策略是：
    #   1) 优先 step 大的
    #   2) step 相同，优先 confidence 高的
    #
    # 这也是 MatchResult 存在的“核心工程价值”
    confidence: float = 1.0
