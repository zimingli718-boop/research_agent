import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.rag_agent import RAGAgent

agent = RAGAgent()

# 测试 1：细粒度问答
query1 = "What are the β1 and β2 hyperparameters in the Adam optimizer?"
print(f"\n{'='*60}")
print(f"测试 1: {query1}")
print('='*60)
result = agent.answer(query1, top_k=5)
print(f"\n【回答】\n{result['answer']}")
print(f"\n【引用来源】")
for s in result["sources"]:
    print(f"  [来源{s['index']}] paper_id={s['paper_id'][:8]}... "
          f"chunk={s['chunk_index']} "
          f"section={s.get('section_path') or 'N/A'}")

# 测试 2：作者与机构
query2 = "Which institutions are the authors of this paper affiliated with?"
print(f"\n{'='*60}")
print(f"测试 2: {query2}")
print('='*60)
result = agent.answer(query2, top_k=5)
print(f"\n【回答】\n{result['answer']}")
print(f"\n【引用来源】")
for s in result["sources"]:
    print(f"  [来源{s['index']}] paper_id={s['paper_id'][:8]}... "
          f"chunk={s['chunk_index']} "
          f"section={s.get('section_path') or 'N/A'}")

# 测试 3：训练细节
query3 = "What GPU model and how many GPUs were used for training?"
print(f"\n{'='*60}")
print(f"测试 3: {query3}")
print('='*60)
result = agent.answer(query3, top_k=5)
print(f"\n【回答】\n{result['answer']}")
print(f"\n【引用来源】")
for s in result["sources"]:
    print(f"  [来源{s['index']}] paper_id={s['paper_id'][:8]}... "
          f"chunk={s['chunk_index']} "
          f"section={s.get('section_path') or 'N/A'}")