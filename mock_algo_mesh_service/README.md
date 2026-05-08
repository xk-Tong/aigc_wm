# Mock Mesh Algo Service

模拟网格模型水印算法服务，用于本地开发联调。

## 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/algo/v1/mesh/health` | 健康检查 |
| POST | `/algo/v1/mesh/generate` | 生成含水印网格模型（返回 OBJ 二进制） |
| POST | `/algo/v1/mesh/watermark/extract` | 提取网格模型中的水印 |

## 启动

```bash
cd mock_algo_mesh_service
uvicorn main:app --port 9003
```

## 生成接口

- 请求：`POST /algo/v1/mesh/generate`，JSON body 含 `prompt`、`model`、`watermark_bits`（32位二进制）、`seed`
- 响应：二进制 OBJ 文件流，headers: `X-File-Format: obj`、`X-Elapsed-Ms`

## 提取接口

- 请求：`POST /algo/v1/mesh/watermark/extract`，multipart form，字段名 `mesh_file`
- 响应：`{"extracted_watermark": "10101010101010101010101010101010", "elapsed_ms": 0, "echo": {...}}`
