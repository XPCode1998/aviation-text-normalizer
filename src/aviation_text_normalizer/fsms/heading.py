from __future__ import annotations

import re
from typing import Optional

from aviation_text_normalizer.core.entity import AviationEntity, EntityType
from aviation_text_normalizer.core.match import MatchResult
from aviation_text_normalizer.utils.number_utils import digits_to_spoken, token_to_digit


# ---------------------------------------------------------------------------
# 航向前缀词集合
#
# 在真实 ATC 通话中，航向通常由以下词引导：
# - "heading"
# - "hdg"（常见缩写）
#
# 使用 set 便于 O(1) 判断，并方便未来扩展（如 "turn heading"）
_HDR_PREFIX = {"heading", "hdg"}

# 航向数字正则：
# ^\d{1,3}$
#
# 用于匹配：
# - 0 ~ 360 范围内常见表示（这里不做范围校验）
# - 例如 "9", "90", "270"
#
# 范围合法性（0~360）不在 FSM 层处理，
# FSM 只负责“结构识别”，不负责“飞行规则校验”
_HDG_RE = re.compile(r"^\d{1,3}$")


class HeadingFSM:
    """
    HeadingFSM（航向识别器）

    支持的典型输入模式：

    1) 数字形式：
       - heading 270
       - hdg 090
       - heading 9

    2) 口语形式：
       - heading two seven zero
       - heading zero niner zero
       - heading 2 7 0（Tokenizer 拆成单数字 token 的情况）

    统一输出策略：
    - CODE   : "HDG 270"（三位补零）
    - SPOKEN : "heading two seven zero"

    设计原则：
    - 必须以明确前缀（heading/hdg）开始，避免误把普通数字当航向
    - 先匹配“直接数字形式”，再匹配“口语形式”
    - 所有航向都统一补齐三位（符合 ATC 规范）
    """

    def match(self, tokens: list[str], index: int) -> Optional[MatchResult]:
        """
        从 tokens[index] 开始尝试识别航向。

        参数：
        - tokens : Tokenizer 输出的 token 列表
        - index  : 当前扫描位置

        返回：
        - MatchResult：识别成功
        - None        ：当前位置不是航向结构
        """
        if index >= len(tokens):
            # 防御性：index 越界
            return None

        # 必须以航向前缀词开头
        # 若当前 token 不是 heading/hdg，直接返回 None
        if tokens[index].lower() not in _HDR_PREFIX:
            return None

        # ------------------------------------------------------------------
        # Case 1：heading 270（数字直接给出）
        # ------------------------------------------------------------------
        # 这是最明确、歧义最小的航向表达
        if index + 1 < len(tokens) and _HDG_RE.fullmatch(tokens[index + 1]):
            # 提取数字并补足三位：
            # "9"  -> "009"
            # "90" -> "090"
            # "270"-> "270"
            deg = tokens[index + 1].zfill(3)

            # raw：保留原始 token 组合，便于调试/回溯
            raw = " ".join(tokens[index : index + 2])

            # spoken：始终使用逐位读法
            spoken = f"heading {digits_to_spoken(deg)}"

            entity = AviationEntity(
                type=EntityType.HEADING,
                raw=raw,
                code=f"HDG {deg}",
                spoken=spoken,
                confidence=0.95,  # 结构明确 → 高置信度
            )

            # step=2：消耗 "heading" + 数字
            return MatchResult(entity=entity, step=2, confidence=0.95)

        # ------------------------------------------------------------------
        # Case 2：口语形式（heading two seven zero）
        # ------------------------------------------------------------------
        # 解析策略：
        # - 从 prefix 后一个 token 开始
        # - 逐个尝试解析数字词（two / seven / zero）或单数字 token
        # - 最多收集 3 位（航向最多三位）
        j = index + 1
        digits: list[str] = []

        while j < len(tokens) and len(digits) < 3:
            d = token_to_digit(tokens[j])
            if d is None:
                # 一旦遇到非数字语义 token，停止解析
                break
            digits.append(d)
            j += 1

        # 至少需要 2 位数字，才认为是合理航向：
        # - heading two zero（020）✔
        # - heading seven（7）✘（太短，容易误判）
        if len(digits) >= 2:
            # 拼接并补齐三位
            deg = "".join(digits).zfill(3)

            raw = " ".join(tokens[index:j])
            spoken = f"heading {digits_to_spoken(deg)}"

            entity = AviationEntity(
                type=EntityType.HEADING,
                raw=raw,
                code=f"HDG {deg}",
                spoken=spoken,
                confidence=0.90,  # 口语推断 → 略低置信度
            )

            # step=j-index：prefix + 若干数字 token
            return MatchResult(entity=entity, step=j - index, confidence=0.90)

        # 两种模式都不成立 → 非航向
        return None
