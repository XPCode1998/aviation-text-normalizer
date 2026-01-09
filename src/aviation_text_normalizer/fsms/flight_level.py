from __future__ import annotations

import re
from typing import Optional

from aviation_text_normalizer.core.entity import AviationEntity, EntityType
from aviation_text_normalizer.core.match import MatchResult
from aviation_text_normalizer.data.dictionary import NUMBER_WORDS
from aviation_text_normalizer.utils.number_utils import digits_to_spoken, token_to_digit


# ---------------------------------------------------------------------------
# Flight Level 正则
#
# ^FL\s*([0-9]{2,3})$
#
# 说明：
# - FL 开头（不区分大小写）
# - 中间允许有或没有空格（防御性处理）
# - 后跟 2~3 位数字（如 80 / 330 / 450）
#
# 典型匹配：
# - FL330
# - fl 350
# - FL 80
#
# 不匹配：
# - F L 330（分成三个 token 的情况，由后续分支处理）
# - flight level three three zero（口语情况）
_FL_RE = re.compile(r"^FL\s*([0-9]{2,3})$", re.IGNORECASE)


class FlightLevelFSM:
    """
    FlightLevelFSM（飞行高度层识别器）

    覆盖的典型输入模式：

    1) 紧凑形式（单 token）：
       - FL330
       - fl350

    2) 分离形式（两个 token）：
       - FL 330

    3) 口语形式（多个 token）：
       - flight level three three zero
       - flight level tree tree zero
       - flight level 3 3 0

    统一输出策略：
    - CODE   : FL330
    - SPOKEN : flight level three three zero

    设计原则：
    - 优先匹配“结构明确、歧义最小”的形式（FL330）
    - 口语解析相对宽松，但置信度略低
    """

    def match(self, tokens: list[str], index: int) -> Optional[MatchResult]:
        """
        从 tokens[index] 位置开始尝试匹配 Flight Level。

        参数：
        - tokens : Tokenizer 输出的 token 列表（通常已小写）
        - index  : 当前解析起始位置

        返回：
        - MatchResult：匹配成功
        - None        ：不匹配 Flight Level
        """
        if index >= len(tokens):
            # 防御性检查：index 越界
            return None

        tok = tokens[index]

        # ------------------------------------------------------------------
        # Case 1: FL330 作为一个 token
        # ------------------------------------------------------------------
        # 这种情况通常来自：
        # - 原始输入本身（FL330）
        # - tokenizer 的 merge pass（fl + 330 -> fl330）
        #
        # tok.replace(" ", "") 是防御性写法：
        # - 即便 tokenizer 没合并空格，也能匹配
        m = _FL_RE.match(tok.replace(" ", ""))
        if m:
            fl = m.group(1)  # 提取数字部分，如 "330"

            # spoken 输出统一用 digits_to_spoken：
            # "330" -> "three three zero"
            spoken = f"flight level {digits_to_spoken(fl)}"

            entity = AviationEntity(
                type=EntityType.FLIGHT_LEVEL,
                raw=tok,                # 原始 token（便于调试）
                code=f"FL{fl}",         # 规范化 CODE
                spoken=spoken,           # 口语输出
                confidence=1,         # 结构明确 → 高置信度
            )
            return MatchResult(entity=entity, step=1, confidence=1)

        # ------------------------------------------------------------------
        # Case 2: FL 330 （分离 token）
        # ------------------------------------------------------------------
        # tokens[index] == "fl"
        # tokens[index+1] == 数字串
        if tok.lower() == "fl" and index + 1 < len(tokens) and tokens[index + 1].isdigit():
            fl = tokens[index + 1]
            raw = " ".join(tokens[index : index + 2])
            spoken = f"flight level {digits_to_spoken(fl)}"

            entity = AviationEntity(
                type=EntityType.FLIGHT_LEVEL,
                raw=raw,
                code=f"FL{fl}",
                spoken=spoken,
                confidence=0.9,  # 比 FL330 略低，但仍然非常可靠
            )
            return MatchResult(entity=entity, step=2, confidence=0.9)

        # ------------------------------------------------------------------
        # Case 3: flight level three three zero（口语形式）
        # ------------------------------------------------------------------
        # 必须严格以 ["flight", "level"] 起始，
        # 这是防止和普通数字短语产生歧义的重要约束
        if tokens[index : index + 2] == ["flight", "level"]:
            j = index + 2
            nums: list[str] = []

            # 向后收集：
            # - 数字词（three / tree / fife / niner 等）
            # - 单个数字 token（"3"）
            while j < len(tokens):
                w = tokens[j].lower()

                # NUMBER_WORDS 包含航空数字读法
                # w.isdigit() 且 len(w)==1 是防御性处理 tokenizer 产出的数字 token
                if w in NUMBER_WORDS or (w.isdigit() and len(w) == 1):
                    nums.append(w)
                    j += 1
                else:
                    break

            # Flight level 至少需要 2 位数字（FL80 / FL330）
            if len(nums) >= 2:
                digits: list[str] = []

                # 将 token 序列统一转换成纯数字字符
                for w in nums:
                    if w.isdigit():
                        digits.append(w)
                    else:
                        digits.append(str(NUMBER_WORDS[w]))

                fl = "".join(digits)
                raw = " ".join(tokens[index:j])

                # spoken 使用 _norm_word 统一航空变体读法
                # tree -> three, fife -> five, niner -> nine
                spoken = "flight level " + " ".join(_norm_word(x) for x in nums)

                entity = AviationEntity(
                    type=EntityType.FLIGHT_LEVEL,
                    raw=raw,
                    code=f"FL{fl}",
                    spoken=spoken,
                    confidence=0.90,  # 口语推断 → 稍低置信度
                )
                return MatchResult(entity=entity, step=j - index, confidence=0.90)

        # 所有模式都不匹配
        return None


def _norm_word(x: str) -> str:
    """
    规范化单个数字读法 token（用于 SPOKEN 输出）。

    目的：
    - 输入端尽量宽松（接受 tree / fife / niner / ait / oh）
    - 输出端尽量统一（three / five / nine / eight / zero）

    输入：
    - x: 数字 token（可能是 digit 或数字读法）

    输出：
    - 标准英语数字读法
    """
    if x.isdigit():
        # 单个数字 token（"3"） → "three"
        return digits_to_spoken(x)

    return {
        "tree": "three",
        "fife": "five",
        "niner": "nine",
        "ait": "eight",
        "oh": "zero",
    }.get(x, x)
