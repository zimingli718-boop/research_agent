import re


class Guardrails:

    def verify(self, answer: str, sources: list) -> dict:
        """
        检查答案中的事实声明是否都有 [来源N] 标注
        返回：
          - total_sentences: 句子总数
          - unsupported_sentences: 无引用标注的句子
          - faithfulness_score: 忠实度分数（0-1）
          - citations_used: 使用的来源编号
        """
        if not answer:
            return {
                "total_sentences": 0,
                "unsupported_sentences": [],
                "faithfulness_score": 0.0,
                "citations_used": [],
            }

        # 按中文/英文句号、问号、感叹号分句
        sentences = re.split(r'[。！？.!?]+', answer)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

        unsupported = []
        citations_used = set()

        for sent in sentences:
            # 找句子里的 [来源N] 标注
            citations = re.findall(r'\[来源(\d+)\]', sent)
            if citations:
                citations_used.update(int(c) for c in citations)
            else:
                # 无引用的句子
                # 过滤掉纯描述性的话（如"根据检索内容..."）
                if len(sent) > 15 and not any(
                    kw in sent for kw in ["检索内容", "无法回答", "不足以", "综上所述", "总结"]
                ):
                    unsupported.append(sent)

        total = len(sentences)
        supported = total - len(unsupported)
        faithfulness = supported / total if total > 0 else 0.0

        return {
            "total_sentences": total,
            "unsupported_sentences": unsupported,
            "faithfulness_score": round(faithfulness, 4),
            "citations_used": sorted(citations_used),
            "max_source_index": max(citations_used) if citations_used else 0,
            "available_sources": len(sources),
        }