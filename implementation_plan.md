# AIGC 数字水印系统 — 系统功能完善实施方案

## 背景

当前系统已完成四种媒体类型（图像/点云/网格/3DGS）的水印嵌入和提取核心算法功能，但存在以下关键缺失：

- **无角色区分**：User 模型有 `role` 字段但从未使用，所有用户权限等同
- **无数据持久化**：水印操作结果只返回前端，刷新页面即丢失
- **无操作审计**：没有操作日志，无法追踪用户行为
- **大量 Placeholder 页面**：溯源验真、水印注册库、操作日志、用户管理、系统配置均未实现
- **鉴权逻辑冗余**：每个 router 重复写 `_extract_token` + `verify_session_token`
- **前端硬编码**：Dashboard 假数据、侧边栏用户信息硬编码

---

## 设计决策摘要

| 决策项 | 选定方案 |
|--------|---------|
| 角色体系 | 三级：`USER` → `ADMIN` → `SUPER_ADMIN` |
| 权限划分 | SUPER_ADMIN 管理所有用户+系统；ADMIN 管理 USER + 全部业务功能；USER 只能做水印嵌入/提取 + 查看自己的历史 |
| 历史记录表 | 一张通用表 `wm_task_record`，通过 `media_type` + `operation_type` 区分 |
| 操作日志表 | 独立的 `sys_operation_log` 表，通过中间件/装饰器自动记录 |
| 水印注册库 | 不单独建表，复用 `wm_task_record` 中 `operation_type=embed` 的记录视图 |
| 前端历史展示 | 各嵌入/提取页底部加折叠面板 + 独立"我的历史"页面 |
| 鉴权重构 | 抽取为 `get_current_user` + `require_role` 两个 FastAPI Depends |
| 数据库迁移 | 用 SQLAlchemy `create_all` 自动建表（开发阶段） |
| 前端菜单权限 | 根据 `role` 字段动态控制菜单可见性 |
| Dashboard | 简化为纯导航快捷入口页（去掉假数据统计） |
| 个人中心 | 侧边栏底部弹窗/页面，支持修改密码、查看个人信息 |
| 溯源验真 | 暂不实现，后续迭代 |
| 系统配置 | 暂不实现，保持 Placeholder |

---

## 实施计划：分 3 期迭代

---

### 第 1 期：基础设施层

> 搭建 RBAC 权限体系、新建数据库表、统一鉴权机制。后续所有业务功能都依赖这一层。

---

#### 1.1 统一鉴权依赖

##### [NEW] [deps.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/deps.py)

新增全局认证依赖模块，包含两个核心函数：

```python
# get_current_user(authorization: str = Header()) -> dict
# - 从 Authorization 头提取 token
# - 调用 Redis 验证 session
# - 返回 session_data（含 id, username, role, status）
# - 失败抛 401

# require_role(*allowed_roles: str) -> Callable
# - 返回一个 Depends 工厂函数
# - 检查 current_user["role"] 是否在 allowed_roles 中
# - 角色层级：SUPER_ADMIN > ADMIN > USER
# - 不匹配抛 403
```

**使用方式**：

```python
# 任何已登录用户可访问
@router.post("/generate-watermarked")
async def generate(body: ..., user: dict = Depends(get_current_user)):
    ...

# 仅 ADMIN 及以上可访问
@router.get("/users")
async def list_users(user: dict = Depends(require_role("ADMIN"))):
    ...
```

##### [MODIFY] [image.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/routers/image.py)
##### [MODIFY] [pointcloud.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/routers/pointcloud.py)
##### [MODIFY] [mesh.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/routers/mesh.py)
##### [MODIFY] [gs.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/routers/gs.py)

- 删除每个 router 中重复的 `_extract_token` 函数和 `IMAGE_REQUIRE_AUTH` 检查块
- 改为使用 `user: dict = Depends(get_current_user)` 参数
- 删除 `service_conf.py` 中的 `*_REQUIRE_AUTH` 配置项

---

#### 1.2 RBAC 角色体系

##### [MODIFY] [auth.py (model)](file:///e:/workspace/aigc_wm/aigc_wm/backend/models/auth.py)

角色常量定义：

```python
class UserRole:
    USER = "USER"
    ADMIN = "ADMIN"  
    SUPER_ADMIN = "SUPER_ADMIN"

ROLE_HIERARCHY = {
    UserRole.USER: 0,
    UserRole.ADMIN: 1,
    UserRole.SUPER_ADMIN: 2,
}
```

User 模型保持不变（已有 `role` 和 `status` 字段）。

##### [MODIFY] [auth.py (crud)](file:///e:/workspace/aigc_wm/aigc_wm/backend/crud/auth.py)

- `generate_access_token` 中的 session_payload 已包含 `role`，无需修改
- 新增 `update_user_role(db, user_id, new_role)` 函数
- 新增 `update_user_status(db, user_id, status)` 函数
- 新增 `reset_user_password(db, user_id, new_password)` 函数
- 新增 `list_users(db, page, size, keyword, role_filter, status_filter)` 分页查询函数

---

#### 1.3 数据库新表

##### [NEW] [record.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/models/record.py)

```python
class WmTaskRecord(Base):
    """水印任务记录表 — 存储所有嵌入/提取操作的业务数据"""
    __tablename__ = "wm_task_record"

    id           # int, PK, auto-increment
    user_id      # int, FK -> sys_user.id
    username     # str, 冗余存储方便查询
    media_type   # str, enum: "image" | "pointcloud" | "mesh" | "gs"
    operation_type  # str, enum: "embed" | "extract"

    # 嵌入操作专用字段
    watermark_bits  # str, nullable, 嵌入的水印值
    prompt          # str, nullable, 生成提示词
    model           # str, nullable, 使用的模型
    original_file_url   # str, nullable
    watermarked_file_url  # str, nullable
    download_url    # str, nullable

    # 提取操作专用字段
    source_file_name  # str, nullable, 上传文件名
    source_file_size  # int, nullable, 上传文件大小
    extracted_bits    # str, nullable, 提取的水印值

    # 公共字段
    elapsed_ms   # int, nullable, 处理耗时
    status       # str, "success" | "failed"
    error_message  # str, nullable
    file_id      # str, 文件唯一标识(uuid)
    
    # created_at / updated_at 继承自 Base
```

##### [NEW] [operation_log.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/models/operation_log.py)

```python
class SysOperationLog(Base):
    """系统操作日志表 — 审计追踪"""
    __tablename__ = "sys_operation_log"

    id           # int, PK, auto-increment
    user_id      # int, nullable (未登录操作如登录失败)
    username     # str, nullable
    operation    # str, 操作类型: "login" | "logout" | "register" | "embed" | "extract" | "user_manage" | ...
    media_type   # str, nullable, 仅水印操作有值
    request_path # str, 请求路径
    request_method  # str, GET/POST/...
    ip_address   # str
    status       # str, "success" | "fail"
    detail       # text/JSON, 补充信息
    
    # created_at 继承自 Base
```

##### [MODIFY] [main.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/main.py)

应用启动时自动建表：

```python
from config.db_conf import async_engine
from models.auth import Base

@app.on_event("startup")
async def startup():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

> [!IMPORTANT]
> 所有新模型（WmTaskRecord, SysOperationLog）需要从 `models/auth.py` 中的 `Base` 继承，确保 `create_all` 能发现它们。需要在 main.py 的 import 中引入这些模型。

---

### 第 2 期：业务功能层

> 在基础设施上实现历史记录持久化、操作日志、前端历史页面等核心业务功能。

---

#### 2.1 历史记录持久化

##### [MODIFY] [image.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/routers/image.py)
##### [MODIFY] [pointcloud.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/routers/pointcloud.py)
##### [MODIFY] [mesh.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/routers/mesh.py)
##### [MODIFY] [gs.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/routers/gs.py)

在每个 `generate-watermarked` 和 `extract-watermark` 端点中，操作成功后：

```python
# 在返回结果前，异步写入 wm_task_record
record = WmTaskRecord(
    user_id=user["id"],
    username=user["username"],
    media_type="image",  # 各 router 填自己的类型
    operation_type="embed",  # 或 "extract"
    watermark_bits=body.watermark_bits,
    # ... 其他字段
    status="success",
)
db.add(record)
await db.commit()
```

##### [NEW] [record.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/crud/record.py)

CRUD 函数：
- `create_task_record(db, record_data)` — 创建记录
- `get_user_records(db, user_id, media_type, operation_type, page, size)` — 分页查询用户历史
- `get_all_records(db, media_type, operation_type, page, size, keyword)` — 管理员查询全部记录
- `get_record_stats(db, user_id=None)` — 统计各类型记录数量

##### [NEW] [record.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/routers/record.py)

历史记录 API：

```
GET /api/v1/records?media_type=image&operation_type=embed&page=1&size=20
# USER: 只返回自己的记录
# ADMIN/SUPER_ADMIN: 可查看所有记录（可选 user_id 筛选）

GET /api/v1/records/{record_id}
# 获取单条记录详情
```

##### [NEW] [record.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/schemas/record.py)

Pydantic 模型：
- `TaskRecordResponse` — 单条记录响应
- `TaskRecordListResponse` — 分页列表响应
- `TaskRecordQuery` — 查询参数

---

#### 2.2 操作日志中间件

##### [NEW] [audit_log.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/services/audit_log.py)

实现两种方式：

**方式1 — 装饰器/工具函数**（推荐，可精确控制记录内容）：

```python
async def log_operation(
    db: AsyncSession,
    user: dict | None,
    operation: str,
    media_type: str | None,
    request: Request,
    status: str,
    detail: dict | None = None,
):
    log = SysOperationLog(
        user_id=user["id"] if user else None,
        username=user["username"] if user else None,
        operation=operation,
        media_type=media_type,
        request_path=str(request.url.path),
        request_method=request.method,
        ip_address=request.client.host,
        status=status,
        detail=json.dumps(detail, ensure_ascii=False) if detail else None,
    )
    db.add(log)
    await db.commit()
```

在各关键端点中调用：

```python
# 登录成功后
await log_operation(db, user_data, "login", None, request, "success")

# 嵌入成功后
await log_operation(db, user, "embed", "image", request, "success", {"watermark": bits})
```

##### [NEW] [log.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/routers/log.py)

操作日志查询 API：

```
GET /api/v1/logs?operation=embed&page=1&size=20
# USER: 只看自己的日志
# ADMIN: 看 USER 角色的日志
# SUPER_ADMIN: 看所有人的日志
```

##### [NEW] [log.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/schemas/log.py)
##### [NEW] [log.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/crud/log.py)

---

#### 2.3 前端历史页面

##### [NEW] [History.vue](file:///e:/workspace/aigc_wm/aigc_wm/frontend/src/views/History.vue)

独立的"我的历史"页面（侧边栏"数据管理"下）：

- 顶部 Tab 切换媒体类型（全部/图像/点云/网格/3DGS）
- 筛选条件：操作类型（嵌入/提取）、时间范围
- 分页表格展示记录列表
- 每行可展开查看详情、下载文件
- ADMIN+ 角色可看到用户名列并搜索其他用户

##### [MODIFY] 各嵌入/提取页面（ImageEmbed.vue 等）

- 页面底部新增可折叠的"近期记录"面板
- 显示当前媒体类型最近 5 条记录
- 操作成功后自动刷新列表
- 点击"查看全部"跳转到 History.vue

##### [NEW] [WatermarkRegistry.vue](file:///e:/workspace/aigc_wm/aigc_wm/frontend/src/views/WatermarkRegistry.vue)

水印注册库页面（替换 Placeholder）：

- 本质是 `wm_task_record` 中 `operation_type=embed` 的筛选视图
- 支持按水印值搜索、按媒体类型筛选、时间范围
- 展示：水印值、媒体类型、生成用户、生成时间、文件预览/下载
- ADMIN+ 可查看所有用户的记录

##### [NEW] [OperationLog.vue](file:///e:/workspace/aigc_wm/aigc_wm/frontend/src/views/OperationLog.vue)

操作日志页面（替换 Placeholder）：

- 分页表格展示操作日志
- 筛选：操作类型、时间范围、用户（ADMIN+）
- 列：时间、用户、操作类型、媒体类型、IP、状态
- 只读，不可编辑

---

### 第 3 期：管理功能层

> 实现用户管理、个人中心、前端权限控制等管理功能。

---

#### 3.1 用户管理

##### [NEW] [user.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/routers/user.py)

用户管理 API（仅 ADMIN+ 可访问）：

```
GET    /api/v1/users?page=1&size=20&keyword=xxx&role=USER&status=1
       # ADMIN 只返回 USER 角色用户
       # SUPER_ADMIN 返回所有用户

PUT    /api/v1/users/{user_id}/status
       # 启用/禁用用户 {"status": 0}

PUT    /api/v1/users/{user_id}/role  
       # 修改角色 {"role": "ADMIN"}
       # ADMIN 只能将 USER 升为 ADMIN
       # SUPER_ADMIN 可任意修改

POST   /api/v1/users/{user_id}/reset-password
       # 重置密码 {"new_password": "xxx"}
       # ADMIN 只能重置 USER 的密码
       # SUPER_ADMIN 可重置任何人
```

##### [NEW] [UserManagement.vue](file:///e:/workspace/aigc_wm/aigc_wm/frontend/src/views/UserManagement.vue)

用户管理页面（替换 Placeholder）：

- 分页表格：用户名、邮箱、角色、状态、注册时间、操作
- 搜索框：按用户名/邮箱搜索
- 筛选：角色、状态
- 操作按钮：启用/禁用（Switch）、修改角色（下拉）、重置密码（弹窗输入新密码）
- 根据当前登录用户角色控制可见用户范围

---

#### 3.2 个人中心

##### [NEW] [profile.py](file:///e:/workspace/aigc_wm/aigc_wm/backend/routers/profile.py)

个人中心 API：

```
GET    /api/v1/profile
       # 返回当前用户完整信息

PUT    /api/v1/profile/password
       # 修改密码 {"old_password": "xxx", "new_password": "xxx"}
```

##### [NEW] [UserProfile.vue](file:///e:/workspace/aigc_wm/aigc_wm/frontend/src/views/UserProfile.vue)

个人中心页面：

- 展示：用户名、邮箱、角色、注册时间
- 修改密码表单：旧密码 + 新密码 + 确认密码
- 从侧边栏底部用户卡片点击进入

---

#### 3.3 前端权限控制

##### [MODIFY] [MainLayout.vue](file:///e:/workspace/aigc_wm/aigc_wm/frontend/src/layouts/MainLayout.vue)

- 侧边栏底部用户信息改为从 `localStorage` 读取动态显示（用户名、角色中文名）
- 菜单项根据 `role` 动态显示/隐藏：

```javascript
const role = JSON.parse(localStorage.getItem('user'))?.role || 'USER'

const menuConfig = {
  // 所有角色可见
  dashboard: true,
  'image-wm': true,
  'pointcloud-wm': true,
  'mesh-wm': true,
  'gs-wm': true,
  
  // 数据管理：所有角色可见（内容按角色筛选）
  'data/history': true,
  'data/registry': ['ADMIN', 'SUPER_ADMIN'],
  'data/logs': ['ADMIN', 'SUPER_ADMIN'],
  
  // 系统管理：仅管理员可见
  'system/users': ['ADMIN', 'SUPER_ADMIN'],
  'system/config': ['SUPER_ADMIN'],
}
```

##### [MODIFY] [index.js (router)](file:///e:/workspace/aigc_wm/aigc_wm/frontend/src/router/index.js)

- 路由 meta 中添加 `roles` 字段
- 路由守卫中增加角色校验：

```javascript
{
  path: 'system/users',
  meta: { title: '用户管理', roles: ['ADMIN', 'SUPER_ADMIN'] }
}

// 守卫中
if (to.meta.roles && !to.meta.roles.includes(user.role)) {
  return '/dashboard'  // 无权限重定向
}
```

##### [MODIFY] [Dashboard.vue](file:///e:/workspace/aigc_wm/aigc_wm/frontend/src/views/Dashboard.vue)

- 去掉所有硬编码统计数据
- 保留快捷导航卡片入口
- 根据角色动态显示相关卡片

---

## 新增文件总览

### 后端

| 文件 | 说明 |
|------|------|
| `backend/deps.py` | 统一认证/授权依赖 |
| `backend/models/record.py` | WmTaskRecord 模型 |
| `backend/models/operation_log.py` | SysOperationLog 模型 |
| `backend/crud/record.py` | 任务记录 CRUD |
| `backend/crud/log.py` | 操作日志 CRUD |
| `backend/schemas/record.py` | 任务记录 Pydantic 模型 |
| `backend/schemas/log.py` | 操作日志 Pydantic 模型 |
| `backend/routers/record.py` | 历史记录 API |
| `backend/routers/log.py` | 操作日志 API |
| `backend/routers/user.py` | 用户管理 API |
| `backend/routers/profile.py` | 个人中心 API |
| `backend/services/audit_log.py` | 审计日志工具函数 |

### 前端

| 文件 | 说明 |
|------|------|
| `frontend/src/views/History.vue` | 历史记录页面 |
| `frontend/src/views/WatermarkRegistry.vue` | 水印注册库页面 |
| `frontend/src/views/OperationLog.vue` | 操作日志页面 |
| `frontend/src/views/UserManagement.vue` | 用户管理页面 |
| `frontend/src/views/UserProfile.vue` | 个人中心页面 |

---

## 数据库变更

新增 2 张表（通过 `create_all` 自动创建）：

```sql
-- wm_task_record（水印任务记录）
-- sys_operation_log（系统操作日志）
```

`sys_user` 表不变，已有 `role` 和 `status` 字段。

---

## 暂不实施

| 功能 | 原因 |
|------|------|
| 溯源验真 | 依赖水印注册库积累数据后再实现 |
| 系统配置动态化 | 当前环境变量方式够用 |
| 数据库迁移（Alembic） | 开发阶段用 create_all 足够 |
| Docker/CI/CD | 非本次范围 |

---

## 验证计划

### 自动化测试

```bash
# 后端单元测试
python -m unittest discover -s backend/tests -v

# 新增测试文件
# backend/tests/test_rbac.py — 测试角色权限
# backend/tests/test_record.py — 测试历史记录 CRUD
# backend/tests/test_audit_log.py — 测试操作日志
```

### 手动验证

- 注册 USER 账号 → 验证只能看到基本菜单
- 数据库手动设置 ADMIN/SUPER_ADMIN 角色 → 验证菜单和 API 权限
- 执行嵌入/提取操作 → 刷新页面验证记录仍在
- 检查操作日志表是否有相应记录
- 测试用户管理：启用/禁用、角色修改、密码重置
