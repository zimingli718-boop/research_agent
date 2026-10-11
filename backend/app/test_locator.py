import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pdf_locator import PDFLocator

locator = PDFLocator("E:/research_agent/data/1706.03762v7.pdf")

# 测试 1：定位标题
print("=== 定位标题 ===")
for title in ["1 Introduction", "3.2 Attention", "5.3 Optimizer", "7 Conclusion", "References"]:
    loc = locator.locate_first(title)
    if loc:
        print(f"  {title} → 第 {loc['page']} 页")
    else:
        print(f"  {title} → 未找到")

# 测试 2：定位引用
print("\n=== 定位引用 ===")
citations = locator.locate_citations(max_ref_num=15)
for num, locs in list(citations.items())[:5]:
    pages = [str(l["page"]) for l in locs]
    print(f"  [{num}] → 出现在第 {', '.join(pages)} 页")

# 测试 3：References 章节
print("\n=== References 章节 ===")
ref_loc = locator.locate_ref_section()
print(f"  References 在第 {ref_loc['page']} 页")