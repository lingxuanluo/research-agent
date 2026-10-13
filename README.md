# ResearchLens：科研论文解读 Agent

## 本地启动

```bash
cd research_agent_app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Windows PowerShell：激活环境使用 `.venv\Scripts\Activate.ps1`，复制环境文件使用 `copy .env.example .env`。

浏览器打开终端显示的 `http://localhost:8501`。

## 功能
- OpenAlex API 跨学科真实论文检索、日期筛选、来源跳转
- SQLite 本地保存文献
- 上传 PDF 并提取文字（不支持扫描 PDF OCR）
- 大众科普 / 科研入门 / 专业科研三种解读
- 结合材料追问、导出 Markdown

## 密钥
在侧边栏填 OpenAlex API Key（推荐，申请 https://openalex.org/settings/api ）和 OpenAI API Key（AI 解读必需）。也可以写进 `.env`。无 OpenAI Key 时提供原文摘录及阅读提示。

## 边界
目前是可运行 MVP：单篇论文摘要或 PDF 的证据约束解读，不是多篇文献向量 RAG。未自动下载全文，也不自动更新知识库。论文结论和模型回答应人工核验。
