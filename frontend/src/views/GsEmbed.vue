<template>
  <div class="max-w-[1400px] mx-auto pb-8 pt-2">
    <div class="flex items-center gap-3 mb-6 px-2">
      <div class="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center text-violet-600">
        <el-icon class="text-xl"><Histogram /></el-icon>
      </div>
      <h2 class="text-2xl font-bold text-gray-800 tracking-tight">3DGS 水印嵌入</h2>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

      <!-- ================= 左侧栏：参数配置区域 ================= -->
      <div class="lg:col-span-5 space-y-6">
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <h3 class="text-lg font-bold text-gray-800 mb-5">生成参数配置</h3>

          <el-form ref="generateFormRef" label-position="top" :model="formData" :rules="formRules">

            <!-- 3DGS 描述 -->
            <el-form-item label="场景描述 (Prompt)" prop="prompt">
              <el-input
                v-model="formData.prompt"
                type="textarea"
                :rows="4"
                maxlength="2000"
                show-word-limit
                placeholder="请输入 3DGS 场景描述，如：一只可爱的小猫咪..."
              />
            </el-form-item>

            <!-- 生成模型 -->
            <el-form-item label="生成模型">
              <el-select v-model="formData.model" size="large" class="w-full">
                <el-option label="Trellis" value="trellis" />
              </el-select>
            </el-form-item>

            <!-- 水印信息：32 位二进制 -->
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

            <!-- 随机种子 -->
            <el-form-item label="随机种子 (可选)">
              <el-input-number
                v-model="formData.seed"
                :min="0"
                :step="1"
                placeholder="留空则随机"
                size="large"
                class="w-full"
              />
            </el-form-item>

            <!-- 生成按钮 -->
            <div class="pt-4">
              <el-button
                type="primary"
                size="large"
                class="w-full h-14! text-lg! rounded-xl! shadow-lg shadow-violet-500/30 bg-violet-600! hover:bg-violet-700! border-none!"
                :loading="isGenerating"
                @click="handleGenerate"
              >
                <el-icon class="mr-2" v-if="!isGenerating"><MagicStick /></el-icon>
                {{ isGenerating ? '正在生成 3DGS 模型...' : '生成 3DGS 模型' }}
              </el-button>
            </div>
          </el-form>
        </div>
      </div>

      <!-- ================= 右侧栏：结果预览区域 ================= -->
      <div class="lg:col-span-7 space-y-6">

        <!-- 3D 预览区域 -->
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col h-[500px]">
          <div class="flex justify-between items-center mb-4 shrink-0">
            <h3 class="text-lg font-bold text-gray-800">3DGS 渲染预览</h3>
            <el-button-group v-if="result">
              <el-button size="small" title="重置视角" @click="resetView"><el-icon><RefreshLeft /></el-icon></el-button>
              <el-button size="small" title="全屏预览" @click="toggleFullscreen"><el-icon><FullScreen /></el-icon></el-button>
            </el-button-group>
          </div>

          <!-- 预览容器：overlay 和 gsplat canvas 分离，避免 innerHTML 破坏 Vue DOM -->
          <div class="flex-1 rounded-2xl overflow-hidden relative border border-gray-100 bg-[#1a1a2e]">
            <!-- Vue 管理的 overlay 层 -->
            <div v-if="!result && !isGenerating" class="absolute inset-0 flex flex-col items-center justify-center text-gray-400 bg-[#f8fafc] z-10">
              <el-icon class="text-5xl mb-2 opacity-50"><Histogram /></el-icon>
              <p>等待生成</p>
            </div>
            <div v-else-if="isGenerating" class="absolute inset-0 flex flex-col items-center justify-center bg-[#f8fafc]/90 backdrop-blur-sm z-10">
              <el-icon class="text-4xl text-violet-500 mb-3 animate-spin"><Loading /></el-icon>
              <p class="text-sm font-medium text-violet-600">正在构建 3DGS 场景并嵌入水印...</p>
            </div>
            <!-- gsplat.js 独占的渲染容器，与 Vue 管理的 DOM 完全隔离 -->
            <div ref="gsContainer" class="absolute inset-0"></div>
          </div>
        </div>

        <!-- 生成结果信息 -->
        <transition name="el-fade-in-linear">
          <div v-if="result" class="space-y-6">

            <!-- 模型信息行 & 操作按钮 -->
            <div class="flex flex-wrap items-center justify-between bg-white rounded-2xl p-4 shadow-sm border border-gray-100 gap-4">
              <div class="flex items-center gap-4 text-sm text-gray-600 font-medium ml-2">
                <span><el-icon class="mr-1 align-middle"><DataAnalysis /></el-icon> Gaussian 数量: <span class="text-gray-800 font-bold">{{ (result.gaussianCount || 0).toLocaleString() }}</span></span>
                <el-divider direction="vertical" />
                <span><el-icon class="mr-1 align-middle"><Timer /></el-icon> 耗时: <span class="text-gray-800 font-bold">{{ result.timeTaken }}s</span></span>
              </div>

              <div class="flex gap-3">
                <el-button plain round @click="handleGenerate">重新生成</el-button>
                <el-button type="primary" round class="shadow-md shadow-violet-500/20 bg-violet-600! border-none!" @click="handleDownload">
                  <el-icon class="mr-1"><Download /></el-icon> 下载模型
                </el-button>
              </div>
            </div>

            <!-- 水印信息卡片 -->
            <div class="bg-violet-50/50 rounded-3xl p-6 border border-violet-100 relative overflow-hidden">
              <div class="absolute top-0 right-0 w-32 h-32 bg-violet-500/5 rounded-full blur-2xl -mr-10 -mt-10"></div>

              <h4 class="text-sm font-bold text-violet-800 mb-4 flex items-center">
                <el-icon class="mr-2 text-lg"><Key /></el-icon> 已嵌入水印信息
              </h4>

              <div class="bg-white rounded-xl p-4 border border-violet-100/50 flex justify-between items-center shadow-sm mb-4">
                <span class="font-mono text-lg text-gray-800 tracking-widest font-bold">
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
      theme-color="violet"
      subtitle="最近 5 条 3DGS 生成记录"
    />
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, onMounted, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'
import RecentRecords from '../components/RecentRecords.vue'

// 动态加载 gsplat 库，避免顶层 import 阻塞路由切换
let _gsModule = null
const ensureGsplatLoaded = async () => {
  if (!_gsModule) {
    _gsModule = await import('@mkkellogg/gaussian-splats-3d')
  }
  return _gsModule
}

// ==================== 表单数据 ====================

const generateFormRef = ref(null)

const formData = ref({
  prompt: '',
  model: 'trellis',
  watermark: '',
  seed: null,
})

const formRules = {
  prompt: [
    { required: true, message: '请输入 3DGS 场景描述', trigger: 'blur' },
    { min: 1, max: 2000, message: '描述长度需在 1-2000 字符之间', trigger: 'blur' },
  ],
  watermark: [
    { required: true, message: '请输入 8 位十六进制水印', trigger: 'blur' },
    { pattern: /^[0-9A-Fa-f]{8}$/, message: '请输入有效的 8 位十六进制水印', trigger: 'blur' },
  ],
}

const isGenerating = ref(false)
const result = ref(null)

// ==================== Gaussian Splats 3D ====================

// gsContainer 是 gsplat.js 的独占渲染容器，与 Vue 管理的 overlay DOM 隔离
const gsContainer = ref(null)
const viewer = shallowRef(null)

const initViewer = async () => {
  if (!gsContainer.value) return

  // 先同步停止旧 viewer，避免与新 viewer 冲突
  // 每次重新初始化前先停掉旧 viewer，避免 GPU 资源和渲染循环叠加。
  await cleanupViewer()

  const GS3D = await ensureGsplatLoaded()

  viewer.value = new GS3D.Viewer({
    rootElement: gsContainer.value,
    cameraUp: [0, -1, 0],
    initialCameraPosition: [0, 0, 2],
    initialCameraLookAt: [0, 0, 0],
    dynamicScene: false,
    selfDrivenMode: true,
  })
}

const loadGsFromUrl = async (url) => {
  if (!viewer.value) await initViewer()
  if (!viewer.value) return

  // 后端返回的是可访问 URL，这里直接交给 gsplat.js 拉取并渲染。
  const GS3D = await ensureGsplatLoaded()

  try {
    await viewer.value.addSplatScene(url, {
      splatAlphaRemovalThreshold: 5,
      showLoadingUI: false,
      // 显式指定 PLY 格式，防止 URL 不以 .ply 结尾时格式检测失败
      format: GS3D.SceneFormat.Ply,
    })
    viewer.value.start()
  } catch (e) {
    console.error('[GsEmbed] addSplatScene failed:', e)
    ElMessage.error('3DGS 模型加载失败')
  }
}

const resetView = async () => {
  if (result.value && result.value.gsUrl) {
    await cleanupViewer()
    await initViewer()
    loadGsFromUrl(result.value.gsUrl)
  }
}

const toggleFullscreen = () => {
  const el = gsContainer.value?.parentElement
  if (!el) return
  if (!document.fullscreenElement) {
    el.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

/**
 * 安全清理 viewer：
 * 1. 先同步 stop() 停止渲染循环
 * 2. 清空容器（gsContainer 不含 Vue 子节点，安全操作）
 * 3. 异步 dispose() 释放 GPU 资源
 */
const cleanupViewer = async () => {
  const v = viewer.value
  viewer.value = null

  if (v) {
    try { v.stop() } catch { /* ignore */ }
    // 清空 gsplat.js 渲染容器（此 div 不含 Vue 管理的子节点）
    if (gsContainer.value) gsContainer.value.innerHTML = ''
    try { await v.dispose() } catch { /* ignore */ }
  }
}

// ==================== 水印与生成 ====================

// 前端输入的是 8 位十六进制水印，提交给后端前先转成 32 位二进制串。
const hexToBinary = (hex) => parseInt(hex, 16).toString(2).padStart(32, '0')
const binaryToHex = (binary) => parseInt(binary, 2).toString(16).toUpperCase().padStart(8, '0')

const generateRandomWatermark = () => {
  const hexChars = '0123456789ABCDEF'
  let hexStr = ''
  for (let i = 0; i < 8; i++) hexStr += hexChars[Math.floor(Math.random() * 16)]
  formData.value.watermark = hexStr
}
    // 请求体字段要和后端 schema 保持一致，尤其是 watermark_bits 这个二进制字段。

const copyWatermark = async () => {
  try {
    await navigator.clipboard.writeText(result.value.watermark)
    ElMessage.success('水印已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

const formattedWatermark = computed(() => {
  if (!result.value || !result.value.watermark) return ''
  return result.value.watermark
})

// 近期记录
const recentRecords = ref([])

const fetchRecentRecords = async () => {
  try {
    const res = await request.get('/api/v1/records', {
      params: { media_type: 'gs', operation_type: 'embed', size: 5, page: 1 }
    })
    if (res?.data?.code === 200) {
      recentRecords.value = res.data.data.items
    }
  } catch { /* ignore */ }
}

const handleDownload = async () => {
  if (!result.value?.downloadUrl) {
    ElMessage.warning('暂无可下载的 3DGS 文件')
    return
  }

  try {
    const response = await fetch(result.value.downloadUrl)
    if (!response.ok) {
      ElMessage.error('下载 3DGS 文件失败')
      return
    }
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = result.value.fileName || 'watermarked_3dgs.ply'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('下载 3DGS 文件失败，请检查网络连接')
  }
}

const handleGenerate = async () => {
  try {
    await generateFormRef.value.validate()
  } catch {
    ElMessage.warning('请先修正参数输入后再生成 3DGS 模型')
    return
  }

  isGenerating.value = true
  result.value = null
  await cleanupViewer()

  try {
    const response = await request.post('/api/v1/gs/generate-watermarked', {
      prompt: formData.value.prompt,
      model: formData.value.model,
      watermark_bits: hexToBinary(formData.value.watermark),
      seed: formData.value.seed,
    }, { timeout: 200000 })

    const payload = response?.data || {}
    isGenerating.value = false

  // 生成完成后立即加载结果文件做预览。
    await initViewer()
    loadGsFromUrl(payload.gs_url)

    const generatedAt = payload.generated_at ? new Date(payload.generated_at) : new Date()
    result.value = {
      gaussianCount: payload.gaussian_count || 0,
      watermark: payload.watermark_bits ? binaryToHex(payload.watermark_bits) : formData.value.watermark,
      timeTaken: ((payload.elapsed_ms || 0) / 1000).toFixed(1),
      timestamp: generatedAt.toLocaleString('zh-CN', { hour12: false }),
      downloadUrl: payload.download_url || payload.gs_url,
      gsUrl: payload.gs_url,
      fileName: payload.gs_id ? `${payload.gs_id}.ply` : 'watermarked_3dgs.ply',
    }

    ElMessage.success('3DGS 模型生成并嵌入水印成功！')
    fetchRecentRecords()
  } catch (err) {
    isGenerating.value = false
    const message = err?.response?.data?.detail || err?.message || '3DGS 模型生成失败，请稍后重试'
    ElMessage.error(message)
  }
}

// ==================== 生命周期清理 ====================

onMounted(() => fetchRecentRecords())

onBeforeUnmount(() => {
  // 路由离开时：先同步 stop 停掉渲染循环（避免卡顿），再异步 dispose
  // 组件卸载时释放 viewer 和 URL，防止路由切换后继续占用资源。
  const v = viewer.value
  viewer.value = null
  if (v) {
    try { v.stop() } catch { /* ignore */ }
    // 延迟 dispose 避免阻塞路由切换动画
    v.dispose().catch(() => {})
  }
})
</script>

<style scoped>
:deep(.el-upload-dragger) {
  background-color: #f8fafc;
  border: 2px dashed #cbd5e1;
  border-radius: 1rem;
  padding: 30px 20px;
  transition: all 0.3s ease;
}
:deep(.el-upload-dragger:hover) {
  border-color: #7c3aed;
  background-color: #f5f3ff;
}
</style>
