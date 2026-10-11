import pymupdf

pdf_path = "E:/research_agent/data/1706.03762v7.pdf"
doc = pymupdf.open(pdf_path)

print(f"总页数: {doc.page_count}")

# 测试 1：搜索标题 "3.2 Attention"
print("\n=== 搜索标题：3.2 Attention ===")
for page_num in range(doc.page_count):
    page = doc[page_num]
    results = page.search_for("3.2 Attention")
    if results:
        print(f"  第 {page_num + 1} 页，找到 {len(results)} 处")
        for r in results:
            print(f"    位置: x={r.x0:.1f}, y={r.y0:.1f}")
        break

# 测试 2：搜索引用 [12]
print("\n=== 搜索引用：[12] ===")
count = 0
for page_num in range(doc.page_count):
    page = doc[page_num]
    results = page.search_for("[12]")
    if results:
        print(f"  第 {page_num + 1} 页，找到 {len(results)} 处")
        count += len(results)
        if count >= 10:
            break
print(f"\n总共找到 [12] 至少 {count} 处")

# 测试 3：搜索 References
print("\n=== 搜索 References 章节 ===")
for page_num in range(doc.page_count):
    page = doc[page_num]
    results = page.search_for("References")
    if results:
        print(f"  References 出现在第 {page_num + 1} 页")
        break