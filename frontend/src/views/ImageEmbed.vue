<template>
  <div class="max-w-[1400px] mx-auto pb-8 pt-2">
    <div class="flex items-center gap-3 mb-6 px-2">
      <div class="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
        <el-icon class="text-xl"><Picture /></el-icon>
      </div>
      <h2 class="text-2xl font-bold text-gray-800 tracking-tight">生成含水印图像</h2>
    </div>

    <!-- 左右两栏布局 (左 5/12 约 40%，右 7/12 约 60%) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      
      <!-- ================= 左侧栏：参数配置区域 ================= -->
      <div class="lg:col-span-5 space-y-6">
        <!-- 配置卡片 -->
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <h3 class="text-lg font-bold text-gray-800 mb-5">生成参数配置</h3>
          
          <el-form label-position="top" class="space-y-4">
            <!-- 1. Prompt 输入框 -->
            <el-form-item label="提示词 (Prompt)">
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
            <el-form-item label="水印信息 (32位二进制)">
              <div class="flex gap-2 w-full">
                <el-input
                  v-model="formData.watermark"
                  placeholder="请输入32位二进制水印，如 10101010..."
                  size="large"
                  maxlength="32"
                  class="flex-1 font-mono"
                />
                <el-button size="large" @click="generateRandomWatermark" class="shrink-0">
                  <el-icon class="mr-1"><Refresh /></el-icon> 随机生成
                </el-button>
              </div>
            </el-form-item>

            <!-- 4. 生成按钮 -->
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
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
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
        </div>
      </div>

      <!-- ================= 右侧栏：结果预览区域 ================= -->
      <div class="lg:col-span-7 space-y-6">
        
        <!-- 图像预览卡片 -->
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col h-[500px]">
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

            <!-- 有图状态 -->
            <div v-else class="w-full h-full overflow-auto flex items-center justify-center custom-scrollbar">
              <img 
                :src="result.imageUrl" 
                alt="Generated Image" 
                class="transition-transform duration-200 origin-center"
                :style="{ transform: `scale(${zoomLevel})`, objectFit: 'contain', maxHeight: '100%', maxWidth: '100%' }"
              />
            </div>
          </div>
        </div>

        <!-- 生成完成后的信息与操作 -->
        <transition name="el-fade-in-linear">
          <div v-if="result" class="space-y-6">
            
            <!-- 操作按钮组 & 生成耗时 -->
            <div class="flex items-center justify-between bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
              <span class="text-sm text-gray-500 font-medium ml-2">
                <el-icon class="mr-1 align-middle"><Timer /></el-icon>
                生成耗时: <span class="text-gray-800 font-bold">{{ result.timeTaken }}s</span>
              </span>
              <div class="flex gap-3">
                <el-button plain round @click="handleGenerate">重新生成</el-button>
                <el-button type="primary" round class="shadow-md shadow-blue-500/20">
                  <el-icon class="mr-1"><Download /></el-icon> 下载图像
                </el-button>
              </div>
            </div>

            <!-- 水印信息卡片 -->
            <div class="bg-blue-50/50 rounded-3xl p-6 border border-blue-100 relative overflow-hidden">
              <div class="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-2xl -mr-10 -mt-10"></div>
              
              <h4 class="text-sm font-bold text-blue-800 mb-4 flex items-center">
                <el-icon class="mr-2 text-lg"><Key /></el-icon> 已嵌入水印信息
              </h4>
              
              <div class="bg-white rounded-xl p-4 border border-blue-100/50 flex justify-between items-center shadow-sm mb-4">
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
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

// 表单数据
const formData = ref({
  prompt: '',
  model: 'flux2',
  watermark: ''
})

// 状态控制
const isGenerating = ref(false)
const result = ref(null)
const zoomLevel = ref(1)

// 随机生成 32 位二进制水印
const generateRandomWatermark = () => {
  let binaryStr = ''
  for (let i = 0; i < 32; i++) {
    binaryStr += Math.random() > 0.5 ? '1' : '0'
  }
  formData.value.watermark = binaryStr
}

// 格式化水印 (每 8 位加一个空格)
const formattedWatermark = computed(() => {
  if (!result.value || !result.value.watermark) return ''
  return result.value.watermark.replace(/(.{8})/g, '$1 ').trim()
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

// 模拟生成请求
const handleGenerate = () => {
  if (!formData.value.prompt) {
    ElMessage.warning('请输入提示词')
    return
  }
  if (!formData.value.watermark || formData.value.watermark.length !== 32) {
    ElMessage.warning('请输入有效的 32 位二进制水印')
    return
  }

  isGenerating.value = true
  result.value = null
  resetZoom()

  // 模拟网络请求延迟 (2.5秒)
  setTimeout(() => {
    isGenerating.value = false
    
    // 构造模拟结果数据
    const now = new Date()
    result.value = {
      imageUrl: 'https://picsum.photos/seed/' + Math.random() + '/800/600', // 随机占位图
      watermark: formData.value.watermark,
      timeTaken: (Math.random() * 5 + 8).toFixed(1), // 模拟 8-13秒 耗时
      timestamp: now.toLocaleString('zh-CN', { hour12: false })
    }
    
    ElMessage.success('图像生成并嵌入水印成功！')
  }, 2500)
}
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
}
:deep(.custom-textarea .el-textarea__inner:hover) {
  border-color: #cbd5e1;
}
:deep(.custom-textarea .el-textarea__inner:focus) {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
  background-color: #ffffff;
}
</style>