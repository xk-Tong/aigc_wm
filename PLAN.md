# AIGC 数字水印系统初期开发设计与 API 接口方案

## 摘要
- 初期目标收敛为 `图像生成/上传 -> 水印嵌入 -> 水印提取/验真 -> 结果查看` 的完整 MVP，不做点云/网格实际实现。
- 技术路线采用 `前端 + 业务后端 + 独立算法后端` 三层结构；业务后端与算法后端通过 `HTTP` 通信，不直接跨机器调用 Python 函数。
- 数据与存储先采用 `MySQL + 服务器本地磁盘`，不引入 MongoDB、Redis、MinIO；复杂报告和算法参数先落 MySQL `JSON` 字段。
- 对前端提供异步任务式 API；对算法组提供按能力拆分的 HTTP 接口；后续可平滑升级到 Redis 队列、MinIO、分布式部署。

## 架构与职责
- 前端负责登录、文件上传、参数填写、任务提交、轮询状态、结果展示与下载。
- 业务后端负责用户认证、文件落盘、任务创建、任务状态流转、调用算法服务、结果持久化、统一错误处理。
- 算法后端只负责模型推理能力，不负责用户、权限、业务审计、数据库主数据。
- 业务后端内部实现 `AlgorithmClient` 适配层，对代码使用者表现为 `generate()`、`embed()`、`extract()`、`verify()` 四个方法；其底层统一走 HTTP，所以既满足你“像调用函数一样用”，也适配多人协作和跨环境部署。
- 初期异步方案不使用 Redis；采用 `MySQL 任务表 + 单实例后台执行器`。业务后端创建任务后立即返回 `task_id`，后台执行器调用算法服务并回写状态。默认单实例部署；服务重启时将 `RUNNING` 任务标记为 `FAILED` 或 `RETRYABLE`。
- 跨机器文件传递不依赖共享磁盘。业务后端调用算法服务时：
  - `generate` 发送 JSON 参数；
  - `embed/extract/verify` 发送 `multipart/form-data` 文件和参数；
  - 算法服务返回 JSON，图像结果使用 `result_image_base64`，检测/验真返回结构化 JSON。
- 初期不做并发优化、消息队列、GPU 调度、对象存储、复杂监控，只预留接口和状态字段。

## 数据设计与关键类型
- `users`：`id`、`username`、`password_hash`、`status`、`created_at`。
- `files`：`id`、`owner_id`、`file_role`、`origin_name`、`storage_path`、`mime_type`、`sha256`、`width`、`height`、`extra_meta(JSON)`、`created_at`。
- `tasks`：`id`、`owner_id`、`task_type`、`status`、`source_file_id`、`result_file_id`、`request_payload(JSON)`、`error_message`、`created_at`、`started_at`、`finished_at`。
- `task_results`：`id`、`task_id`、`result_payload(JSON)`、`report_summary(JSON)`、`created_at`。
- `operation_logs`：记录登录、上传、任务提交、任务失败、结果下载等审计事件。
- 枚举固定为：
  - `task_type`: `GENERATE` / `EMBED` / `EXTRACT` / `VERIFY`
  - `task_status`: `PENDING` / `RUNNING` / `SUCCESS` / `FAILED`
  - `file_role`: `UPLOADED` / `GENERATED` / `WATERMARKED` / `REPORT`
- 本地存储目录固定为：`storage/uploads`、`storage/generated`、`storage/watermarked`、`storage/reports`。
- 公开接口统一响应格式：`{ code, message, data, request_id }`。
- 认证采用 `JWT access token`；初期不做 refresh token，不做复杂 RBAC，只区分“已登录用户”和“未登录用户”。

## API 接口设计
**业务后端对前端 API**
| 方法 | 路径 | 说明 | 关键字段 |
|---|---|---|---|
| POST | `/api/v1/auth/register` | 用户注册 | `username`, `password` |
| POST | `/api/v1/auth/login` | 用户登录 | `username`, `password` |
| GET | `/api/v1/auth/me` | 获取当前用户 | Header `Authorization` |
| POST | `/api/v1/files/upload` | 上传源图 | `file` |
| GET | `/api/v1/files/{file_id}` | 查询文件元数据 | `file_id` |
| GET | `/api/v1/files/{file_id}/download` | 下载文件 | `file_id` |
| POST | `/api/v1/tasks/generate` | 创建生成任务 | `prompt`, `negative_prompt?`, `model_name`, `width`, `height`, `seed?` |
| POST | `/api/v1/tasks/embed` | 创建嵌入任务 | `file_id`, `watermark_text`, `algorithm_params(JSON)` |
| POST | `/api/v1/tasks/extract` | 创建提取任务 | `file_id`, `algorithm_params(JSON)` |
| POST | `/api/v1/tasks/verify` | 创建验真任务 | `file_id`, `expected_watermark?`, `algorithm_params(JSON)` |
| GET | `/api/v1/tasks/{task_id}` | 查询任务状态与结果摘要 | `task_id` |
| GET | `/api/v1/tasks` | 任务列表 | `task_type?`, `status?`, `page`, `page_size` |

**算法后端对业务后端 API**
| 方法 | 路径 | 说明 | 输入 | 输出 |
|---|---|---|---|---|
| GET | `/algo/v1/health` | 健康检查 | 无 | 服务状态、模型就绪信息 |
| POST | `/algo/v1/generate` | 图像生成 | JSON 参数 | `result_image_base64`, `image_meta` |
| POST | `/algo/v1/watermark/embed` | 水印嵌入 | 文件 + 参数 | `result_image_base64`, `metrics` |
| POST | `/algo/v1/watermark/extract` | 水印提取 | 文件 + 参数 | `extracted_watermark`, `confidence`, `metrics` |
| POST | `/algo/v1/watermark/verify` | 水印验真 | 文件 + 参数 | `verified`, `confidence`, `match_detail`, `metrics` |

## 关键流程
- 上传嵌入：前端上传图片到业务后端，业务后端保存本地文件与 `files` 记录；前端提交嵌入任务；后台执行器读取文件并调用算法服务；成功后保存含水印图片，写入 `result_file_id` 和指标。
- AIGC 生成：前端提交生成任务；业务后端创建任务并调用算法服务生成；返回图像后落盘为 `GENERATED` 文件，可继续用于嵌入。
- 提取/验真：前端选择目标文件发起任务；算法服务返回提取文本或验真结论；业务后端将结果写入 `task_results.result_payload`，供任务详情页展示。
- 错误策略：算法服务超时、参数校验失败、模型内部异常都映射为业务后端统一错误码；任务状态置 `FAILED`，保留 `error_message` 便于排查。

## 测试与验收
- 单元测试覆盖：JWT 登录、文件上传校验、任务状态机、`AlgorithmClient` 请求封装、错误码映射。
- 集成测试覆盖：业务后端对“模拟算法服务”的 `generate/embed/extract/verify` 全链路调用。
- 端到端场景覆盖：
  - 注册/登录成功；
  - 上传图片并嵌入水印成功；
  - 生成图片成功并可继续嵌入；
  - 对含水印图片执行提取成功；
  - 对含水印图片执行验真成功；
  - 算法服务超时时任务正确失败；
  - 非本人文件不可访问。
- MVP 验收标准：
  - 前端可完成登录、上传、提交任务、轮询、查看结果；
  - 业务后端在无 Redis/MinIO/MongoDB 情况下稳定完成闭环；
  - 算法后端与业务后端可部署在不同机器、不同虚拟环境下正常通信；
  - API 文档可直接给前端与算法组并行开发。

## 假设与默认决策
- 初期只实际支持 `PNG/JPG/JPEG` 图像输入，输出统一保存为 `PNG`。
- 图片与结果文件规模默认可接受 `base64` 传输；若后续变大，再切换为 MinIO/对象 URL 方案。
- 当前不实现管理员后台、复杂角色权限、分布式任务调度、断点续跑、限流、缓存。
- 若后续接入 Redis，则仅替换任务调度层，不改变前端 API 和 `tasks` 表核心字段。
- 若后续接入 MinIO，则 `files.storage_path` 改存对象键即可，不改变业务接口。
- 若后续扩展点云/网格，仅新增 `content_type` 与对应算法接口，不重构现有图像 MVP 主流程。
