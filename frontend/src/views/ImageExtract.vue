<template>
  <div class="max-w-[1400px] mx-auto pb-8 pt-2">
    <!-- 页面标题 -->
    <div class="flex items-center gap-3 mb-6 px-2">
      <div class="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center text-blue-600">
        <el-icon class="text-xl"><Crop /></el-icon>
      </div>
      <h2 class="text-2xl font-bold text-gray-800 tracking-tight">图像水印提取</h2>
    </div>

    <!-- 左右两栏布局 (左 40%，右 60%) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      
      <!-- ================= 左侧栏：图像上传区域 ================= -->
      <div class="lg:col-span-5 space-y-6">
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <h3 class="text-lg font-bold text-gray-800 mb-5">图像上传</h3>
          
          <!-- 拖拽上传区域 (未上传时显示) -->
          <el-upload
            v-if="!uploadedFileUrl"
            class="custom-upload"
            drag
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            accept=".jpg,.jpeg,.png,.webp"
            @change="handleFileChange"
          >
            <el-icon class="el-icon--upload text-blue-400"><UploadFilled /></el-icon>
            <div class="el-upload__text text-gray-600">
              将图像拖拽到此处，或 <em class="text-blue-500 font-bold not-italic">点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip text-gray-400 text-center mt-3">
                支持 JPG, PNG, WEBP 格式图像，最大不超过 10MB
              </div>
            </template>
          </el-upload>

          <!-- 已上传图像预览 (上传后显示) -->
          <div v-else class="bg-gray-50 rounded-2xl p-4 border border-gray-200">
            <div class="flex flex-col items-center">
              <!-- 缩略图 -->
              <div class="w-full max-h-[200px] rounded-xl overflow-hidden bg-gray-200 mb-4 flex items-center justify-center">
                <img :src="uploadedFileUrl" class="max-w-full max-h-[200px] object-contain" alt="Thumbnail" />
              </div>
              
              <!-- 文件信息 -->
              <div class="w-full flex items-center justify-between bg-white p-3 rounded-xl border border-gray-100 shadow-sm">
                <div class="flex items-center gap-3 overflow-hidden">
                  <el-icon class="text-blue-500 text-2xl shrink-0"><Picture /></el-icon>
                  <div class="overflow-hidden">
                    <p class="text-sm font-bold text-gray-800 truncate" :title="fileInfo.name">{{ fileInfo.name }}</p>
                    <p class="text-xs text-gray-400 mt-0.5">{{ fileInfo.size }}</p>
                  </div>
                </div>
                <!-- 移除按钮 -->
                <el-button type="danger" plain circle size="small" @click="removeFile" class="shrink-0 ml-2">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ================= 右侧栏：提取结果区域 ================= -->
      <div class="lg:col-span-7 space-y-6">
        
        <!-- 提取按钮 -->
        <el-button 
          type="primary" 
          size="large" 
          class="w-full h-14! text-lg! rounded-xl! shadow-lg shadow-blue-500/30 transition-all"
          :disabled="!uploadedFileUrl"
          :loading="isExtracting"
          @click="startExtraction"
        >
          <el-icon class="mr-2" v-if="!isExtracting"><Search /></el-icon>
          {{ isExtracting ? '正在深度解析提取中...' : '提取水印' }}
        </el-button>

        <!-- 结果展示卡片 -->
        <div 
          class="bg-white rounded-3xl p-6 shadow-sm border-2 transition-all duration-300 min-h-[200px] flex flex-col justify-center relative overflow-hidden"
          :class="resultCardClass"
        >
          <!-- 状态 1: 空白状态 -->
          <div v-if="!result && !isExtracting" class="text-center text-gray-400">
            <el-icon class="text-5xl mb-3 opacity-30"><DocumentScanner /></el-icon>
            <p class="font-medium">等待提取</p>
            <p class="text-xs mt-1 opacity-70">请先上传图像并点击提取按钮</p>
          </div>

          <!-- 状态 2: 提取成功 -->
          <div v-else-if="result && result.status === 'success'" class="relative z-10">
            <div class="flex items-center gap-2 mb-6">
              <div class="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600">
                <el-icon><Select /></el-icon>
              </div>
              <h3 class="text-lg font-bold text-green-700">提取成功</h3>
            </div>

            <div class="bg-gray-50 rounded-2xl p-5 border border-gray-100 mb-5 relative group">
              <p class="text-xs text-gray-500 mb-2 font-medium">解析到的水印内容 (易读格式)：</p>
              <p class="font-mono text-2xl text-gray-800 tracking-widest font-bold mb-3">
                {{ formattedWatermark }}
              </p>
              
              <!-- 复制按钮 -->
              <el-button 
                size="small" 
                round 
                class="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity shadow-sm"
                @click="copyWatermark"
              >
                <el-icon class="mr-1"><CopyDocument /></el-icon> 复制内容
              </el-button>
            </div>

            <div class="flex items-center text-sm text-gray-500">
              <el-icon class="mr-1"><Timer /></el-icon>
              提取耗时: <span class="font-bold text-gray-800 ml-1">{{ result.timeTaken }}s</span>
            </div>
          </div>

          <!-- 状态 3: 提取失败 -->
          <div v-else-if="result && result.status === 'error'" class="text-center relative z-10">
            <div class="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center text-red-500 mx-auto mb-4">
              <el-icon class="text-3xl"><WarningFilled /></el-icon>
            </div>
            <h3 class="text-lg font-bold text-red-600 mb-2">提取失败</h3>
            <p class="text-sm text-gray-600">{{ result.message }}</p>
          </div>
          
          <!-- 成功时的背景光晕装饰 -->
          <div v-if="result && result.status === 'success'" class="absolute -right-10 -bottom-10 w-40 h-40 bg-green-400/10 rounded-full blur-3xl pointer-events-none"></div>
        </div>

        <!-- 图像大图预览卡片 (仅上传后显示) -->
        <div v-if="uploadedFileUrl" class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-md font-bold text-gray-800">图像预览</h3>
            <span class="text-xs text-gray-400">点击图像可放大查看细节</span>
          </div>
          <div class="bg-[#f8fafc] rounded-2xl p-2 flex justify-center items-center h-[300px] overflow-hidden border border-gray-50">
            <el-image 
              :src="uploadedFileUrl" 
              :preview-src-list="[uploadedFileUrl]" 
              fit="contain" 
              class="w-full h-full rounded-xl cursor-zoom-in hover:opacity-95 transition-opacity" 
            />
          </div>
        </div>

      </div>
    </div>

    <!-- 近期记录面板 -->
    <div class="mt-8 bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
      <el-collapse v-model="recentPanelActive">
        <el-collapse-item title="近期记录" name="recent">
          <div v-if="recentRecords.length === 0" class="text-center text-gray-400 py-4">暂无记录</div>
          <el-table v-else :data="recentRecords" size="small" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="extracted_bits" label="提取水印" width="140">
              <template #default="{ row }"><span class="font-mono text-xs">{{ row.extracted_bits || '-' }}</span></template>
            </el-table-column>
            <el-table-column prop="source_file_name" label="文件名" min-width="140">
              <template #default="{ row }"><span class="text-xs">{{ row.source_file_name || '-' }}</span></template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="70">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 'success' ? 'success' : 'danger'">{{ row.status === 'success' ? '成功' : '失败' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="elapsed_ms" label="耗时" width="90">
              <template #default="{ row }">{{ row.elapsed_ms ? `${(row.elapsed_ms / 1000).toFixed(1)}s` : '-' }}</template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="160">
              <template #default="{ row }">{{ formatRecentTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>
          <div class="flex justify-end mt-3">
            <el-button link type="primary" @click="$router.push('/data/history')">查看全部 <el-icon class="ml-1"><ArrowRight /></el-icon></el-button>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowRight } from '@element-plus/icons-vue'
import request from '../utils/request'

// 文件相关状态
const uploadedFileUrl = ref('')
const fileInfo = ref({ name: '', size: '' })
const uploadedFile = ref(null)

// 提取状态
const isExtracting = ref(false)
const result = ref(null)

// 处理文件选择/拖拽
const handleFileChange = (uploadFile) => {
  const file = uploadFile.raw
  if (!file) return

  // 校验格式
  const isValidFormat = ['image/jpeg', 'image/png', 'image/webp'].includes(file.type)
  if (!isValidFormat) {
    ElMessage.error('只支持 JPG, PNG, WEBP 格式的图像！')
    return
  }

  // 校验大小 (10MB)
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('图像大小不能超过 10MB！')
    return
  }

  // 生成本地预览 URL
  if (uploadedFileUrl.value) {
    URL.revokeObjectURL(uploadedFileUrl.value)
  }
  uploadedFileUrl.value = URL.createObjectURL(file)
  uploadedFile.value = file
  
  // 格式化文件大小
  const sizeMB = (file.size / (1024 * 1024)).toFixed(2)
  fileInfo.value = {
    name: file.name,
    size: sizeMB > 1 ? `${sizeMB} MB` : `${(file.size / 1024).toFixed(2)} KB`
  }
  
  // 清除之前的提取结果
  result.value = null
}

// 移除文件
const removeFile = () => {
  if (uploadedFileUrl.value) {
    URL.revokeObjectURL(uploadedFileUrl.value) // 释放内存
  }
  uploadedFileUrl.value = ''
  uploadedFile.value = null
  fileInfo.value = { name: '', size: '' }
  result.value = null
}

// 动态计算结果卡片的边框颜色类名
const resultCardClass = computed(() => {
  if (!result.value) return 'border-gray-100'
  if (result.value.status === 'success') return 'border-green-400 bg-green-50/30'
  if (result.value.status === 'error') return 'border-red-400 bg-red-50/30'
  return 'border-gray-100'
})

const binaryToHex = (binary) => parseInt(binary, 2).toString(16).toUpperCase().padStart(8, '0')

// 格式化水印
const formattedWatermark = computed(() => {
  if (!result.value || !result.value.watermark) return ''
  return result.value.watermark
})

// 复制水印到剪贴板
const copyWatermark = async () => {
  try {
    await navigator.clipboard.writeText(result.value.watermark)
    ElMessage.success('水印内容已复制到剪贴板')
  } catch (err) {
    ElMessage.error('复制失败，请手动复制')
  }
}

// 近期记录
const recentPanelActive = ref([])
const recentRecords = ref([])

const fetchRecentRecords = async () => {
  try {
    const res = await request.get('/api/v1/records', {
      params: { media_type: 'image', operation_type: 'extract', size: 5, page: 1 }
    })
    if (res?.data?.code === 200) {
      recentRecords.value = res.data.data.items
    }
  } catch { /* ignore */ }
}

const formatRecentTime = (t) => {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

// 向业务后端提交图像提取请求，并把结果展示到页面上。
const startExtraction = async () => {
  if (!uploadedFile.value) return

  isExtracting.value = true
  result.value = null

  try {
    const formData = new FormData()
    formData.append('image_file', uploadedFile.value)

    const response = await request.post('/api/v1/image/extract-watermark', formData)
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
      timestamp: payload.extracted_at
        ? new Date(payload.extracted_at).toLocaleString('zh-CN', { hour12: false })
        : new Date().toLocaleString('zh-CN', { hour12: false }),
    }
    ElMessage.success('水印提取成功！')
    fetchRecentRecords()
  } catch (err) {
    isExtracting.value = false

    result.value = {
      status: 'error',
      message: err?.response?.data?.detail || err?.message || '未检测到有效的水印信息，或图像已被严重破坏。'
    }
    ElMessage.error(result.value.message)
  }
}

onMounted(() => fetchRecentRecords())
</script>

<style scoped>
/* 深度定制 Element Plus 的拖拽上传组件样式 */
:deep(.custom-upload .el-upload-dragger) {
  background-color: #f8fafc;
  border: 2px dashed #cbd5e1;
  border-radius: 1rem;
  padding: 40px 20px;
  transition: all 0.3s ease;
}
:deep(.custom-upload .el-upload-dragger:hover) {
  border-color: #3b82f6;
  background-color: #eff6ff;
}
:deep(.custom-upload .el-upload-dragger.is-dragover) {
  border-color: #3b82f6;
  background-color: #eff6ff;
  transform: scale(1.02);
}
</style>