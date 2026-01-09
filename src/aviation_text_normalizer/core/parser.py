from __future__ import annotations
import logging
from dataclasses import dataclass
from aviation_text_normalizer.core.entity import RenderMode
from aviation_text_normalizer.core.match import MatchResult
from aviation_text_normalizer.core.tokenizer import Tokenizer
from aviation_text_normalizer.fsms.base import FSM


logger = logging.getLogger(__name__)


@dataclass
class Parser:
    """
    Parser 是整个系统的“调度中心”。
    """

    # fsms：所有 FSM 的列表。
    fsms: list[FSM]

    # tokenizer：Tokenizer 实例。
    tokenizer: Tokenizer = Tokenizer()

    def parse(self, text: str, mode: RenderMode = RenderMode.SPOKEN) -> str:
        """
        解析入口：把原始文本转成最终输出字符串。
        """

        # 1) normalize：统一空格、去掉干扰符号、统一破折号等
        normalized = self.tokenizer.normalize(text)

        # 2) tokenize：把文本分成 token 列表（后续 FSM 都基于 token 工作）
        tokens = self.tokenizer.tokenize(normalized)

        # out：最终输出 token/实体渲染结果的列表
        out: list[str] = []

        # i：当前扫描位置（token index）
        i = 0
        while i < len(tokens):
            # 3) 对当前位置尝试所有 FSM，选出“最佳匹配”
            best = self._best_match(tokens, i)

            # 若没有任何 FSM 能匹配，说明当前位置是普通词/噪声/未知结构：
            # 直接原样输出 tokens[i]，然后 i 向前移动 1
            if best is None:
                out.append(tokens[i])
                i += 1
                continue

            # 若匹配成功：
            # - best.entity 是识别出的实体
            # - entity.render(mode) 决定输出 CODE 还是 SPOKEN
            out.append(best.entity.render(mode))

            # step 表示匹配消费了多少 token，需要跳过
            # max(1, step) 是鲁棒性兜底：防止 step=0 导致死循环
            i += max(1, best.step)

        # 4) 拼回句子：用空格连接所有输出片段
        # 注意：这种拼接方式简单可靠，但会改变原始标点/大小写等。
        # 若未来需要保留标点或生成更自然的文本，可以换成更复杂的渲染器。
        return " ".join(out)

    def _best_match(self, tokens: list[str], index: int) -> MatchResult | None:
        """
        在 tokens[index] 位置，尝试所有 FSM， 选择一个最好的 MatchResult。

        贪心选择策略：
        - 先比 step: 匹配覆盖 token 越长越优（更具体）
        - step 相同再比 confidence: 置信度越高越优（更可靠）

        """

        # best：当前找到的最佳匹配；初始为 None
        best: MatchResult | None = None

        # 依次让每个 FSM 尝试匹配
        for fsm in self.fsms:
            try:
                # 成功则返回 MatchResult，失败则返回 None
                res = fsm.match(tokens, index)
            except Exception:
                # - 任意一个 FSM 崩溃，都不允许影响整体解析
                # - 记录异常栈，便于定位 FSM 的 bug
                logger.exception(
                    "FSM crashed at index=%d, window=%r",
                    index,
                    tokens[index : index + 8],
                )
                res = None

            # 若该 FSM 无匹配，继续尝试下一个 FSM
            if res is None:
                continue

            # 冲突消解：
            # 1) best 为空：直接取 res
            # 2) best 不为空：比较 (step, confidence) 的字典序
            # - step 更大就赢
            # - step 相同则 confidence 更大就赢
            if best is None or (res.step, res.confidence) > (best.step, best.confidence):
                best = res

        # 返回最佳匹配（或 None）
        return best
