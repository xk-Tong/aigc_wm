# Mock Algo Service

用于本地联调“业务后端 -> 算法服务 -> 前端展示”链路。

## 功能

- 接收 `POST /algo/v1/generate` 的图像生成参数。
- 接收 `POST /algo/v1/watermark/extract` 的图像文件，返回 32 位二进制水印。
- 读取项目根目录下的 `test.png`。
- 返回符合业务后端预期的 JSON：
  - `result_image_base64`
  - `image_format`
  - `width`
  - `height`
  - `elapsed_ms`
  - `echo`

## 启动方式

在仓库根目录执行：

```bash
pip install -r mock_algo_service/requirements.txt
uvicorn mock_algo_service.main:app --host 0.0.0.0 --port 9001 --reload
```

如果你启动提取接口时报 multipart 相关错误，说明运行环境里还没装 `python-multipart`，请先安装依赖。

业务后端默认会请求：`http://127.0.0.1:9001/algo/v1/generate`。
如果你的 mock 服务地址不同，请在业务后端设置环境变量：

- `ALGO_IMAGE_BASE_URL`
- `ALGO_IMAGE_TIMEOUT_SECONDS`
- `BIZ_IMAGE_STORAGE_ROOT`
