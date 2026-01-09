from __future__ import annotations
import re
from typing import Optional
from aviation_text_normalizer.core.entity import AviationEntity, EntityType
from aviation_text_normalizer.core.match import MatchResult
from aviation_text_normalizer.data.dictionary import AIRLINE_ICAO, NUMBER_REVERSE
from aviation_text_normalizer.utils.number_utils import token_to_digit

# -----------------------------------------------------------------------------
# 正则：判断 ICAO 三字码（例如 CSN / CCA / CES）
_ICAO_CODE_RE = re.compile(r"^[A-Z]{3}$")

# 正则：匹配“ICAO 三字码 + 数字串”的紧凑形式（例如 CSN6889）
_ICAO_MIX_RE = re.compile(r"^([A-Z]{3})\s*([0-9]{1,5})$")


class CallsignFSM:
    """
    Callsign FSM（呼号识别器）

    支持的输入模式（典型 ATC/RTF 文本）：

    1) 紧凑模式：
       - CSN6889
       - CCA123
       - CES0123

    2) 分离模式：
       - CSN 6889
       - CSN six eight eight nine
       - CSN 6 8 8 9（tokenizer 有时会产生单独数字 token）

    3) 航空公司英文名称 + 数字：
       - china southern six eight eight nine
       - air china one two three
       - china eastern five five five

    输出策略：
    - CODE：统一输出 ICAO+数字，如 "CSN6889"
    - SPOKEN：输出航空公司名称 + 数字逐位读，如 "china southern six eight eight nine"

    注意：
    - Callsign 与 runway / taxiway 都可能出现 “字母+数字”结构，因此需要：
      * 尽量匹配更具体的呼号模式（3字母 + 1~5位数字）
      * 依赖 Parser 冲突消解（step/confidence）来最终选择
    """

    def match(self, tokens: list[str], index: int) -> Optional[MatchResult]:
        """
        从 tokens[index] 位置开始尝试识别呼号。

        参数：
        - tokens：Tokenizer 产出的 token 列表（通常已统一小写）
        - index：当前扫描位置

        返回：
        - MatchResult：匹配成功
        - None：匹配失败

        设计原则：
        - match 必须“只读 tokens”
        - 对边界条件要非常谨慎：任何越界都要提前检查
        - 即使输入不规范，也尽量返回 None 而不是抛异常
        """
        if index >= len(tokens):
            # 防御性检查：防止 index 越界
            return None

        # 当前 token（可能是 "csn6889" 或 "csn" 或 "china" 等）
        t0 = tokens[index]

        # 呼号判定需要用大写规则，因此统一转大写
        # 例如：tokenizer 把 "CSN" 变成 "csn"，这里转回来
        t0u = t0.upper()

        # Case 1：紧凑 token（CSN6889）
        m = _ICAO_MIX_RE.match(t0u)
        if m:
            # 正则分组：
            # group(1) = ICAO code，例如 "CSN"
            # group(2) = digits，例如 "6889"
            icao, digits = m.group(1), m.group(2)

            # 取航空公司英文名；若字典无该 ICAO code，则回退为 code 本身
            # 这样至少保证 spoken 不会为空
            name = AIRLINE_ICAO.get(icao, icao)

            # 数字逐位读（"6889" -> "six eight eight nine"）
            spoken_digits = " ".join(NUMBER_REVERSE.get(ch, ch) for ch in digits)

            # 构造统一实体：
            # raw：原 token（如 "csn6889"）
            # code：规范化（如 "CSN6889"）
            # spoken：口语读法（如 "china southern six eight eight nine"）
            entity = AviationEntity(
                type=EntityType.CALLSIGN,
                raw=t0,
                code=f"{icao}{digits}",
                spoken=f"{name} {spoken_digits}",
                confidence=1,
            )
            # step=1：只消耗当前 token
            return MatchResult(entity=entity, step=1, confidence=1)

        # Case 2：分离模式（CSN 6889 / CSN six eight eight nine）
        if _ICAO_CODE_RE.fullmatch(t0u):
            j = index + 1  # 从下一 token 开始收集
            digits: list[str] = []

            while j < len(tokens):
                tok = tokens[j]

                # 如果 token 直接是数字串（例如 "6889"）
                # 这里的策略是直接 append 整个 tok
                # 注意：如果 tok 是 "6889"，那 digits.append("6889")，后续 join 会得到 "6889"
                # 这等价于“整体数字串”被保留。对呼号来说是合理的。
                if tok.isdigit():
                    digits.append(tok)
                    j += 1
                    continue

                # 否则尝试把 token 解析成单个数字（例如 "six" -> "6"）
                d = token_to_digit(tok)
                if d is None:
                    # 遇到非数字相关 token，终止收集
                    break

                digits.append(d)
                j += 1

            # 若成功收集到至少一个数字片段，则认为匹配成功
            if digits:
                icao = t0u
                dstr = "".join(digits)  # 将收集到的数字片段拼成完整数字串

                name = AIRLINE_ICAO.get(icao, icao)
                spoken_digits = " ".join(NUMBER_REVERSE.get(ch, ch) for ch in dstr)

                # raw：用原 tokens 拼回，用于 debug/回溯
                raw = " ".join(tokens[index:j])

                entity = AviationEntity(
                    type=EntityType.CALLSIGN,
                    raw=raw,
                    code=f"{icao}{dstr}",
                    spoken=f"{name} {spoken_digits}",
                    confidence=0.90,  # 分离模式，稍低置信度
                )
                # step = j-index：消耗 ICAO + 若干数字 token
                return MatchResult(entity=entity, step=j - index, confidence=0.90)

        # Case 3：航空公司名称 + 数字（china southern six eight eight nine）
        for icao, name in AIRLINE_ICAO.items():
            nt = name.split()

            # 如果当前 tokens[index:...] 与航空公司名称 token 序列不一致，跳过
            if tokens[index : index + len(nt)] != nt:
                continue

            # 名称匹配成功，开始在名称后面收集数字
            j = index + len(nt)
            digits: list[str] = []

            while j < len(tokens):
                d = token_to_digit(tokens[j])
                if d is None:
                    break
                digits.append(d)
                j += 1

            # 若收集到数字，认为是呼号（例如 "china southern 6889"）
            if digits:
                dstr = "".join(digits)
                spoken_digits = " ".join(NUMBER_REVERSE.get(ch, ch) for ch in dstr)
                raw = " ".join(tokens[index:j])

                entity = AviationEntity(
                    type=EntityType.CALLSIGN,
                    raw=raw,
                    code=f"{icao}{dstr}",
                    spoken=f"{name} {spoken_digits}",
                    confidence=0.85,
                )
                return MatchResult(entity=entity, step=j - index, confidence=0.85)

        # 三种模式都无法匹配 -> None
        return None

