# Mock 3DGS Algorithm Service

本地开发用的 3DGS（3D Gaussian Splatting）算法服务模拟器。

## 启动方式

```bash
cd mock_algo_gs_service
pip install -r requirements.txt
uvicorn main:app --reload --port 9004
```

## 接口说明

| 接口 | 方法 | 说明 |
|---|---|---|
| `/algo/v1/gs/health` | GET | 健康检查 |
| `/algo/v1/gs/generate` | POST | 生成含水印 3DGS PLY 文件 |
| `/algo/v1/gs/watermark/extract` | POST | 从上传的 PLY 中提取水印 |

### 生成接口

- **请求体**: JSON，包含 `prompt`、`model`、`watermark_bits`（32 位二进制）、`seed`
- **响应**: 二进制 PLY 文件流
- **响应头**:
  - `X-File-Format`: 文件格式（`ply`）
  - `X-Elapsed-Ms`: 算法耗时（毫秒）
  - `X-Gaussian-Count`: Gaussian 数量

### 提取接口

- **请求**: `multipart/form-data`，字段名 `gs_file`
- **响应**: JSON，包含 `extracted_watermark`（32 位二进制）和 `elapsed_ms`

## Mock 数据说明

生成接口返回一个合成的球形 Gaussian 分布（100 个 Gaussian），
每个 Gaussian 包含位置、球谐基色、不透明度、缩放和旋转属性。

提取接口始终返回固定水印：`10101010101010101010101010101010`。
