from __future__ import annotations
from typing import Optional, Protocol
from aviation_text_normalizer.core.match import MatchResult


class FSM(Protocol):
    """
    FSM interface: try matching tokens from index.
    """

    def match(self, tokens: list[str], index: int) -> Optional[MatchResult]:
        """
        尝试从 tokens[index] 开始进行匹配。

        Parameters
        ----------
        tokens : list[str]
            Tokenizer 产出的 token 列表。
            Parser 通常会先对输入文本进行 normalize/tokenize,
            从而让 tokens 具有更稳定、可预测的形式（如统一小写、规范空格等）。

        index : int
            当前解析位置(0 <= index < len(tokens))。
            FSM 应当从该位置开始尝试匹配自己的目标结构。

        Returns
        -------
        Optional[MatchResult]
            - MatchResult: 匹配成功
              * entity: AviationEntity(识别出的语义实体)
              * step: int(本次匹配消费了多少个 token;Parser 会据此前进)
              * confidence: float(置信度，用于 Parser 做冲突消解)
            - None: 匹配失败（表示“该位置不是我能处理的结构”）
        """
        ...
