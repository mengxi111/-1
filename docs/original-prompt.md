你是资深后端架构师，请帮我设计一个“自习室管理系统”的 MVP。
要求：
1. 角色：学员、管理员
2. 功能：座位管理、预约下单、签到、订单管理、会员卡(可选)、简单统计
3. 输出内容：
   - 业务流程（学员端+管理员端）
   - 数据库表设计（PostgreSQL），含字段、索引、关键约束（尤其是防止同一座位同一时段重复预约）
   - 状态机：booking 和 order 的状态流转图（用文字描述即可）
   - API 列表（RESTful），按模块分组
请以清晰的 markdown 输出。
请用 FastAPI + SQLAlchemy2.0 + PostgreSQL 生成一个可运行的后端项目骨架（MVP）。
要求：
1) 目录结构清晰：app/main.py, app/core/config.py, app/db/session.py, app/models, app/schemas, app/api/router.py
2) 实现以下模块的基础 CRUD：
   - store, seat, user
3) 实现预约 booking 的创建接口（POST /bookings）
   - 输入：seat_id, start_time, end_time, user_id
   - 规则：同一 seat 在时间段重叠时禁止创建（必须防并发）
   - 返回：booking_id, status
4) 提供 Alembic 迁移脚本
5) 给出 requirements.txt 和启动方式
请直接输出完整代码（按文件分块），确保能本地运行。
在现有 booking 创建逻辑上，加入“防并发抢座”机制：
1) 使用 Redis 分布式锁（key: seat:{seat_id}:{date}:{start}-{end}）
2) 数据库层再加唯一/排他约束（你选择合适方式：排他约束或用重叠检测 + 事务隔离）
3) 接口在高并发下必须保证不会出现重复预约
请给出：
- 代码修改（具体到文件）
- Redis 依赖与配置
- 压测建议（如何验证不会重复）
请为系统增加签到与自动过期：
1) 签到接口 POST /bookings/{id}/checkin
   - 生成二维码/验证码（先用 6 位数字验证码即可）
   - 验证成功则 booking.status = checked_in
2) 定时任务：
   - 对 start_time 已过且未签到的 booking 自动标记为 expired，并释放座位占用
实现方式：APScheduler 或 Celery 任选其一，但要给出可运行代码。
请增加管理后台统计接口：
1) GET /stats/overview?store_id=&date=
返回：
- 今日订单数、今日收入、今日上座率（按可用座位数）
- 按小时的上座趋势（数组）
2) 统计口径要写清楚（订单状态、退款是否算收入等）
给出接口代码、SQL 查询、返回示例 JSON。
给系统加一个“运营 AI 助手”接口：
POST /ai/query
输入：自然语言问题（中文），例如：
- “今天上座率多少？”
- “本周收入最高的是哪一天？”
要求：
1) 先实现一个 rule-based 解析器（不用真接大模型也能跑）
2) 预留可插拔 LLM：如果配置了 OPENAI_API_KEY（或其他），则用 LLM 把问题转成结构化查询参数
3) 输出：answer + used_sql + confidence
请给出完整实现与示例。