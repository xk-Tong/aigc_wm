<template>
  <div class="max-w-[1400px] mx-auto pb-8 pt-2">
    <!-- 页面标题 -->
    <div class="flex items-center gap-3 mb-6 px-2">
      <div class="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center text-indigo-600">
        <el-icon class="text-xl"><Location /></el-icon>
      </div>
      <h2 class="text-2xl font-bold text-gray-800 tracking-tight">点云水印嵌入</h2>
    </div>

    <!-- 左右两栏布局 -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      
      <!-- ================= 左侧栏：参数配置区域 ================= -->
      <div class="lg:col-span-5 space-y-6">
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
            <el-form-item label="点云描述 (Prompt)" prop="prompt">
              <el-input
                v-model="formData.prompt"
                type="textarea"
                :rows="4"
                maxlength="2000"
                show-word-limit
                placeholder="请输入点云描述"
                class="custom-textarea"
              />
            </el-form-item>

            <!-- 2. 模型选择 -->
            <el-form-item label="生成模型">
              <el-select v-model="formData.model" size="large" class="w-full">
                <el-option label="Trellis (推荐)" value="trellis" />
                <el-option label="Point-E" value="pointe" />
                <el-option label="Shape-E" value="shapee" />
              </el-select>
            </el-form-item>

            <!-- 3. 水印信息输入 -->
            <el-form-item label="水印信息 (8位十六进制)" prop="watermark">
              <div class="flex gap-2 w-full">
                <el-input
                  v-model="formData.watermark"
                  placeholder="请输入8位十六进制水印，如 A1B2C3D4..."
                  size="large"
                  maxlength="8"
                  class="flex-1 font-mono"
                />
                <el-button size="large" @click="generateRandomWatermark" class="shrink-0">
                  <el-icon class="mr-1"><Refresh /></el-icon> 随机生成
                </el-button>
              </div>
            </el-form-item>

            <!-- 4. 随机种子 -->
            <el-form-item label="随机种子 (Seed)">
              <el-input-number
                v-model="formData.seed"
                :min="0"
                :step="1"
                :precision="0"
                controls-position="right"
                size="large"
                placeholder="可选，留空则使用随机种子"
                class="w-full param-input-number"
              />
              <div class="text-xs text-gray-400 mt-1">可选参数，设置后相同种子可生成一致的点云</div>
            </el-form-item>

            <!-- 5. 生成按钮 -->
            <div class="pt-4">
              <el-button 
                type="primary" 
                size="large" 
                class="w-full !h-14 !text-lg !rounded-xl shadow-lg shadow-indigo-500/30 !bg-indigo-600 hover:!bg-indigo-700 !border-none"
                :loading="isGenerating"
                @click="handleGenerate"
              >
                <el-icon class="mr-2" v-if="!isGenerating"><MagicStick /></el-icon>
                {{ isGenerating ? '正在生成点云并嵌入水印...' : '生成点云' }}
              </el-button>
            </div>
          </el-form>
        </div>
      </div>

      <!-- ================= 右侧栏：结果预览区域 ================= -->
      <div class="lg:col-span-7 space-y-6">
        
        <!-- 3D 预览区域 -->
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col h-[500px]" ref="fullscreenContainer">
          <div class="flex justify-between items-center mb-4 shrink-0">
            <h3 class="text-lg font-bold text-gray-800">3D 预览</h3>
            <!-- 工具栏 -->
            <el-button-group v-if="result">
              <el-button size="small" title="重置视角" @click="resetView"><el-icon><RefreshLeft /></el-icon></el-button>
              <el-button size="small" title="切换背景色" @click="toggleBackground"><el-icon><PictureRounded /></el-icon></el-button>
              <el-button size="small" title="显示/隐藏坐标轴" @click="toggleAxes"><el-icon><Position /></el-icon></el-button>
              <el-button size="small" title="全屏预览" @click="toggleFullscreen"><el-icon><FullScreen /></el-icon></el-button>
            </el-button-group>
          </div>

          <!-- Three.js 渲染容器 -->
          <div class="flex-1 rounded-2xl overflow-hidden relative border border-gray-100 bg-[#1e1e1e]" ref="canvasContainer">
            
            <!-- 空白状态 -->
            <div v-if="!result && !isGenerating" class="absolute inset-0 flex flex-col items-center justify-center text-gray-400 bg-[#f8fafc] z-10">
              <el-icon class="text-5xl mb-2 opacity-50"><Box /></el-icon>
              <p>等待生成</p>
            </div>
            
            <!-- 加载状态 -->
            <div v-else-if="isGenerating" class="absolute inset-0 flex flex-col items-center justify-center bg-[#f8fafc]/90 backdrop-blur-sm z-10">
              <el-icon class="text-5xl mb-2 is-loading text-indigo-500"><Loading /></el-icon>
              <p class="text-sm font-medium text-indigo-600 mt-4 animate-pulse">正在生成点云并嵌入水印...</p>
            </div>

            <!-- Canvas 将由 Three.js 挂载到这里 -->
          </div>
        </div>

        <!-- 生成完成后的信息与操作 -->
        <transition name="el-fade-in-linear">
          <div v-if="result" class="space-y-6">
            
            <!-- 模型信息行 & 操作按钮 -->
            <div class="flex flex-wrap items-center justify-between bg-white rounded-2xl p-4 shadow-sm border border-gray-100 gap-4">
              <div class="flex items-center gap-4 text-sm text-gray-600 font-medium ml-2">
                <span><el-icon class="mr-1 align-middle"><DataAnalysis /></el-icon> 原始点数: <span class="text-gray-800 font-bold">{{ result.pointsCount.toLocaleString() }}</span></span>
                <el-divider direction="vertical" />
                <span><el-icon class="mr-1 align-middle"><Timer /></el-icon> 生成耗时: <span class="text-gray-800 font-bold">{{ result.timeTaken }}s</span></span>
              </div>
              
              <div class="flex gap-3">
                <el-button plain round @click="handleGenerate">重新生成</el-button>
                <el-button type="primary" round class="shadow-md shadow-indigo-500/20 !bg-indigo-600 !border-none" @click="handleDownload">
                  <el-icon class="mr-1"><Download /></el-icon> 下载点云
                </el-button>
              </div>
            </div>

            <!-- 水印信息卡片 -->
            <div class="bg-indigo-50/50 rounded-3xl p-6 border border-indigo-100 relative overflow-hidden">
              <div class="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-2xl -mr-10 -mt-10"></div>
              
              <h4 class="text-sm font-bold text-indigo-800 mb-4 flex items-center">
                <el-icon class="mr-2 text-lg"><Key /></el-icon> 已嵌入水印信息
              </h4>
              
              <div class="bg-white rounded-xl p-4 border border-indigo-100/50 flex justify-between items-center shadow-sm mb-4">
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
import { ref, computed, onBeforeUnmount, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { PLYLoader } from 'three/examples/jsm/loaders/PLYLoader.js'

const formData = ref({
  prompt: '',
  model: 'trellis',
  watermark: '',
  seed: null,
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

const formRules = {
  prompt: [
    { required: true, message: '请输入点云描述', trigger: 'blur' },
    { min: 1, max: 2000, message: '描述长度需在 1-2000 字符之间', trigger: 'blur' },
  ],
  watermark: [
    { required: true, message: '请输入 8 位十六进制水印', trigger: 'blur' },
    { pattern: /^[0-9A-Fa-f]{8}$/, message: '请输入有效的 8 位十六进制水印', trigger: 'blur' },
  ],
}

const isGenerating = ref(false)
const result = ref(null)

const canvasContainer = ref(null)
const fullscreenContainer = ref(null)
const scene = shallowRef(null)
const camera = shallowRef(null)
const renderer = shallowRef(null)
const controls = shallowRef(null)
const pointsObject = shallowRef(null)
const axesHelper = shallowRef(null)
let animationFrameId = null

const generateRandomWatermark = () => {
  const hexChars = '0123456789ABCDEF'
  let hexStr = ''
  for (let i = 0; i < 8; i++) hexStr += hexChars[Math.floor(Math.random() * 16)]
  formData.value.watermark = hexStr
}

const formattedWatermark = computed(() => {
  if (!result.value || !result.value.watermark) return ''
  return result.value.watermark
})

const copyWatermark = async () => {
  try {
    await navigator.clipboard.writeText(result.value.watermark)
    ElMessage.success('水印已复制到剪贴板')
  } catch (err) {
    ElMessage.error('复制失败')
  }
}

const handleDownload = () => {
  if (!result.value?.downloadUrl) {
    ElMessage.warning('暂无可下载点云文件')
    return
  }
  window.open(result.value.downloadUrl, '_blank', 'noopener,noreferrer')
}

const initThree = () => {
  if (!canvasContainer.value) return

  scene.value = new THREE.Scene()
  scene.value.background = new THREE.Color(0x1e1e1e)

  const width = canvasContainer.value.clientWidth
  const height = canvasContainer.value.clientHeight
  camera.value = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000)
  camera.value.position.set(0, 0, 5)

  renderer.value = new THREE.WebGLRenderer({ antialias: true })
  renderer.value.setSize(width, height)
  renderer.value.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  canvasContainer.value.appendChild(renderer.value.domElement)

  controls.value = new OrbitControls(camera.value, renderer.value.domElement)
  controls.value.enableDamping = true
  controls.value.dampingFactor = 0.05

  axesHelper.value = new THREE.AxesHelper(2)
  scene.value.add(axesHelper.value)

  window.addEventListener('resize', onWindowResize)
  animate()
}

const animate = () => {
  animationFrameId = requestAnimationFrame(animate)
  if (controls.value) controls.value.update()
  if (renderer.value && scene.value && camera.value) {
    renderer.value.render(scene.value, camera.value)
  }
}

const onWindowResize = () => {
  if (!canvasContainer.value || !camera.value || !renderer.value) return
  const width = canvasContainer.value.clientWidth
  const height = canvasContainer.value.clientHeight
  camera.value.aspect = width / height
  camera.value.updateProjectionMatrix()
  renderer.value.setSize(width, height)
}

const loadPointCloudFromUrl = (url) => {
  if (!scene.value) return

  if (pointsObject.value) {
    scene.value.remove(pointsObject.value)
    disposeObject3D(pointsObject.value)
    pointsObject.value = null
  }

  new PLYLoader().load(
    url,
    (geometry) => {
      geometry.computeBoundingBox()
      const box = geometry.boundingBox
      const center = box.getCenter(new THREE.Vector3())
      const size = box.getSize(new THREE.Vector3()).length()

      geometry.translate(-center.x, -center.y, -center.z)

      const scale = 4 / (size || 1)
      const hasColor = geometry.hasAttribute('color')

      const material = new THREE.PointsMaterial({
        size: 0.03 / scale,
        vertexColors: hasColor,
        color: hasColor ? 0xffffff : 0x4f46e5,
        transparent: true,
        opacity: 0.8,
      })

      pointsObject.value = new THREE.Points(geometry, material)
      pointsObject.value.scale.setScalar(scale)
      pointsObject.value.rotation.x = Math.PI
      scene.value.add(pointsObject.value)
      resetView()

      if (result.value) {
        result.value.pointsCount = geometry.attributes.position.count
      }
    },
    undefined,
    () => {
      ElMessage.error('点云文件加载失败，请检查文件是否损坏')
    }
  )
}

const disposeMaterial = (material) => {
  if (!material) return
  if (Array.isArray(material)) {
    material.forEach((item) => item?.dispose?.())
    return
  }
  material.dispose?.()
}

const disposeObject3D = (object) => {
  object?.traverse?.((child) => {
    if (child.isMesh || child.isPoints || child.isLine) {
      child.geometry?.dispose?.()
      disposeMaterial(child.material)
    }
  })
}

const resetView = () => {
  if (camera.value && controls.value) {
    camera.value.position.set(0, 0, 5)
    controls.value.target.set(0, 0, 0)
    controls.value.update()
  }
}

const toggleBackground = () => {
  if (scene.value) {
    const currentHex = scene.value.background.getHexString()
    scene.value.background = new THREE.Color(currentHex === '1e1e1e' ? 0xf8fafc : 0x1e1e1e)
  }
}

const toggleAxes = () => {
  if (axesHelper.value) {
    axesHelper.value.visible = !axesHelper.value.visible
  }
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    fullscreenContainer.value?.requestFullscreen().catch(() => {
      ElMessage.error('全屏请求失败')
    })
  } else {
    document.exitFullscreen()
  }
}

const handleGenerate = async () => {
  try {
    await generateFormRef.value.validate()
  } catch (_err) {
    ElMessage.warning('请先修正参数输入后再生成点云')
    return
  }

  isGenerating.value = true
  result.value = null

  try {
    const response = await request.post('/api/v1/pointcloud/generate-watermarked', {
      prompt: formData.value.prompt,
      model: formData.value.model,
      watermark_bits: formData.value.watermark,
      seed: formData.value.seed,
    })

    const payload = response?.data || {}
    isGenerating.value = false

    if (!scene.value) initThree()
    loadPointCloudFromUrl(payload.pointcloud_url)

    const generatedAt = payload.generated_at ? new Date(payload.generated_at) : new Date()
    result.value = {
      // 算法端返回的点数不再由接口直接返回，在3D模型加载完成后更新
      pointsCount: 0, 
      watermark: payload.watermark_bits || formData.value.watermark,
      timeTaken: ((payload.elapsed_ms || 0) / 1000).toFixed(1),
      timestamp: generatedAt.toLocaleString('zh-CN', { hour12: false }),
      downloadUrl: payload.download_url || payload.pointcloud_url,
    }

    ElMessage.success('点云生成并嵌入水印成功！')
  } catch (err) {
    isGenerating.value = false
    const message =
      err?.response?.data?.detail || err?.message || '点云生成失败，请稍后重试'
    ElMessage.error(message)
  }
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', onWindowResize)
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
  if (pointsObject.value) {
    if (scene.value) scene.value.remove(pointsObject.value)
    disposeObject3D(pointsObject.value)
  }
  if (renderer.value) {
    renderer.value.dispose()
    renderer.value.forceContextLoss()
  }
})
</script>

<style scoped>
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
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
  border-color: #4f46e5;
  background-color: #ffffff;
}

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
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
  border-color: #4f46e5;
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
  color: #4f46e5;
}

:fullscreen {
  background-color: #f4f6f8;
  padding: 24px;
}
</style>
