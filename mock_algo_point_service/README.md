# Mock Point Cloud Algorithm Service

模拟点云算法服务，用于本地联调测试。

## 启动方式

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 9002 --reload
```

## 接口说明

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/algo/v1/pointcloud/health` | 健康检查 |
| POST | `/algo/v1/pointcloud/generate` | 生成含水印点云（返回二进制 PLY 流） |
| POST | `/algo/v1/pointcloud/watermark/extract` | 提取点云水印（上传文件，返回 JSON） |

### 生成接口

请求体（JSON）：
```json
{
  "prompt": "一只飞翔的鸟",
  "model": "trellis",
  "watermark_bits": "A1B2C3",
  "seed": 42,
  "point_count": 50000
}
```

响应：二进制 PLY 文件流，元数据通过响应头传递：
- `X-Point-Count`: 实际点数
- `X-File-Format`: 文件格式（ply）
- `X-Elapsed-Ms`: 算法耗时（毫秒）

### 提取接口

请求：`multipart/form-data`，字段名 `pointcloud_file`

响应（JSON）：
```json
{
  "extracted_watermark": "A1B2C3",
  "elapsed_ms": 123,
  "echo": {
    "filename": "test.ply",
    "content_type": "application/octet-stream",
    "size_bytes": 1234567
  }
}
```
