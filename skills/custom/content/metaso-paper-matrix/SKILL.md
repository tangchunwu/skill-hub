---
name: metaso-paper-matrix
description: 使用 metaso MCP 进行学术检索与文献矩阵生成，强制 scope="paper"、多轮检索、逐篇精读、输出 GB/T 7714-2015 与标准 CSV。适用于“文献矩阵”“核心文献补充”“按主题找高质量论文并生成CSV”等场景。
---

# Metaso Paper Matrix

## 目标

围绕指定主题，生成 12-18 篇高相关学术文献矩阵，满足：

1. 全流程基于 `metaso_web_search` + `metaso_web_reader`
2. 严格优先学术来源（`scope="paper"`）
3. 引文按 GB/T 7714-2015 输出
4. 最终输出一个干净的 CSV 代码块

## 触发词

- "文献矩阵"
- "核心文献补充"
- "按主题检索论文"
- "GB/T 7714-2015"
- "用 metaso 搜论文"

## 强制流程

### 1) 制定检索策略

- 给出中英关键词（同义词与近义词扩展）
- 限定时间范围：`2019-2026`
- 指定来源优先级：高 IF 期刊 / 顶级会议

### 2) 多轮检索（必须）

每轮都必须调用：

```text
metaso_web_search(
  query="...",
  scope="paper",
  size=15~20,
  includeSummary=true
)
```

要求：
- 至少 3 轮检索（不同关键词组合）
- 不能首轮即停止
- 记录候选论文 URL 与摘要摘要要点

### 3) 候选筛选

筛选标准：
- 与主题直接相关
- 方法/实证/综述价值明确
- 来源可信（期刊/会议可识别）
- 优先包含 DOI

### 4) 逐篇精读（必须）

对入围论文逐篇调用：

```text
metaso_web_reader(url="<论文链接>", format="markdown")
```

提取字段：
- Title
- Authors
- Year
- Journal/Conference
- DOI
- Abstract
- Keywords
- Research_Type
- Core_Contribution
- Relevance

### 5) GB/T 7714-2015 生成

根据文献类型生成：
- 期刊：`[J]`
- 会议：`[C]//`
- 在线资源：`[EB/OL]`

基本要求：
- 作者、题名、文献类型、来源、年份、卷(期)、页码（可得则填）
- DOI 或可核验链接

### 6) 最终输出格式（必须）

仅输出一个 CSV 代码块：

```csv
序号,Title,Authors,Year,Journal/Conference,GBT_Citation,DOI,Abstract,Keywords,Research_Type,Core_Contribution,Relevance
```

## 质量校验

输出前必须检查：

1. 条目数在 12-18 之间
2. 不重复（标题与 DOI 去重）
3. 引文字段完整且符合 GB/T 7714-2015 基本结构
4. DOI 可用则不留空；无 DOI 时标注 `N/A`
5. CSV 列顺序严格一致

## 禁止事项

- 禁止混入新闻、博客、营销站、论坛贴
- 禁止只做单轮检索
- 禁止省略 `scope="paper"`
- 禁止不读原文页面就生成“看似完整”的字段
- 禁止输出除最终 CSV 以外的冗余内容（除非用户明确要求）

## 默认执行风格

- 先给检索策略 + 第一轮调用，再继续迭代检索
- 最终只给一个完整 CSV
- 若用户要求写入本地文件，再额外保存为 `.csv`
