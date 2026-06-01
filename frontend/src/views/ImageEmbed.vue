<template>
  <div class="max-w-[1400px] mx-auto pb-8 pt-2">
    <div class="flex items-center gap-3 mb-6 px-2">
      <div class="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
        <el-icon class="text-xl"><Picture /></el-icon>
      </div>
      <h2 class="text-2xl font-bold text-gray-800 tracking-tight">生成含水印图像</h2>
    </div>

    <!-- 左右两栏布局 (左 4/12 约 33%，右 8/12 约 67%) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

      <!-- ================= 左侧栏：参数配置区域 ================= -->
      <div class="lg:col-span-4 space-y-6">
        <!-- 配置卡片 -->
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <h3 class="text-lg font-bold text-gray-800 mb-5">生成参数配置</h3>
          
          <el-form
            ref="generateFormRef"
            :model="formData"
            :rules="formRules"
            status-icon
            label-position="top"
            class="space-y-4"
          >
            <!-- 1. Prompt 输入框 -->
            <el-form-item label="提示词 (Prompt)" prop="prompt">
              <el-input
                v-model="formData.prompt"
                type="textarea"
                :rows="4"
                maxlength="2000"
                show-word-limit
                placeholder="请输入画面描述，支持中英文..."
                class="custom-textarea"
              />
            </el-form-item>

            <!-- 2. 模型选择 -->
            <el-form-item label="生成模型">
              <el-select v-model="formData.model" size="large" class="w-full">
                <el-option label="FLUX.2 " value="flux2" />
                <el-option label="Stable Diffusion 3.5" value="sd3.5" />
              </el-select>
            </el-form-item>

            <!-- 3. 水印信息输入 -->
            <el-form-item label="水印信息 (8位十六进制)" prop="watermark">
              <div class="flex gap-2 w-full">
                <el-input
                  v-model="formData.watermark"
                  placeholder="请输入8位十六进制水印，如 A1B2C3D4"
                  size="large"
                  maxlength="8"
                  class="flex-1 font-mono"
                />
                <el-button size="large" @click="generateRandomWatermark" class="shrink-0">
                  <el-icon class="mr-1"><Refresh /></el-icon> 随机生成
                </el-button>
              </div>
            </el-form-item>

            <!-- 4. 图像尺寸与引导尺度 -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <el-form-item label="宽度 width (像素)" prop="width" class="!mb-0">
                <el-input-number
                  v-model="formData.width"
                  :min="512"
                  :max="2048"
                  :step="64"
                  :precision="0"
                  controls-position="right"
                  size="large"
                  class="w-full param-input-number"
                />
              </el-form-item>

              <el-form-item label="高度 height (像素)" prop="height" class="!mb-0">
                <el-input-number
                  v-model="formData.height"
                  :min="512"
                  :max="2048"
                  :step="64"
                  :precision="0"
                  controls-position="right"
                  size="large"
                  class="w-full param-input-number"
                />
              </el-form-item>
            </div>

            <el-form-item label="引导尺度 guidance_scale (0-10)" prop="guidance_scale">
              <el-input-number
                v-model="formData.guidance_scale"
                :min="0"
                :max="20"
                :step="0.1"
                :precision="1"
                controls-position="right"
                size="large"
                class="w-full param-input-number"
              />
              <div class="text-xs text-gray-400 mt-1">建议范围 0.0 - 10.0，默认值 1.0</div>
            </el-form-item>

            <!-- 5. 生成按钮 -->
            <div class="pt-4">
              <el-button 
                type="primary" 
                size="large" 
                class="w-full !h-14 !text-lg !rounded-xl shadow-lg shadow-blue-500/30"
                :loading="isGenerating"
                @click="handleGenerate"
              >
                <el-icon class="mr-2" v-if="!isGenerating"><MagicStick /></el-icon>
                {{ isGenerating ? '正在生成并嵌入水印...' : '开始生成图像' }}
              </el-button>
            </div>
          </el-form>
        </div>

        <!-- 可选：最近生成历史 -->
        <!-- <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <h3 class="text-md font-bold text-gray-800 mb-4">最近生成历史</h3>
          <div class="space-y-3">
            <div v-for="i in 3" :key="i" class="flex items-center gap-3 p-2 hover:bg-gray-50 rounded-xl cursor-pointer transition-colors">
              <div class="w-12 h-12 rounded-lg bg-gray-200 overflow-hidden shrink-0">
                <img :src="`https://picsum.photos/seed/history${i}/100/100`" class="w-full h-full object-cover" />
              </div>
              <div class="flex-1 overflow-hidden">
                <p class="text-sm font-medium text-gray-800 truncate">A beautiful landscape with mountains...</p>
                <p class="text-xs text-gray-400 mt-0.5">2026-04-10 14:2{{ i }}:00</p>
              </div>
            </div>
          </div>
        </div> -->
      </div>

      <!-- ================= 右侧栏：结果预览区域 ================= -->
      <div class="lg:col-span-8 space-y-4">

        <!-- 图像预览卡片 -->
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col h-[680px]">
          <div class="flex justify-between items-center mb-4 shrink-0">
            <h3 class="text-lg font-bold text-gray-800">预览区域</h3>
            <!-- 工具栏 -->
            <el-button-group v-if="result">
              <el-button size="small" @click="zoomIn"><el-icon><ZoomIn /></el-icon></el-button>
              <el-button size="small" @click="zoomOut"><el-icon><ZoomOut /></el-icon></el-button>
              <el-button size="small" @click="resetZoom"><el-icon><RefreshLeft /></el-icon></el-button>
            </el-button-group>
          </div>

          <!-- 预览框 -->
          <div class="flex-1 bg-[#f8fafc] rounded-2xl border border-gray-100 overflow-hidden relative flex items-center justify-center">
            <!-- 空白状态 -->
            <div v-if="!result && !isGenerating" class="text-center text-gray-400">
              <el-icon class="text-5xl mb-2 opacity-50"><PictureFilled /></el-icon>
              <p>等待生成</p>
            </div>

            <!-- 加载状态 -->
            <div v-else-if="isGenerating" class="text-center text-blue-500">
              <el-icon class="text-5xl mb-2 is-loading"><Loading /></el-icon>
              <p class="text-sm font-medium animate-pulse">AI 正在努力作画中...</p>
            </div>

            <!-- 有图状态：对比展示 -->
            <template v-else>
              <!-- 模式切换按钮 -->
              <div class="absolute top-3 left-3 z-20 flex gap-0.5 bg-white/80 backdrop-blur rounded-lg p-0.5 shadow-sm border border-gray-200">
                <button
                  class="px-3 py-1.5 text-xs font-medium rounded-md transition-colors"
                  :class="compareMode === 'side' ? 'bg-blue-500 text-white shadow' : 'text-gray-600 hover:text-gray-800'"
                  @click="compareMode = 'side'"
                >并排</button>
                <button
                  class="px-3 py-1.5 text-xs font-medium rounded-md transition-colors"
                  :class="compareMode === 'slider' ? 'bg-blue-500 text-white shadow' : 'text-gray-600 hover:text-gray-800'"
                  @click="compareMode = 'slider'"
                >叠加</button>
              </div>

              <!-- 并排模式 -->
              <div v-if="compareMode === 'side'" class="w-full h-full flex gap-4 p-6" :style="{ transform: `scale(${zoomLevel})`, transformOrigin: 'center center' }">
                <div class="flex-1 flex flex-col items-center min-w-0">
                  <span class="text-xs text-gray-500 mb-2 shrink-0 font-medium">原图 (无水印)</span>
                  <div class="flex-1 w-full flex items-center justify-center min-h-0">
                    <img :src="result.originalUrl" alt="原始图像" class="max-w-full max-h-full object-contain rounded-lg shadow-sm" />
                  </div>
                </div>
                <div class="flex-1 flex flex-col items-center min-w-0">
                  <span class="text-xs text-gray-500 mb-2 shrink-0 font-medium">水印图</span>
                  <div class="flex-1 w-full flex items-center justify-center min-h-0">
                    <img :src="result.watermarkedUrl" alt="水印图像" class="max-w-full max-h-full object-contain rounded-lg shadow-sm" />
                  </div>
                </div>
              </div>

              <!-- 叠加拖动对比模式 -->
              <div v-else class="w-full h-full flex items-center justify-center p-6">
                <div class="relative w-full h-full select-none" :style="{ transform: `scale(${zoomLevel})`, transformOrigin: 'center center' }">
                  <!-- 底层：水印图（全图可见） -->
                  <img :src="result.watermarkedUrl" alt="水印图像" class="absolute inset-0 w-full h-full object-contain rounded-lg" />
                  <!-- 顶层：原图（裁剪显示左侧部分） -->
                  <img :src="result.originalUrl" alt="原始图像" class="absolute inset-0 w-full h-full object-contain rounded-lg"
                       :style="{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }" />
                  <!-- 分界线 -->
                  <div class="absolute top-0 bottom-0 w-0.5 bg-white shadow-md pointer-events-none" :style="{ left: `${sliderPos}%` }"></div>
                  <!-- 滑块手柄 -->
                  <div class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-9 h-9 bg-white rounded-full shadow-lg flex items-center justify-center pointer-events-none border border-gray-200"
                       :style="{ left: `${sliderPos}%` }">
                    <svg class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7l-5 5 5 5M16 7l5 5-5 5" /></svg>
                  </div>
                  <!-- 拖动条 -->
                  <input type="range" min="0" max="100" v-model.number="sliderPos" class="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-10" />
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 生成完成后的信息与操作 -->
        <transition name="el-fade-in-linear">
          <div v-if="result" class="space-y-3">

            <!-- 操作按钮组 & 生成耗时（紧凑单行） -->
            <div class="flex items-center justify-between bg-white rounded-2xl px-5 py-3 shadow-sm border border-gray-100">
              <span class="text-sm text-gray-500 font-medium">
                <el-icon class="mr-1 align-middle"><Timer /></el-icon>
                生成耗时: <span class="text-gray-800 font-bold">{{ result.timeTaken }}s</span>
              </span>
              <div class="flex gap-3">
                <el-button plain round size="small" @click="handleGenerate">重新生成</el-button>
                <el-button type="primary" round size="small" class="shadow-md shadow-blue-500/20" @click="handleDownload">
                  <el-icon class="mr-1"><Download /></el-icon> 下载图像
                </el-button>
              </div>
            </div>

            <!-- 水印信息卡片（精简内边距） -->
            <div class="bg-blue-50/50 rounded-2xl px-5 py-4 border border-blue-100 relative overflow-hidden">
              <div class="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-2xl -mr-10 -mt-10"></div>

              <h4 class="text-sm font-bold text-blue-800 mb-3 flex items-center">
                <el-icon class="mr-2 text-lg"><Key /></el-icon> 已嵌入水印信息
              </h4>

              <div class="bg-white rounded-xl px-4 py-3 border border-blue-100/50 flex justify-between items-center shadow-sm mb-3">
                <span class="font-mono text-base text-gray-800 tracking-widest font-bold">
                  {{ formattedWatermark }}
                </span>
                <el-button circle size="small" @click="copyWatermark" title="复制水印">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </div>

              <div class="text-xs text-gray-500 flex items-center">
                <el-icon class="mr-1"><Calendar /></el-icon>
                嵌入时间: {{ result.timestamp }}
              </div>
            </div>

          </div>
        </transition>

      </div>
    </div>

    <!-- 近期记录面板 -->
    <RecentRecords
      :records="recentRecords"
      operation-type="embed"
      theme-color="blue"
      subtitle="最近 5 条图像生成记录"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'
import RecentRecords from '../components/RecentRecords.vue'

// 用户在页面输入的生成参数。
const formData = ref({
  prompt: '',
  model: 'flux2',
  watermark: '',
  width: 1024,
  height: 1024,
  guidance_scale: 1.0,
})

const generateFormRef = ref()

const validateIntegerRange = (label, min, max) => (_rule, value, callback) => {
  if (value === undefined || value === null || value === '') {
    callback(new Error(`请输入${label}`))
    return
  }
  if (!Number.isInteger(value)) {
    callback(new Error(`${label}必须为整数`))
    return
  }
  if (value < min || value > max) {
    callback(new Error(`${label}需在 ${min}-${max} 之间`))
    return
  }
  callback()
}

const validateNumberRange = (label, min, max) => (_rule, value, callback) => {
  if (value === undefined || value === null || value === '') {
    callback(new Error(`请输入${label}`))
    return
  }
  if (Number.isNaN(Number(value))) {
    callback(new Error(`${label}必须为数字`))
    return
  }
  const numericValue = Number(value)
  if (numericValue < min || numericValue > max) {
    callback(new Error(`${label}需在 ${min}-${max} 之间`))
    return
  }
  callback()
}

const formRules = {
  prompt: [
    { required: true, message: '请输入提示词', trigger: 'blur' },
    { min: 1, max: 2000, message: '提示词长度需在 1-2000 字符之间', trigger: 'blur' },
  ],
  watermark: [
    { required: true, message: '请输入 8 位十六进制水印', trigger: 'blur' },
    { pattern: /^[0-9A-Fa-f]{8}$/, message: '请输入有效的 8 位十六进制水印', trigger: 'blur' },
  ],
  width: [
    { validator: validateIntegerRange('宽度', 512, 2048), trigger: ['blur', 'change'] },
  ],
  height: [
    { validator: validateIntegerRange('高度', 512, 2048), trigger: ['blur', 'change'] },
  ],
  guidance_scale: [
    { validator: validateNumberRange('引导尺度', 0, 20), trigger: ['blur', 'change'] },
  ],
}

// 页面运行状态：是否在生成、当前结果、图片缩放倍数、对比模式、叠加滑块位置。
const isGenerating = ref(false)
const result = ref(null)
const zoomLevel = ref(1)
const compareMode = ref('side')  // 'side' | 'slider'
const sliderPos = ref(50)        // 叠加模式下滑块位置百分比

const hexToBinary = (hex) => parseInt(hex, 16).toString(2).padStart(32, '0')
const binaryToHex = (binary) => parseInt(binary, 2).toString(16).toUpperCase().padStart(8, '0')

const generateRandomWatermark = () => {
  const hexChars = '0123456789ABCDEF'
  let hexStr = ''
  for (let i = 0; i < 8; i++) {
    hexStr += hexChars[Math.floor(Math.random() * 16)]
  }
  formData.value.watermark = hexStr
}

const formattedWatermark = computed(() => {
  if (!result.value || !result.value.watermark) return ''
  return result.value.watermark
})

// 复制水印到剪贴板
const copyWatermark = async () => {
  try {
    await navigator.clipboard.writeText(result.value.watermark)
    ElMessage.success('水印已复制到剪贴板')
  } catch (err) {
    ElMessage.error('复制失败')
  }
}

// 缩放控制
const zoomIn = () => { zoomLevel.value = Math.min(zoomLevel.value + 0.2, 3) }
const zoomOut = () => { zoomLevel.value = Math.max(zoomLevel.value - 0.2, 0.5) }
const resetZoom = () => { zoomLevel.value = 1 }

// 近期记录
const recentRecords = ref([])

const fetchRecentRecords = async () => {
  try {
    const res = await request.get('/api/v1/records', {
      params: { media_type: 'image', operation_type: 'embed', size: 5, page: 1 }
    })
    if (res?.data?.code === 200) {
      recentRecords.value = res.data.data.items
    }
  } catch { /* ignore */ }
}

// 下载按钮逻辑：直接打开后端返回的下载地址。
const handleDownload = () => {
  if (!result.value?.downloadUrl) {
    ElMessage.warning('暂无可下载图像')
    return
  }

  window.open(result.value.downloadUrl, '_blank', 'noopener,noreferrer')
}

// 主流程：提交生成请求 -> 接收结果 -> 更新页面展示。
const handleGenerate = async () => {
  try {
    await generateFormRef.value.validate()
  } catch (_err) {
    ElMessage.warning('请先修正参数输入后再生成图像')
    return
  }

  isGenerating.value = true
  result.value = null
  resetZoom()

  try {
    // 把页面字段映射为后端接口字段。
    const response = await request.post('/api/v1/image/generate-watermarked', {
      prompt: formData.value.prompt,
      model: formData.value.model,
      watermark_bits: hexToBinary(formData.value.watermark),
      width: formData.value.width,
      height: formData.value.height,
      guidance_scale: formData.value.guidance_scale,
    })

    const payload = response?.data || {}
    isGenerating.value = false

    // 把后端返回数据转换成页面需要的展示结构。
    const generatedAt = payload.generated_at ? new Date(payload.generated_at) : new Date()
    result.value = {
      originalUrl: payload.original_image_url,
      watermarkedUrl: payload.watermarked_image_url,
      downloadUrl: payload.download_url || payload.watermarked_image_url,
      watermark: payload.watermark_bits ? binaryToHex(payload.watermark_bits) : formData.value.watermark,
      timeTaken: ((payload.elapsed_ms || 0) / 1000).toFixed(1),
      timestamp: generatedAt.toLocaleString('zh-CN', { hour12: false }),
    }
    compareMode.value = 'side'
    sliderPos.value = 50

    ElMessage.success('图像生成并嵌入水印成功！')
    fetchRecentRecords()
  } catch (err) {
    // 统一错误提示：优先展示后端 detail，其次展示通用错误。
    isGenerating.value = false

    const message =
      err?.response?.data?.detail || err?.message || '图像生成失败，请稍后重试'
    ElMessage.error(message)
  }
}

onMounted(() => fetchRecentRecords())
</script>

<style scoped>
/* 隐藏滚动条但保留功能 */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #e2e8f0;
  border-radius: 10px;
}

/* 优化文本域样式 */
:deep(.custom-textarea .el-textarea__inner) {
  background-color: #f8fafc;
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid #e2e8f0;
  padding: 12px;
  transition: all 0.2s ease;
  font-weight: 600; /* 或 bold */
  color: #1f2937; /* 更深的灰黑色 */
}
:deep(.custom-textarea .el-textarea__inner:hover) {
  border-color: #cbd5e1;
}
:deep(.custom-textarea .el-textarea__inner:focus) {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
  background-color: #ffffff;
}

/* 数值输入框：视觉与页面已有输入风格统一，并强化焦点态反馈。 */
:deep(.param-input-number.el-input-number) {
  width: 100%;
}
:deep(.param-input-number .el-input__wrapper) {
  background-color: #f8fafc;
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}
:deep(.param-input-number .el-input__wrapper:hover) {
  border-color: #cbd5e1;
}
:deep(.param-input-number .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
  background-color: #ffffff;
}
:deep(.param-input-number .el-input-number__increase),
:deep(.param-input-number .el-input-number__decrease) {
  background-color: #ffffff;
  color: #64748b;
  border-left: 1px solid #e2e8f0;
}
:deep(.param-input-number .el-input-number__increase:hover),
:deep(.param-input-number .el-input-number__decrease:hover) {
  color: #2563eb;
}
</style>