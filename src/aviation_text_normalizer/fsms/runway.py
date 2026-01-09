from __future__ import annotations

import re
from typing import Optional

from aviation_text_normalizer.core.entity import AviationEntity, EntityType
from aviation_text_normalizer.core.match import MatchResult
from aviation_text_normalizer.utils.number_utils import digits_to_spoken, token_to_digit


# ---------------------------------------------------------------------------
# 跑道前缀集合
#
# 真实 ATC 语料中跑道通常由这些词引导：
# - runway
# - rwy（常见缩写）
#
# 使用 set 便于 O(1) 判断，并方便未来扩展（如 "runway-in-use"）
_RW_PREFIX = {"runway", "rwy"}

# 跑道编号形式正则（带可选侧向字母）：
# ^\d{2}([LRC])?$
#
# - 两位数字：01 ~ 36（本 FSM 不做范围校验，仅做结构识别）
# - 可选方向字母：L/R/C（Left/Right/Center）
#
# 典型匹配：
# - "34"
# - "34L"
# - "01R"
#
# 不匹配：
# - "4"（少于两位，避免误判）
# - "340"（三位数字，明显不是跑道）
_RW_CODE_RE = re.compile(r"^\d{2}([LRC])?$")

# 紧凑形式正则（必须带侧向字母）：
# ^\d{2}[LRC]$
#
# 用于识别没有显式前缀的跑道 token（例如 "34L"），
# 但这种识别容易与其它字母数字结构冲突，因此给低置信度。
_RW_TIGHT_RE = re.compile(r"^\d{2}[LRC]$")

# 方向词到方向码的映射
# 口语侧向：left/right/center -> L/R/C
_DIR_WORD_TO_CODE = {"left": "L", "right": "R", "center": "C"}

# 方向码到口语词的映射（用于 spoken 输出）
# L/R/C -> left/right/center
_DIR_CODE_TO_WORD = {"L": "left", "R": "right", "C": "center"}


class RunwayFSM:
    """
    RunwayFSM（跑道识别器）

    支持的典型输入模式：

    1) 带前缀的编码形式（最可靠）：
       - runway 34L
       - rwy 34
       - runway 01R

    2) 带前缀的口语形式：
       - runway three four left
       - runway zero one right
       （注意：本实现只收集两位数字 + 可选侧向）

    3) 无前缀的紧凑形式（低置信度兜底）：
       - 34L
       - 01R
       （容易与其他结构冲突，因此必须低置信度）

    输出策略：
    - CODE   : "RWY 34L" / "RWY 34"
    - SPOKEN : "runway three four left" / "runway three four"

    置信度策略：
    - 带前缀 + 合法结构 → 高（0.95 / 0.90）
    - 无前缀直接 token → 低（0.75），避免抢占 callsign/其他实体
    """

    def match(self, tokens: list[str], index: int) -> Optional[MatchResult]:
        """
        从 tokens[index] 开始尝试识别跑道。

        返回：
        - MatchResult：成功识别
        - None        ：不匹配跑道

        设计要点：
        - 优先匹配“带前缀”的结构（更可靠、更少歧义）
        - 无前缀结构仅作为兜底，并给低置信度
        """
        if index >= len(tokens):
            # 防御性检查：index 越界
            return None

        # ------------------------------------------------------------------
        # Case 1：带前缀 runway/rwy
        # ------------------------------------------------------------------
        # 只要当前 token 是 runway/rwy，则进入“前缀后解析”分支。
        # 这样能保证“跑道解析必须有语义锚点”，召回与精度更平衡。
        if tokens[index].lower() in _RW_PREFIX:
            return self._match_after_prefix(tokens, index)

        # ------------------------------------------------------------------
        # Case 2：无前缀的紧凑形式（34L）
        # ------------------------------------------------------------------
        # 这种形式可能出现在某些转录文本或简写里：
        # - "taxi to 34L"
        #
        # 但也可能与其它结构冲突（例如 taxiway、callsign 的 alnum 结构）。
        # 因此：
        # - 只允许“必须带 L/R/C”的紧凑 token
        # - 且给予低置信度
        t = tokens[index].upper()
        if _RW_TIGHT_RE.fullmatch(t):
            num, side = t[:2], t[2]
            raw = tokens[index]

            # CODE 输出统一为 "RWY <num><side>"
            code = f"RWY {num}{side}"

            # SPOKEN 输出为 "runway <digits> <left/right/center>"
            spoken = f"runway {digits_to_spoken(num)} {_DIR_CODE_TO_WORD[side]}"

            entity = AviationEntity(
                type=EntityType.RUNWAY,
                raw=raw,
                code=code,
                spoken=spoken,
                confidence=0.75,  # 无前缀 → 低置信度
            )
            return MatchResult(entity=entity, step=1, confidence=0.75)

        # 其他情况不匹配跑道
        return None

    def _match_after_prefix(self, tokens: list[str], index: int) -> Optional[MatchResult]:
        """
        处理带前缀 runway/rwy 的情况。

        index 指向前缀词（runway 或 rwy），后续 token 才是跑道编号/侧向信息。
        """
        if index + 1 >= len(tokens):
            # 前缀后没有内容，无法匹配
            return None

        # 前缀后的第一个 token（可能是 "34L" 或 "34" 或 "three"）
        t1 = tokens[index + 1].upper()

        # ------------------------------------------------------------------
        # Case 1：runway 34L / runway 34（编码形式）
        # ------------------------------------------------------------------
        # 这是最常见的规范形式，优先处理
        if _RW_CODE_RE.fullmatch(t1):
            num = t1[:2]  # 两位跑道编号
            side = t1[2] if len(t1) == 3 else ""  # 可选 L/R/C

            raw = " ".join(tokens[index : index + 2])
            code = f"RWY {num}{side}"

            # spoken 默认只读数字部分
            spoken = f"runway {digits_to_spoken(num)}"
            if side:
                spoken += f" {_DIR_CODE_TO_WORD[side]}"

            entity = AviationEntity(
                type=EntityType.RUNWAY,
                raw=raw,
                code=code,
                spoken=spoken,
                confidence=0.95,  # 带前缀 + 编码形式 → 最高置信度
            )
            return MatchResult(entity=entity, step=2, confidence=0.95)

        # ------------------------------------------------------------------
        # Case 2：runway three four left（口语形式）
        # ------------------------------------------------------------------
        # 解析策略：
        # - 前缀后读取两位数字（逐位读法）
        # - 可选读取侧向词（left/right/center）
        #
        # 这里要求必须有两位数字，避免误把 “runway left” 等噪声识别为跑道
        d1 = token_to_digit(tokens[index + 1])
        d2 = token_to_digit(tokens[index + 2]) if index + 2 < len(tokens) else None
        if d1 is not None and d2 is not None:
            # 拼成两位跑道编号，例如 "3"+"4" -> "34"
            num = d1 + d2

            # j 指向可能的侧向词位置（第三个 token）
            j = index + 3
            side = ""

            # 若存在侧向词 left/right/center，则读取并转为 L/R/C
            if j < len(tokens) and tokens[j].lower() in _DIR_WORD_TO_CODE:
                side = _DIR_WORD_TO_CODE[tokens[j].lower()]
                j += 1

            raw = " ".join(tokens[index:j])
            code = f"RWY {num}{side}"

            spoken = f"runway {digits_to_spoken(num)}"
            if side:
                spoken += f" {_DIR_CODE_TO_WORD[side]}"

            entity = AviationEntity(
                type=EntityType.RUNWAY,
                raw=raw,
                code=code,
                spoken=spoken,
                confidence=0.90,  # 口语推断 → 略低于编码形式
            )
            return MatchResult(entity=entity, step=j - index, confidence=0.90)

        # 无法匹配跑道
        return None
