from __future__ import annotations
import re
from typing import Optional
from aviation_text_normalizer.core.entity import AviationEntity, EntityType
from aviation_text_normalizer.core.match import MatchResult
from aviation_text_normalizer.data.dictionary import DECIMAL_WORDS
from aviation_text_normalizer.utils.number_utils import num_str_to_spoken, token_to_digit


# 将频率与其他普通数值进行整合


# ---------------------------------------------------------------------------
# 频率规范形式的正则：例如 118.75 / 121.9 / 123.450
#
# ^\d{3}\.\d{1,3}$
# - 3 位整数部分：常见 VHF 频段（108~137MHz）通常是三位开头
# - 小数点后 1~3 位：现实语料中常见 1 位（121.9）、2 位（118.75）、
#   以及某些格式会写到 3 位（123.450）
#
# 注意：这里是“识别 token 是否像频率”的轻量规则，不校验范围合法性（如 999.999）。
# 如果需要更严格，可以在后续加范围约束（属于增强，不影响本 FSM 结构）。
_FREQ_RE = re.compile(r"^\d{3}\.\d{1,3}$")

# 频率常见前缀词：
# - contact 118.75
# - frequency 118.75
# - on 118.75
# - freq 118.75
#
# 用集合便于 O(1) 判断，并允许将来增添更多触发词（如 "monitor"）
_PREFIX = {"freq", "frequency", "contact", "on"}


class FrequencyFSM:
    """
    FrequencyFSM（通信频率识别器）

    支持的输入模式：

    1) 规范数字形式（CODE-like）：
       - 118.75
       - 121.9
       - 123.450

    2) 口语逐位读法（SPOKEN-like）：
       - one one eight decimal seven five
       - one two one point niner
       - one one eight dot seven five

       其中 decimal/point/dot 都视为小数点语义（DECIMAL_WORDS）

    3) 带前缀形式：
       - contact 118.75
       - frequency 118.75
       - on 118.75
       - freq 118.75

    输出策略：
    - code：统一输出形如 "118.75"
    - spoken：由 num_str_to_spoken 生成 "one one eight decimal seven five"

    置信度策略：
    - 直接命中规范数字 token（118.75） -> confidence 更高（0.95）
    - 通过口语推断拼接频率 -> confidence 略低（0.90）
    """

    def match(self, tokens: list[str], index: int) -> Optional[MatchResult]:
        """
        从 tokens[index] 位置开始尝试识别频率。

        返回：
        - MatchResult：成功
        - None：不匹配频率

        设计要点：
        - 支持可选前缀（contact/frequency/on）
        - 先尝试“规范数字形式”，因为更可靠、歧义更小
        - 再尝试“口语形式”，相对宽松
        """
        if index >= len(tokens):
            # 防御性：避免越界
            return None

        # start 表示真正开始解析频率的 token 下标
        # 默认从 index 开始；
        # 若 index 是前缀词，则频率从 index+1 开始
        start = index
        if tokens[index].lower() in _PREFIX and index + 1 < len(tokens):
            start = index + 1

        # ------------------------------------------------------------------
        # Case 1：规范数字 token（118.75）
        # ------------------------------------------------------------------
        tok = tokens[start]
        if _FREQ_RE.fullmatch(tok):
            # raw：从 index 到 start+1 拼回原始片段
            # - 如果有前缀：raw = "contact 118.75"
            # - 如果无前缀：raw = "118.75"
            raw = " ".join(tokens[index : start + 1])

            # code：直接使用 tok（已是规范形式）
            # spoken：用工具函数转口语读法
            entity = AviationEntity(
                type=EntityType.FREQUENCY,
                raw=raw,
                code=tok,
                spoken=num_str_to_spoken(tok),
                confidence=0.95,
            )

            # step：
            # - 无前缀时：start==index -> step=1
            # - 有前缀时：start==index+1 -> step=2
            return MatchResult(entity=entity, step=start - index + 1, confidence=0.95)

        # ------------------------------------------------------------------
        # Case 2：口语读法（one one eight decimal seven five）
        # ------------------------------------------------------------------
        # 解析策略：
        # - 先收集小数点前（major）至少 2 位数字，最多 4 位（防止无限吃 token）
        # - 再匹配小数点词（decimal/point/dot）
        # - 再收集小数点后（minor）1~3 位数字
        #
        # 为什么 major 允许 2~4 位？
        # - 常见频率整数部分是 3 位（118/121/123）
        # - 有时语料中可能出现 2 位开头的误写/省略，保留一定宽松度
        # - 4 位是一个上限保护，避免误吞其它数字序列
        j = start
        major: list[str] = []
        while j < len(tokens) and len(major) < 4:
            d = token_to_digit(tokens[j])
            if d is None:
                break
            major.append(d)
            j += 1

        # 必须满足：
        # - major 至少 2 位（否则太容易误匹配普通数字短语）
        # - 后面必须出现 decimal/point/dot
        if len(major) >= 2 and j < len(tokens) and tokens[j].lower() in DECIMAL_WORDS:
            j += 1  # 跳过 decimal 词

            # 小数点后最多 3 位（覆盖 121.9 / 118.75 / 123.450）
            minor: list[str] = []
            while j < len(tokens) and len(minor) < 3:
                d = token_to_digit(tokens[j])
                if d is None:
                    break
                minor.append(d)
                j += 1

            # 小数点后至少要有 1 位数字，否则不算频率
            if minor:
                code = f"{''.join(major)}.{''.join(minor)}"
                raw = " ".join(tokens[index:j])

                entity = AviationEntity(
                    type=EntityType.FREQUENCY,
                    raw=raw,
                    code=code,
                    spoken=num_str_to_spoken(code),
                    confidence=0.90,
                )
                return MatchResult(entity=entity, step=j - index, confidence=0.90)

        # 所有模式都无法匹配 -> None
        return None
