import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.rag_agent import RAGAgent
from models.database import SessionLocal, Paper

# 获取库中所有论文
db = SessionLocal()
papers = db.query(Paper).all()
print(f"\n库中共有 {len(papers)} 篇论文：")
for p in papers:
    print(f"  - {p.id[:8]}... | {p.title[:60]}")
db.close()

if len(papers) < 2:
    print("\n⚠️ 库中论文不足 2 篇，无法测试多文对比。")
    exit(1)

# 取前两篇做对比
paper_ids = [papers[0].id, papers[1].id]

agent = RAGAgent()

# 多文对比 query
query = "Compare the model architectures described in these papers."
print(f"\n{'='*60}")
print(f"多文对比: {query}")
print(f"限定论文: {[pid[:8] for pid in paper_ids]}")
print('='*60)

result = agent.answer(query, top_k=5, paper_ids=paper_ids)

print(f"\n【回答】\n{result['answer']}")
print(f"\n【引用来源】")
for s in result["sources"]:
    print(f"  [来源{s['index']}] paper_id={s['paper_id'][:8]}... "
          f"chunk={s['chunk_index']} "
          f"section={s.get('section_path') or 'N/A'}")