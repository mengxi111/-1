# 自习室管理系统（毕业设计展示版）

## 项目简介
本项目是一个面向学生与门店运营人员的自习室管理系统，后端采用 FastAPI，前端为项目内置中文静态页面。系统支持登录鉴权、预约、签到、过期释放、黑名单、通知、公告、统计与管理后台运营功能，适合课程设计/毕业设计演示。

## 技术栈
- 后端：`FastAPI`、`SQLAlchemy 2.0`、`Alembic`
- 数据库：`PostgreSQL`
- 缓存与锁：`Redis`（支持 Redis 异常时数据库兜底）
- 定时任务：`APScheduler`
- 鉴权：`JWT Access + Refresh`、`RBAC（student/staff/admin/super_admin）`
- 前端：项目内置 `HTML/CSS/JS`（全中文 UI）

## 核心功能

### 认证与权限
- 注册、登录、刷新令牌、退出登录
- 未登录仅可访问 `/auth/login`、`/auth/register`
- 学生端与管理端隔离：
  - 学生端：`/student`，仅 `student` 可访问
  - 管理端：`/admin`，仅 `staff/admin/super_admin` 可访问
- 接口隔离：
  - 学生接口：`/api/student/*`
  - 管理接口：`/api/admin/*`
  - 认证接口：`/api/auth/*`

### 学生端
- 门店/座位查询
- 某座位“今天/明天”可用时段查询
- 创建预约、取消预约、改期
- 我的预约、签到（含二维码模拟签到）
- 通知中心（站内通知 + 可选邮件推送）
- 学生公告列表

### 管理端
- 门店、区域、座位、价格方案管理
- 座位批量生成（如 `A01-A50`）
- 预约管理（查询、手动取消、强制签到、标记完成）
- 订单管理（查询、取消、退款、CSV 导出）
- 会员管理
- 公告管理（发布/下线）
- 黑名单管理（手动拉黑/解除）
- 统计概览（今日指标、7天趋势、热门座位）与签到率趋势图
- 操作日志查询
- 系统配置（预约时长、取消/改期时间、签到宽限、拉黑阈值）

### 自动任务
- 已预约超时未签到自动过期
- 已签到到达结束时间自动完成
- 预约开始前提醒通知
- 通知邮件批量发送

## 预约规则（关键）
- 同一座位同一时段不可重复预约
- 同一用户同一时段只能预约一个座位
- 座位状态非“可用”不可预约
- 不在门店营业时间内不可预约
- 取消规则：开始前 `CANCEL_BEFORE_MINUTES`（默认 30）分钟
- 改期规则：开始前 `RESCHEDULE_BEFORE_MINUTES`（默认 60）分钟

## 目录结构
```text
app/
  api/                 # /api/auth /api/student /api/admin
  core/                # 配置、鉴权、统一响应
  crud/                # 业务读写与规则
  db/                  # SQLAlchemy 会话
  middleware/          # API 包装、管理操作日志
  models/              # ORM 模型
  schemas/             # Pydantic 模型
  services/            # 锁、邮件、初始化数据
  tasks/               # APScheduler 定时任务
  static/              # 前端页面（中文）
  ui/                  # 前端路由
alembic/versions/      # 数据库迁移脚本
scripts/               # 一键启动、种子数据
```

## 环境要求
- Python 3.11+（推荐）
- PostgreSQL 14+
- Redis 6+
- Windows PowerShell 或 Linux shell

## 一键启动（PowerShell）
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\run_full.ps1
```

可选参数：
```powershell
.\scripts\run_full.ps1 -SkipInstall        # 跳过依赖安装
.\scripts\run_full.ps1 -SkipSeed           # 跳过种子数据
.\scripts\run_full.ps1 -NoDocker           # 不自动拉起 Docker
.\scripts\run_full.ps1 -Port 8001          # 指定端口
```

## 手动启动
```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt

Copy-Item .env.local.example .env

docker compose -f docker-compose.local.yml up -d postgres redis
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python scripts\seed_demo_data.py

.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

## 访问地址
- 登录页：`http://127.0.0.1:8001/auth/login`
- 学生端：`http://127.0.0.1:8001/student`
- 管理端：`http://127.0.0.1:8001/admin`
- Swagger：`http://127.0.0.1:8001/docs`
- 健康检查：`http://127.0.0.1:8001/healthz`

## 初始化种子数据
系统启动时若核心数据为空会自动创建：
- 门店：主校区自习室
- 区域：A区、B区
- 座位：A01-A10、B01-B10
- 价格方案：按小时 5 元
- 演示账号：`admin/123456`、`student/123456`
- 演示预约记录、公告、通知

也可由管理员调用：
- `POST /api/admin/bootstrap`
- `POST /api/admin/bootstrap-demo`

## 默认演示账号（seed_demo_data）
- 管理员：`admin / 123456`
- 学生：`student / 123456`
- 超级管理员：`super_admin / 123456`

## 关键环境变量（.env）
- `DATABASE_URL`：PostgreSQL 连接串
- `REDIS_URL`：Redis 连接串
- `REDIS_LOCK_REQUIRED`：`false` 时 Redis 不可用自动走数据库兜底
- `CHECKIN_GRACE_MINUTES`：签到宽限（默认 30）
- `MIN_BOOKING_MINUTES`：最短预约时长（默认 30）
- `MAX_BOOKING_HOURS`：最长预约时长（默认 12）
- `NO_SHOW_BLACKLIST_THRESHOLD`：爽约拉黑阈值（默认 3）
- `REMINDER_MINUTES_BEFORE_START`：开场提醒分钟数（默认 30）

## 常见问题
1. `ERR_CONNECTION_REFUSED`
- 后端未启动，先执行 `run_full.ps1` 或 `uvicorn`。

2. “预约锁服务不可用，请稍后重试”
- 检查 Redis；若 `REDIS_LOCK_REQUIRED=false`，系统会自动用数据库约束兜底。

3. `/admin` 打开后被跳回登录页
- 账号角色不是 `staff/admin/super_admin`，请使用管理账号登录。

## 毕设亮点（可写入论文）
- 预约状态机完整闭环：已预约→已签到→已完成，含取消/过期分支
- 双重并发保护：Redis 锁 + 数据库排他约束
- 自动化运营规则：超时过期、自动完成、黑名单自动拉黑
- 可配置规则中心：预约时长、取消/改期窗口、签到宽限、爽约阈值
- 统一 API 结构与中文错误语义，便于前后端联调
- 管理后台覆盖真实运营场景：资源管理、统计、日志、导出
