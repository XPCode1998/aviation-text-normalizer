from __future__ import annotations
import re
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Token 分割用的正则表达式
#
# 模式解释（从左到右）：
# 1) [A-Za-z]+
#    - 连续的英文字母
#    - 用于识别单词（如 runway, heading, csn）
#
# 2) \d+(?:\.\d+)?
#    - 整数或小数
#    - 用于识别数值（如 118.75, 330）
#
# 3) [^\sA-Za-z\d]+
#    - 既不是空白，也不是字母或数字的连续字符
#    - 用于捕获标点、符号（如 ",", "!", "-", "/" 等）
#
# 使用“或（|）”连接，确保文本能被完整切分、不遗漏字符
#
# 重要设计点：
# - tokenizer 并不直接“理解语义”
# - 只保证：切分稳定、规则清晰、可预测
#
# 语义合并（如 CSN + 6889 -> CSN6889）应由后续 FSM 或 merge pass 处理
_TOKEN_RE = re.compile(r"[A-Za-z]+|\d+(?:\.\d+)?|[^\sA-Za-z\d]+")


@dataclass(frozen=True, slots=True)
class Tokenizer:
    """
    Normalize and tokenize ATC text.

    - 输入：原始 ATC 文本（可能包含噪声、标点、不规则空格）
    - 输出：稳定、可预测的 token 序列（供 FSM 使用）
    """

    def normalize(self, text: str) -> str:
        """
        对原始文本进行“规范化预处理”。
        """

        # 去除首尾空白（避免首尾产生空 token）
        s = text.strip()

        # 将常见分隔符替换为空格
        s = re.sub(r"[,\;:\(\)\[\]\{\}]", " ", s)

        # 将不同 Unicode 破折号统一为 ASCII "-"
        s = s.replace("–", "-").replace("—", "-")

        # 压缩连续空白为单个空格
        s = re.sub(r"\s+", " ", s).strip()

        return s

    def tokenize(self, text: str) -> list[str]:
        """
        将规范化后的文本切分为 token 列表。
        """

        # 使用全局正则模式进行扫描式切分
        raw_tokens = _TOKEN_RE.findall(text)

        # tokens：最终输出的 token 列表
        tokens: list[str] = []

        for tok in raw_tokens:
            # 如果是纯字母 token：
            # - 统一转为小写
            #
            # 这样 FSM 可以用小写规则匹配，避免大小写噪声
            if re.fullmatch(r"[A-Za-z]+", tok):
                tokens.append(tok.lower())
            else:
                # 数字 / 小数 / 符号 token 原样保留
                tokens.append(tok)

        # 丢弃“纯标点 token”
        tokens = [t for t in tokens if not re.fullmatch(r"[^\w\.]+", t)]

        return tokens
