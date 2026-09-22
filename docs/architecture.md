# 自习室管理系统架构说明

## 系统架构

```mermaid
flowchart TB
    Student[学生端 HTML/CSS/JS] --> API[FastAPI]
    Admin[管理端 HTML/CSS/JS] --> API
    API --> Auth[JWT + RBAC]
    API --> Routers[学生 / 管理 / 认证路由]
    Routers --> Services[预约锁、通知、初始化服务]
    Routers --> CRUD[业务规则与数据访问]
    Services --> Redis[(Redis 分布式锁)]
    CRUD --> PostgreSQL[(PostgreSQL)]
    Alembic[Alembic] --> PostgreSQL
    Scheduler[APScheduler] --> CRUD
    Scheduler --> Email[邮件通知]
    Middleware[响应包装与操作审计] --> API
```

## 并发预约时序

```mermaid
sequenceDiagram
    participant U as 学生端
    participant A as FastAPI
    participant R as Redis
    participant D as PostgreSQL

    U->>A: POST /api/student/bookings
    A->>A: 校验身份、时间与营业规则
    A->>R: 获取 seat + time 分布式锁
    alt 成功获取锁
        A->>D: 在事务中写入预约
        D->>D: 排他约束检查时间区间
        alt 无冲突
            D-->>A: 提交成功
            A-->>U: 返回预约结果
        else 时间重叠
            D-->>A: 约束冲突
            A-->>U: 返回座位已被预约
        end
        A->>R: 释放锁
    else 锁被占用
        A-->>U: 返回稍后重试
    end
```

## 预约状态机

```mermaid
stateDiagram-v2
    [*] --> booked: 创建预约
    booked --> checked_in: 有效签到
    booked --> cancelled: 学生或管理员取消
    booked --> expired: 超过签到宽限期
    checked_in --> completed: 到达预约结束时间
    checked_in --> cancelled: 管理员异常处理
    cancelled --> [*]
    expired --> [*]
    completed --> [*]
```

## 可靠性边界

- Redis 锁用于降低同一座位同一时段的并发竞争，PostgreSQL 排他约束作为最终一致性防线。
- JWT Access/Refresh Token 与 RBAC 隔离学生、员工、管理员和超级管理员权限。
- 定时任务负责预约过期、自动完成、提醒与邮件发送；重复执行必须保持幂等。
- 管理员操作日志对密码、Token、Secret 和 API Key 等字段脱敏。
- 生产环境禁止默认 JWT 密钥和自动创建演示账号。
