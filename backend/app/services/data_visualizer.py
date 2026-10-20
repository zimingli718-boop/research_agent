import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import base64
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# 支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

class DataVisualizer:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            timeout=300,
        )
        self.model = "deepseek-chat"

    def process_csv(self, csv_bytes: bytes) -> dict:
        try:
            df = pd.read_csv(io.BytesIO(csv_bytes))
        except Exception as e:
            return {"error": f"CSV 解析失败: {str(e)}"}

        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        categorical_cols = df.select_dtypes(include='object').columns.tolist()

        if not numeric_cols:
            return {"error": "CSV 中没有数值列，无法绘图"}

        fig, ax = plt.subplots(figsize=(8, 5), dpi=150)

        # 自动选择图表类型
        if categorical_cols and numeric_cols:
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]
            df.groupby(x_col)[y_col].mean().plot(kind='bar', ax=ax, color='#3b82f6')
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
        elif len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            ax.plot(df[x_col], df[y_col], marker='o', color='#10b981')
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
        else:
            df[numeric_cols[0]].plot(kind='line', ax=ax, color='#3b82f6')

        ax.set_title('Data Visualization', fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # 解决X轴标签竖着的问题
        plt.xticks(rotation=0)
        plt.tight_layout()

        # 转 Base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)

        # 自动提炼 Caption
        csv_preview = df.head(5).to_string()
        prompt = f"""你是一位学术论文作者。请根据以下数据表格，写一段学术规范的 Figure Caption（图注），并提炼核心结论。

数据预览：
{csv_preview}

要求：
1. 用英文撰写 Figure Caption（如 "Figure 1: Comparison of..."）。
2. 用中文提炼 1-2 句核心趋势结论。
3. 输出 Markdown 格式。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        return {
            "image_base64": img_base64,
            "caption": response.choices[0].message.content,
            "columns": df.columns.tolist(),
            "rows": len(df),
        }