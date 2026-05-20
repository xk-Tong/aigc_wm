<template>
  <div class="max-w-[1400px] mx-auto pb-8 pt-2">
    <div class="flex items-center gap-3 mb-6 px-2">
      <div class="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center text-violet-600">
        <el-icon class="text-xl"><Crop /></el-icon>
      </div>
      <h2 class="text-2xl font-bold text-gray-800 tracking-tight">3DGS 水印提取</h2>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

      <!-- ================= 左侧栏：3DGS 上传区域 ================= -->
      <div class="lg:col-span-5 space-y-6">
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <div class="flex justify-between items-center mb-5">
            <h3 class="text-lg font-bold text-gray-800">3DGS 文件上传</h3>
            <el-button v-if="uploadedFile" type="primary" link @click="removeFile">重新上传</el-button>
          </div>

          <el-upload
            v-if="!uploadedFile"
            class="custom-upload"
            drag
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            accept=".ply"
            @change="handleFileChange"
          >
            <el-icon class="el-icon--upload text-violet-400"><UploadFilled /></el-icon>
            <div class="el-upload__text text-gray-600">将 3DGS PLY 文件拖拽到此处，或 <em class="text-violet-500 font-bold not-italic">点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip text-gray-400 text-center mt-3">支持 .ply 格式 3DGS 文件，最大不超过 100MB</div>
            </template>
          </el-upload>

          <div v-else class="bg-gray-50 rounded-2xl p-4 border border-gray-200">
            <div class="flex flex-col items-center">
              <div class="w-full h-[160px] rounded-xl bg-linear-to-br from-violet-900 to-gray-900 mb-4 flex items-center justify-center relative overflow-hidden shadow-inner">
                <div class="absolute inset-0 opacity-20" style="background-image: linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px); background-size: 20px 20px;"></div>
                <el-icon class="text-5xl text-violet-300/80 z-10"><Histogram /></el-icon>
              </div>

              <div class="w-full flex items-center justify-between bg-white p-3 rounded-xl border border-gray-100 shadow-sm">
                <div class="flex items-center gap-3 overflow-hidden">
                  <div class="w-10 h-10 rounded-lg bg-violet-50 flex items-center justify-center text-violet-500 shrink-0">
                    <span class="text-xs font-bold">PLY</span>
                  </div>
                  <div class="overflow-hidden">
                    <p class="text-sm font-bold text-gray-800 truncate" :title="fileInfo.name">{{ fileInfo.name }}</p>
                    <div class="flex items-center gap-2 text-xs text-gray-400 mt-0.5">
                      <span>{{ fileInfo.size }}</span>
                    </div>
                  </div>
                </div>
                <el-button type="danger" plain circle size="small" @click="removeFile" class="shrink-0 ml-2"><el-icon><Delete /></el-icon></el-button>
              </div>
            </div>
          </div>

          <div class="mt-6">
            <el-collapse class="custom-collapse">
              <el-collapse-item title="支持的文件格式说明" name="1">
                <div class="text-xs text-gray-500 space-y-2 leading-relaxed">
                  <p><strong>.ply:</strong> 3D Gaussian Splatting 的标准存储格式，包含每个 Gaussian 的位置、旋转、缩放、颜色和不透明度等属性。</p>
                  <p>PLY 文件由 INRIA gaussian-splatting 训练流程生成，是学术界和工具链中最主流的 3DGS 输出格式。</p>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>
      </div>

      <!-- ================= 右侧栏：提取结果与 3D 预览 ================= -->
      <div class="lg:col-span-7 space-y-6">
        <el-button
          type="primary" size="large" class="w-full h-14! text-lg! rounded-xl! shadow-lg shadow-violet-500/30 bg-violet-600! hover:bg-violet-700! border-none! transition-all"
          :disabled="!uploadedFile" :loading="isExtracting" @click="startExtraction"
        >
          <el-icon class="mr-2" v-if="!isExtracting"><Search /></el-icon>
          {{ isExtracting ? '正在解析 3DGS Gaussian 特征...' : '提取水印' }}
        </el-button>

        <div class="bg-white rounded-3xl p-6 shadow-sm border-2 transition-all duration-300 min-h-[220px] flex flex-col justify-center relative overflow-hidden" :class="resultCardClass">
          <div v-if="!result && !isExtracting" class="text-center text-gray-400">
            <el-icon class="text-5xl mb-3 opacity-30"><DocumentScanner /></el-icon>
            <p class="font-medium">等待提取</p>
          </div>

          <div v-else-if="result && result.status === 'success'" class="relative z-10">
            <div class="flex items-center justify-between mb-6">
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600"><el-icon><Select /></el-icon></div>
                <h3 class="text-lg font-bold text-green-700">提取成功</h3>
              </div>
              <el-button size="small" round @click="copyWatermark"><el-icon class="mr-1"><CopyDocument /></el-icon> 复制水印</el-button>
            </div>
            <div class="bg-gray-50 rounded-2xl p-5 border border-gray-100 mb-5">
              <p class="text-xs text-gray-500 mb-2 font-medium">提取到的水印内容：</p>
              <p class="font-mono text-2xl text-gray-800 tracking-widest font-bold">{{ result.watermark }}</p>
            </div>
            <div class="flex flex-wrap items-center gap-4 text-sm text-gray-500">
              <span><el-icon class="mr-1 align-middle"><Timer /></el-icon> 提取耗时: <span class="font-bold text-gray-800">{{ result.timeTaken }}s</span></span>
              <el-divider direction="vertical" />
              <span><el-icon class="mr-1 align-middle"><DataAnalysis /></el-icon> 文件大小: <span class="font-bold text-gray-800">{{ fileInfo.size }}</span></span>
            </div>
          </div>

          <div v-else-if="result && result.status === 'error'" class="text-center relative z-10">
            <div class="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center text-red-500 mx-auto mb-4"><el-icon class="text-3xl"><WarningFilled /></el-icon></div>
            <h3 class="text-lg font-bold text-red-600 mb-2">提取失败</h3>
            <p class="text-sm text-gray-600">{{ result.message }}</p>
          </div>
          <div v-if="result && result.status === 'success'" class="absolute -right-10 -bottom-10 w-40 h-40 bg-green-400/10 rounded-full blur-3xl pointer-events-none"></div>
        </div>

        <div v-show="uploadedFile" class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col h-[400px]">
          <div class="flex justify-between items-center mb-4 shrink-0">
            <h3 class="text-md font-bold text-gray-800">3DGS 渲染预览</h3>
          </div>
          <div class="flex-1 rounded-2xl overflow-hidden relative border border-gray-100 bg-[#1a1a2e]">
            <!-- gsplat.js 独占的渲染容器，不包含 Vue 管理的子节点 -->
            <div ref="gsContainer" class="absolute inset-0"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, shallowRef, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

// 动态加载 gsplat 库，避免顶层 import 阻塞路由切换
let _gsModule = null
const ensureGsplatLoaded = async () => {
  if (!_gsModule) {
    _gsModule = await import('@mkkellogg/gaussian-splats-3d')
  }
  return _gsModule
}

// ==================== 响应式状态 ====================

const uploadedFile = ref(null)
const fileInfo = ref({ name: '', size: '' })
const isExtracting = ref(false)
const result = ref(null)

// ==================== Gaussian Splats 3D ====================

// gsContainer 是 gsplat.js 的独占渲染容器，与 Vue 管理的 overlay DOM 隔离
const gsContainer = ref(null)
const viewer = shallowRef(null)
let objectUrl = null

// ==================== 计算属性 ====================

const resultCardClass = computed(() => {
  if (!result.value) return 'border-gray-100'
  return result.value.status === 'success' ? 'border-green-400 bg-green-50/30' : 'border-red-400 bg-red-50/30'
})

// ==================== 文件处理 ====================

const handleFileChange = (uploadFile) => {
  const file = uploadFile.raw
  if (!file) return

  if (file.size > 100 * 1024 * 1024) {
    ElMessage.error('3DGS 文件大小不能超过 100MB！')
    return
  }

  const ext = file.name.split('.').pop().toLowerCase()
  if (ext !== 'ply') {
    ElMessage.error('只支持 PLY 格式的 3DGS 文件')
    return
  }

  uploadedFile.value = file

  const sizeMB = (file.size / (1024 * 1024)).toFixed(2)
  fileInfo.value = {
    name: file.name,
    size: sizeMB > 1 ? `${sizeMB} MB` : `${(file.size / 1024).toFixed(2)} KB`,
  }

  result.value = null

  nextTick(() => {
    loadUserGs(file)
  })
}

const removeFile = () => {
  uploadedFile.value = null
  result.value = null
  cleanupViewer()
}

// ==================== Viewer 管理 ====================

const initViewer = async () => {
  if (!gsContainer.value) return

  await cleanupViewer()

  const GS3D = await ensureGsplatLoaded()

  viewer.value = new GS3D.Viewer({
    rootElement: gsContainer.value,
    cameraUp: [0, 1, 0],
    initialCameraPosition: [0, 0, 6],
    initialCameraLookAt: [0, 0, 0],
    dynamicScene: false,
    selfDrivenMode: true,
  })
}

const loadUserGs = async (file) => {
  await initViewer()
  if (!viewer.value) return

  objectUrl = URL.createObjectURL(file)

  const GS3D = await ensureGsplatLoaded()

  try {
    await viewer.value.addSplatScene(objectUrl, {
      splatAlphaRemovalThreshold: 5,
      showLoadingUI: false,
      // 关键：blob URL 不以 .ply 结尾，必须显式指定格式
      format: GS3D.SceneFormat.Ply,
    })
    viewer.value.start()
  } catch (e) {
    console.error('[GsExtract] addSplatScene failed:', e)
    ElMessage.error('3DGS PLY 文件加载失败，请检查文件格式是否正确')
  }
}

/**
 * 安全清理 viewer：
 * 1. 先同步 stop() 停止渲染循环
 * 2. 清空容器（gsContainer 不含 Vue 子节点，安全操作）
 * 3. 异步 dispose() 释放 GPU 资源
 */
const cleanupViewer = async () => {
  if (objectUrl) {
    URL.revokeObjectURL(objectUrl)
    objectUrl = null
  }

  const v = viewer.value
  viewer.value = null

  if (v) {
    try { v.stop() } catch { /* ignore */ }
    if (gsContainer.value) gsContainer.value.innerHTML = ''
    try { await v.dispose() } catch { /* ignore */ }
  }
}

// ==================== 水印提取 ====================

const binaryToHex = (binary) => parseInt(binary, 2).toString(16).toUpperCase().padStart(8, '0')

const copyWatermark = async () => {
  await navigator.clipboard.writeText(result.value.watermark)
  ElMessage.success('水印内容已复制')
}

const startExtraction = async () => {
  if (!uploadedFile.value) return

  isExtracting.value = true
  result.value = null

  try {
    const formDataObj = new FormData()
    formDataObj.append('gs_file', uploadedFile.value)

    const response = await request.post('/api/v1/gs/extract-watermark', formDataObj)
    const payload = response?.data || {}
    const watermarkBits = payload.watermark_bits || payload.extracted_watermark || ''

    if (!/^[01]{32}$/.test(watermarkBits)) {
      throw new Error('算法服务返回了非法的水印数据')
    }

    const hexWatermark = binaryToHex(watermarkBits)

    isExtracting.value = false

    result.value = {
      status: 'success',
      watermark: hexWatermark,
      timeTaken: ((payload.elapsed_ms || 0) / 1000).toFixed(2),
    }
    ElMessage.success('水印提取成功！')
  } catch (err) {
    isExtracting.value = false
    const message = err?.response?.data?.detail || err?.message || '3DGS 数据可能已被破坏或未包含有效的水印特征，提取失败。'
    result.value = { status: 'error', message }
    ElMessage.error(message)
  }
}

// ==================== 生命周期清理 ====================

onBeforeUnmount(() => {
  if (objectUrl) {
    URL.revokeObjectURL(objectUrl)
    objectUrl = null
  }
  const v = viewer.value
  viewer.value = null
  if (v) {
    try { v.stop() } catch { /* ignore */ }
    v.dispose().catch(() => {})
  }
})
</script>

<style scoped>
:deep(.custom-upload .el-upload-dragger) {
  background-color: #f8fafc;
  border: 2px dashed #cbd5e1;
  border-radius: 1rem;
  padding: 30px 20px;
  transition: all 0.3s ease;
}
:deep(.custom-upload .el-upload-dragger:hover) {
  border-color: #7c3aed;
  background-color: #f5f3ff;
}
:deep(.custom-collapse) {
  border-top: none;
  border-bottom: none;
}
:deep(.custom-collapse .el-collapse-item__header) {
  background-color: transparent;
  border-bottom: 1px solid #f1f5f9;
  font-weight: 600;
  color: #475569;
}
:deep(.custom-collapse .el-collapse-item__wrap) {
  background-color: transparent;
  border-bottom: none;
}
</style>
