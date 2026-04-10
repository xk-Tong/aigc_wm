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
          
          <el-form label-position="top" class="space-y-4">
            <!-- 1. 输入类型切换 -->
            <el-form-item label="输入模式">
              <el-radio-group v-model="formData.inputType" class="w-full">
                <el-radio-button label="text" class="flex-1 text-center">文字输入</el-radio-button>
                <el-radio-button label="image" class="flex-1 text-center">图像输入</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <!-- 2. 文字输入模式 -->
            <el-form-item v-if="formData.inputType === 'text'" label="点云描述 (Prompt)">
              <el-input
                v-model="formData.prompt"
                type="textarea"
                :rows="4"
                maxlength="1000"
                show-word-limit
                placeholder="请输入点云描述，如：一只飞翔的鸟、一辆复古跑车..."
                class="custom-textarea"
              />
            </el-form-item>

            <!-- 3. 图像输入模式 -->
            <el-form-item v-if="formData.inputType === 'image'" label="参考图像">
              <el-upload
                v-if="!uploadedImageUrl"
                class="custom-upload"
                drag
                action="#"
                :auto-upload="false"
                :show-file-list="false"
                accept=".jpg,.jpeg,.png,.webp"
                @change="handleImageChange"
              >
                <el-icon class="el-icon--upload text-indigo-400"><UploadFilled /></el-icon>
                <div class="el-upload__text text-gray-600">
                  将图像拖拽到此处，或 <em class="text-indigo-500 font-bold not-italic">点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip text-gray-400 text-center mt-2">支持 JPG, PNG, WEBP，最大 5MB</div>
                </template>
              </el-upload>

              <!-- 已上传图像预览 -->
              <div v-else class="relative rounded-xl overflow-hidden border border-gray-200 group">
                <img :src="uploadedImageUrl" class="w-full h-40 object-cover" />
                <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <el-button type="danger" circle @click="removeImage">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </el-form-item>

            <!-- 4. 模型选择 -->
            <el-form-item label="生成模型">
              <el-select v-model="formData.model" size="large" class="w-full">
                <el-option label="Trellis (推荐)" value="trellis" />
                <el-option label="Point-E" value="pointe" />
                <el-option label="Shape-E" value="shapee" />
              </el-select>
            </el-form-item>

            <!-- 5. 水印信息输入 -->
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

            <!-- 6. 生成按钮 -->
            <div class="pt-4">
              <el-button 
                type="primary" 
                size="large" 
                class="w-full !h-14 !text-lg !rounded-xl shadow-lg shadow-indigo-500/30 !bg-indigo-600 hover:!bg-indigo-700 !border-none"
                :loading="isGenerating"
                @click="handleGenerate"
              >
                <el-icon class="mr-2" v-if="!isGenerating"><MagicStick /></el-icon>
                {{ isGenerating ? '正在生成点云...' : '生成点云' }}
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
              <el-progress type="dashboard" :percentage="generateProgress" color="#4f46e5" />
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
                <el-dropdown @command="handleDownload">
                  <el-button type="primary" round class="shadow-md shadow-indigo-500/20 !bg-indigo-600 !border-none">
                    <el-icon class="mr-1"><Download /></el-icon> 下载点云<el-icon class="el-icon--right"><arrow-down /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="ply">下载 .ply 格式</el-dropdown-item>
                      <el-dropdown-item command="pcd">下载 .pcd 格式</el-dropdown-item>
                      <el-dropdown-item command="xyz">下载 .xyz 格式</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
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
import { ref, computed, onMounted, onBeforeUnmount, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

// --- 表单与状态数据 ---
const formData = ref({
  inputType: 'text',
  prompt: '',
  model: 'trellis',
  watermark: ''
})
const uploadedImageUrl = ref('')
const isGenerating = ref(false)
const generateProgress = ref(0)
const result = ref(null)

// --- Three.js 相关变量 (使用 shallowRef 避免 Vue 深度响应式带来的性能问题) ---
const canvasContainer = ref(null)
const fullscreenContainer = ref(null)
const scene = shallowRef(null)
const camera = shallowRef(null)
const renderer = shallowRef(null)
const controls = shallowRef(null)
const pointsObject = shallowRef(null)
const axesHelper = shallowRef(null)
let animationFrameId = null

// --- 业务逻辑 ---

const generateRandomWatermark = () => {
  let binaryStr = ''
  for (let i = 0; i < 32; i++) binaryStr += Math.random() > 0.5 ? '1' : '0'
  formData.value.watermark = binaryStr
}

const formattedWatermark = computed(() => {
  if (!result.value || !result.value.watermark) return ''
  return result.value.watermark.replace(/(.{8})/g, '$1 ').trim()
})

const copyWatermark = async () => {
  try {
    await navigator.clipboard.writeText(result.value.watermark)
    ElMessage.success('水印已复制到剪贴板')
  } catch (err) {
    ElMessage.error('复制失败')
  }
}

const handleImageChange = (uploadFile) => {
  const file = uploadFile.raw
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('图像大小不能超过 5MB！')
    return
  }
  uploadedImageUrl.value = URL.createObjectURL(file)
}

const removeImage = () => {
  if (uploadedImageUrl.value) URL.revokeObjectURL(uploadedImageUrl.value)
  uploadedImageUrl.value = ''
}

const handleDownload = (format) => {
  ElMessage.success(`开始下载 ${format.toUpperCase()} 格式点云文件...`)
}

// --- Three.js 核心逻辑 ---

const initThree = () => {
  if (!canvasContainer.value) return

  // 1. 场景
  scene.value = new THREE.Scene()
  scene.value.background = new THREE.Color(0x1e1e1e) // 默认深色背景

  // 2. 相机
  const width = canvasContainer.value.clientWidth
  const height = canvasContainer.value.clientHeight
  camera.value = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000)
  camera.value.position.set(0, 0, 5)

  // 3. 渲染器
  renderer.value = new THREE.WebGLRenderer({ antialias: true })
  renderer.value.setSize(width, height)
  renderer.value.setPixelRatio(window.devicePixelRatio)
  canvasContainer.value.appendChild(renderer.value.domElement)

  // 4. 控制器 (OrbitControls)
  controls.value = new OrbitControls(camera.value, renderer.value.domElement)
  controls.value.enableDamping = true
  controls.value.dampingFactor = 0.05

  // 5. 坐标轴辅助
  axesHelper.value = new THREE.AxesHelper(2)
  scene.value.add(axesHelper.value)

  // 监听容器大小变化
  window.addEventListener('resize', onWindowResize)

  // 开始动画循环
  animate()
}

const animate = () => {
  animationFrameId = requestAnimationFrame(animate)
  if (controls.value) controls.value.update()
  if (renderer.value && scene.value && camera.value) {
    // 让点云缓慢自转，增加视觉效果
    if (pointsObject.value) {
      pointsObject.value.rotation.y += 0.002
    }
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

// 模拟生成一个点云模型 (球体表面随机点)
const createMockPointCloud = () => {
  if (pointsObject.value) {
    scene.value.remove(pointsObject.value)
    pointsObject.value.geometry.dispose()
    pointsObject.value.material.dispose()
  }

  const particleCount = 128000
  const geometry = new THREE.BufferGeometry()
  const positions = new Float32Array(particleCount * 3)
  const colors = new Float32Array(particleCount * 3)

  const color = new THREE.Color()

  for (let i = 0; i < particleCount; i++) {
    // 随机生成球体上的点
    const theta = Math.random() * Math.PI * 2
    const phi = Math.acos((Math.random() * 2) - 1)
    const radius = 1.5 + (Math.random() * 0.1) // 稍微有点厚度的球壳

    const x = radius * Math.sin(phi) * Math.cos(theta)
    const y = radius * Math.sin(phi) * Math.sin(theta)
    const z = radius * Math.cos(phi)

    positions[i * 3] = x
    positions[i * 3 + 1] = y
    positions[i * 3 + 2] = z

    // 深度着色：根据 Z 轴或 Y 轴赋予颜色
    color.setHSL((y / radius + 1) / 2 * 0.5 + 0.5, 0.8, 0.6)
    colors[i * 3] = color.r
    colors[i * 3 + 1] = color.g
    colors[i * 3 + 2] = color.b
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))

  const material = new THREE.PointsMaterial({
    size: 0.015,
    vertexColors: true,
    transparent: true,
    opacity: 0.8
  })

  pointsObject.value = new THREE.Points(geometry, material)
  scene.value.add(pointsObject.value)
}

// --- 工具栏操作 ---
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
    // 在深色和浅色之间切换
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
    fullscreenContainer.value?.requestFullscreen().catch(err => {
      ElMessage.error('全屏请求失败')
    })
  } else {
    document.exitFullscreen()
  }
}

// --- 模拟生成流程 ---
const handleGenerate = () => {
  if (formData.value.inputType === 'text' && !formData.value.prompt) {
    ElMessage.warning('请输入点云描述')
    return
  }
  if (formData.value.inputType === 'image' && !uploadedImageUrl.value) {
    ElMessage.warning('请上传参考图像')
    return
  }
  if (!formData.value.watermark || formData.value.watermark.length !== 32) {
    ElMessage.warning('请输入有效的 32 位二进制水印')
    return
  }

  isGenerating.value = true
  generateProgress.value = 0
  result.value = null

  // 模拟进度条
  const interval = setInterval(() => {
    generateProgress.value += Math.floor(Math.random() * 15)
    if (generateProgress.value >= 100) {
      clearInterval(interval)
      generateProgress.value = 100
      
      setTimeout(() => {
        isGenerating.value = false
        
        // 渲染点云
        if (!scene.value) initThree()
        createMockPointCloud()
        resetView()

        // 构造结果数据
        result.value = {
          pointsCount: 128000,
          watermark: formData.value.watermark,
          timeTaken: (Math.random() * 10 + 35).toFixed(1), // 35-45s
          timestamp: new Date().toLocaleString('zh-CN', { hour12: false })
        }
        ElMessage.success('点云生成并嵌入水印成功！')
      }, 500)
    }
  }, 300)
}

// --- 生命周期 ---
onMounted(() => {
  // 初始不渲染，等生成后再渲染
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onWindowResize)
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
  if (renderer.value) {
    renderer.value.dispose()
    renderer.value.forceContextLoss()
  }
  if (pointsObject.value) {
    pointsObject.value.geometry.dispose()
    pointsObject.value.material.dispose()
  }
})
</script>

<style scoped>
/* 深度定制 Element Plus 的拖拽上传组件样式 */
:deep(.custom-upload .el-upload-dragger) {
  background-color: #f8fafc;
  border: 2px dashed #cbd5e1;
  border-radius: 1rem;
  padding: 30px 20px;
  transition: all 0.3s ease;
}
:deep(.custom-upload .el-upload-dragger:hover) {
  border-color: #4f46e5;
  background-color: #eef2ff;
}

:deep(.custom-textarea .el-textarea__inner) {
  background-color: #f8fafc;
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid #e2e8f0;
  padding: 12px;
  transition: all 0.2s ease;
}
:deep(.custom-textarea .el-textarea__inner:focus) {
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
  border-color: #4f46e5;
  background-color: #ffffff;
}

/* 全屏时的背景处理 */
:fullscreen {
  background-color: #f4f6f8;
  padding: 24px;
}
</style>