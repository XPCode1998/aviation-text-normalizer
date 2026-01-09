from __future__ import annotations

import re
from typing import Optional

from aviation_text_normalizer.core.entity import AviationEntity, EntityType
from aviation_text_normalizer.core.match import MatchResult
from aviation_text_normalizer.utils.number_utils import digits_to_spoken, token_to_digit


# ---------------------------------------------------------------------------
# QNH 数值正则
#
# ^\d{4}$
#
# QNH（场压）在航空通话中通常以四位数字给出，例如：
# - 1013
# - 1008
# - 0998（某些地区会出现，前导零通常仍读出）
#
# 这里不校验气压范围（如 950~1050 hPa），
# FSM 层只负责“结构识别”，不做物理/气象校验。
_QNH_RE = re.compile(r"^\d{4}$")


class QNHFSM:
    """
    QNHFSM（机场气压 QNH 识别器）

    支持的输入模式：

    1) 数字形式：
       - qnh 1013
       - qnh 0998

    2) 口语形式：
       - qnh one zero one three
       - qnh nine eight seven six

    输出统一格式：
    - CODE   : "QNH 1013"
    - SPOKEN : "qnh one zero one three"

    设计原则：
    - QNH 必须以明确前缀 "qnh" 开始（极强语义锚点）
    - 必须严格是 4 位数字（防止误把普通数字当 QNH）
    - 数字形式优先，口语形式兜底
    """

    def match(self, tokens: list[str], index: int) -> Optional[MatchResult]:
        """
        从 tokens[index] 开始尝试匹配 QNH。

        参数：
        - tokens : Tokenizer 输出的 token 列表
        - index  : 当前扫描位置

        返回：
        - MatchResult：成功识别 QNH
        - None        ：不匹配 QNH
        """
        # 防御性检查：
        # - index 越界
        # - 当前 token 不是 "qnh"（大小写不敏感）
        if index >= len(tokens) or tokens[index].lower() != "qnh":
            return None

        # ------------------------------------------------------------------
        # Case 1：数字形式（qnh 1013）
        # ------------------------------------------------------------------
        # 最明确、最规范的形式，优先匹配
        if index + 1 < len(tokens) and _QNH_RE.fullmatch(tokens[index + 1]):
            v = tokens[index + 1]  # 四位数字气压值
            raw = " ".join(tokens[index : index + 2])

            entity = AviationEntity(
                type=EntityType.QNH,
                raw=raw,
                code=f"QNH {v}",
                spoken=f"qnh {digits_to_spoken(v)}",
                confidence=0.95,  # 数字直接给出 → 高置信度
            )

            # step=2：消耗 "qnh" + 数值 token
            return MatchResult(entity=entity, step=2, confidence=0.95)

        # ------------------------------------------------------------------
        # Case 2：口语形式（qnh one zero one three）
        # ------------------------------------------------------------------
        # 解析策略：
        # - 从 "qnh" 后一个 token 开始
        # - 尝试逐位解析数字读法
        # - 严格要求恰好 4 位（这是 QNH 的强约束）
        j = index + 1
        digs: list[str] = []

        while j < len(tokens) and len(digs) < 4:
            d = token_to_digit(tokens[j])
            if d is None:
                # 一旦出现非数字语义 token，终止解析
                break
            digs.append(d)
            j += 1

        # 必须恰好 4 位数字，才能构成合法 QNH
        if len(digs) == 4:
            v = "".join(digs)
            raw = " ".join(tokens[index:j])

            entity = AviationEntity(
                type=EntityType.QNH,
                raw=raw,
                code=f"QNH {v}",
                spoken=f"qnh {digits_to_spoken(v)}",
                confidence=0.90,  # 口语推断 → 稍低置信度
            )

            # step=j-index：消耗 "qnh" + 4 个数字 token
            return MatchResult(entity=entity, step=j - index, confidence=0.90)

        # 其他情况（位数不足 / 夹杂非数字 token）一律视为不匹配
        return None
