name: sync-minecontext
description: 将 MineContext 数据库增量同步到 Obsidian。当用户说"同步 minecontext"、"sync minecontext"或"/sync-minecontext"时使用此 skill。
---

# MineContext 数据同步

将 MineContext 应用的数据库内容增量同步到 Obsidian。

## 同步内容
- 每日报告 (DailyReport) → MineContext每日报告/
- 活动日志 (activity) → MineContext活动日志/
- 提醒建议 (tips) → MineContext提醒建议/
- 待办事项 (todo) → MineContext待办事项/

## 执行步骤

使用 Bash 工具执行以下 Python 脚本：

```bash
python3 << 'EOF'
import sqlite3
import os
from datetime import datetime

db_path = "/Users/tangchunwu/Library/Application Support/MineContext/persist/sqlite/app.db"
obsidian_base = "/Users/tangchunwu/Documents/Obsidian Vault"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. 同步每日报告
report_dir = os.path.join(obsidian_base, "MineContext每日报告")
os.makedirs(report_dir, exist_ok=True)
cursor.execute("SELECT id, content, DATE(created_at) FROM vaults WHERE document_type = 'DailyReport' ORDER BY created_at")
report_count = 0
for id, content, date in cursor.fetchall():
    filepath = os.path.join(report_dir, f"{date}_{id}.md")
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        report_count += 1
print(f"每日报告: 新增 {report_count} 个")

# 2. 同步活动日志
activity_dir = os.path.join(obsidian_base, "MineContext活动日志")
os.makedirs(activity_dir, exist_ok=True)
cursor.execute("SELECT DISTINCT DATE(start_time) FROM activity ORDER BY DATE(start_time)")
activity_count = 0
for (date,) in cursor.fetchall():
    filepath = os.path.join(activity_dir, f"{date}.md")
    cursor.execute("SELECT TIME(start_time), TIME(end_time), title, content FROM activity WHERE DATE(start_time) = ? ORDER BY start_time", (date,))
    activities = cursor.fetchall()
    existing_count = 0
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            existing_count = f.read().count('## ')
    if len(activities) > existing_count:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {date} 活动日志\n\n")
            for start, end, title, content in activities:
                f.write(f"## {start} - {end}\n### {title}\n\n{content}\n\n---\n\n")
        activity_count += 1
print(f"活动日志: 更新 {activity_count} 天")

# 3. 同步提醒建议
tips_dir = os.path.join(obsidian_base, "MineContext提醒建议")
os.makedirs(tips_dir, exist_ok=True)
cursor.execute("SELECT DISTINCT DATE(created_at) FROM tips ORDER BY DATE(created_at)")
tips_count = 0
for (date,) in cursor.fetchall():
    filepath = os.path.join(tips_dir, f"{date}.md")
    cursor.execute("SELECT TIME(created_at), content FROM tips WHERE DATE(created_at) = ? ORDER BY created_at", (date,))
    tips = cursor.fetchall()
    existing_count = 0
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            existing_count = f.read().count('## ')
    if len(tips) > existing_count:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {date} 提醒与建议\n\n")
            for time, content in tips:
                f.write(f"## {time}\n\n{content}\n\n---\n\n")
        tips_count += 1
print(f"提醒建议: 更新 {tips_count} 天")

# 4. 同步待办事项
todo_dir = os.path.join(obsidian_base, "MineContext待办事项")
os.makedirs(todo_dir, exist_ok=True)
cursor.execute("SELECT DISTINCT DATE(created_at) FROM todo ORDER BY DATE(created_at)")
todo_count = 0
for (date,) in cursor.fetchall():
    filepath = os.path.join(todo_dir, f"{date}.md")
    cursor.execute("SELECT TIME(created_at), content, status, urgency, reason FROM todo WHERE DATE(created_at) = ? ORDER BY created_at", (date,))
    todos = cursor.fetchall()
    existing_count = 0
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            existing_count = f.read().count('## ')
    if len(todos) > existing_count:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {date} 待办事项\n\n")
            for time, content, status, urgency, reason in todos:
                status_text = "已完成" if status == 1 else "待办"
                urgency_text = ["低", "中", "高"][min(urgency or 0, 2)]
                f.write(f"## {time} - {status_text}\n**优先级**: {urgency_text}\n\n{content}\n\n")
                if reason:
                    f.write(f"> {reason}\n\n")
                f.write("---\n\n")
        todo_count += 1
print(f"待办事项: 更新 {todo_count} 天")

conn.close()
print(f"\n同步完成! {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
EOF
```

执行完成后向用户报告同步结果。
