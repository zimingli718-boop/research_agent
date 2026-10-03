import os
from dotenv import load_dotenv

load_dotenv()

# 尝试导入 MinerU SDK
try:
    from mineru import MinerU
    print("MinerU SDK 导入成功")
except ImportError as e:
    print(f"导入失败: {e}")
    print("尝试其他导入方式...")
    try:
        from mineru.client import MinerU
        print("使用 mineru.client.MinerU")
    except ImportError:
        print("需要根据实际 SDK 调整导入语句")
        exit(1)

# 用 flash 模式（免 Token）
client = MinerU()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
pdf_path = os.path.join(BASE_DIR, "data", "1706.03762v7.pdf")

print(f"开始解析: {pdf_path}")
print("=" * 50)

result = client.flash_extract(pdf_path)

print("解析成功！")
print("=" * 50)
print(f"Markdown 前 500 字：\n{result.markdown[:500]}")