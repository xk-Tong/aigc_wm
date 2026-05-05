<template>
  <div class="max-w-[1400px] mx-auto pb-8 pt-2">
    <!-- 页面标题 -->
    <div class="flex items-center gap-3 mb-6 px-2">
      <div class="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center text-indigo-600">
        <el-icon class="text-xl"><Crop /></el-icon>
      </div>
      <h2 class="text-2xl font-bold text-gray-800 tracking-tight">点云水印提取</h2>
    </div>

    <!-- 左右两栏布局 -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      
      <!-- ================= 左侧栏：点云上传区域 ================= -->
      <div class="lg:col-span-5 space-y-6">
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <div class="flex justify-between items-center mb-5">
            <h3 class="text-lg font-bold text-gray-800">点云文件上传</h3>
            <el-button v-if="uploadedFile" type="primary" link @click="removeFile">
              重新上传
            </el-button>
          </div>
          
          <!-- 拖拽上传区域 (未上传时显示) -->
          <el-upload
            v-if="!uploadedFile"
            class="custom-upload"
            drag
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            accept=".ply,.pcd,.xyz,.obj,.stl"
            @change="handleFileChange"
          >
            <el-icon class="el-icon--upload text-indigo-400"><UploadFilled /></el-icon>
            <div class="el-upload__text text-gray-600">
              将点云文件拖拽到此处，或 <em class="text-indigo-500 font-bold not-italic">点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip text-gray-400 text-center mt-3">
                支持 .ply, .pcd, .xyz, .obj, .stl 格式，最大不超过 50MB
              </div>
            </template>
          </el-upload>

          <!-- 已上传文件预览 (上传后显示) -->
          <div v-else class="bg-gray-50 rounded-2xl p-4 border border-gray-200">
            <div class="flex flex-col items-center">
              <!-- 缩略图占位 (使用 CSS 模拟 3D 效果) -->
              <div class="w-full h-[160px] rounded-xl bg-gradient-to-br from-indigo-900 to-gray-900 mb-4 flex items-center justify-center relative overflow-hidden shadow-inner">
                <div class="absolute inset-0 opacity-30" style="background-image: radial-gradient(circle, #fff 1px, transparent 1px); background-size: 10px 10px;"></div>
                <el-icon class="text-5xl text-indigo-300/80 z-10"><Location /></el-icon>
              </div>
              
              <!-- 文件信息 -->
              <div class="w-full flex items-center justify-between bg-white p-3 rounded-xl border border-gray-100 shadow-sm">
                <div class="flex items-center gap-3 overflow-hidden">
                  <div class="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-500 shrink-0">
                    <span class="text-xs font-bold">{{ fileExtension }}</span>
                  </div>
                  <div class="overflow-hidden">
                    <p class="text-sm font-bold text-gray-800 truncate" :title="fileInfo.name">{{ fileInfo.name }}</p>
                    <div class="flex items-center gap-2 text-xs text-gray-400 mt-0.5">
                      <span>{{ fileInfo.size }}</span>
                      <span class="w-1 h-1 rounded-full bg-gray-300"></span>
                      <span>约 {{ fileInfo.pointsCount }} 个点</span>
                    </div>
                  </div>
                </div>
                <el-button type="danger" plain circle size="small" @click="removeFile" class="shrink-0 ml-2">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>

          <!-- 格式说明折叠面板 -->
          <div class="mt-6">
            <el-collapse class="custom-collapse">
              <el-collapse-item title="支持的文件格式说明" name="1">
                <div class="text-xs text-gray-500 space-y-2 leading-relaxed">
                  <p><strong>.ply (Polygon File Format):</strong> 推荐格式，支持存储点坐标、颜色、法线等丰富属性。</p>
                  <p><strong>.pcd (Point Cloud Data):</strong> PCL 库官方格式，结构严谨，适合大规模点云数据。</p>
                  <p><strong>.xyz:</strong> 纯文本格式，仅包含坐标信息，体积较小但不支持颜色。</p>
                  <p><strong>.obj / .stl:</strong> 常见的网格模型格式，系统会自动提取其顶点作为点云进行处理。</p>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>
      </div>

      <!-- ================= 右侧栏：提取结果与预览区域 ================= -->
      <div class="lg:col-span-7 space-y-6">
        
        <!-- 提取按钮 -->
        <el-button 
          type="primary" 
          size="large" 
          class="w-full !h-14 !text-lg !rounded-xl shadow-lg shadow-indigo-500/30 !bg-indigo-600 hover:!bg-indigo-700 !border-none transition-all"
          :disabled="!uploadedFile"
          :loading="isExtracting"
          @click="startExtraction"
        >
          <el-icon class="mr-2" v-if="!isExtracting"><Search /></el-icon>
          {{ isExtracting ? '正在深度解析点云特征...' : '提取水印' }}
        </el-button>

        <!-- 结果展示卡片 -->
        <div 
          class="bg-white rounded-3xl p-6 shadow-sm border-2 transition-all duration-300 min-h-[220px] flex flex-col justify-center relative overflow-hidden"
          :class="resultCardClass"
        >
          <!-- 状态 1: 空白状态 -->
          <div v-if="!result && !isExtracting" class="text-center text-gray-400">
            <el-icon class="text-5xl mb-3 opacity-30"><DocumentScanner /></el-icon>
            <p class="font-medium">等待提取</p>
            <p class="text-xs mt-1 opacity-70">请先上传点云文件并点击提取按钮</p>
          </div>

          <!-- 状态 2: 提取成功 -->
          <div v-else-if="result && result.status === 'success'" class="relative z-10">
            <div class="flex items-center justify-between mb-6">
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600">
                  <el-icon><Select /></el-icon>
                </div>
                <h3 class="text-lg font-bold text-green-700">提取成功</h3>
              </div>
              <el-button size="small" round @click="copyWatermark" class="shadow-sm">
                <el-icon class="mr-1"><CopyDocument /></el-icon> 复制水印
              </el-button>
            </div>

            <div class="bg-gray-50 rounded-2xl p-5 border border-gray-100 mb-5">
              <p class="text-xs text-gray-500 mb-2 font-medium">解析到的水印内容 (易读格式)：</p>
              <p class="font-mono text-2xl text-gray-800 tracking-widest font-bold mb-3">
                {{ formattedWatermark }}
              </p>
              <p class="text-xs text-gray-400 font-mono break-all">
                原始二进制: {{ result.watermark }}
              </p>
            </div>

            <div class="flex flex-wrap items-center gap-4 text-sm text-gray-500">
              <span><el-icon class="mr-1 align-middle"><Timer /></el-icon> 提取耗时: <span class="font-bold text-gray-800">{{ result.timeTaken }}s</span></span>
              <el-divider direction="vertical" />
              <span><el-icon class="mr-1 align-middle"><DataAnalysis /></el-icon> 原始点数: <span class="font-bold text-gray-800">{{ fileInfo.pointsCount }}</span></span>
              <el-divider direction="vertical" />
              <span><el-icon class="mr-1 align-middle"><Document /></el-icon> 格式: <span class="font-bold text-gray-800">{{ fileExtension.toUpperCase() }}</span></span>
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

        <!-- 3D 预览卡片 (仅上传后显示) -->
        <div v-show="uploadedFile" class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col h-[400px]">
          <div class="flex justify-between items-center mb-4 shrink-0">
            <h3 class="text-md font-bold text-gray-800">点云 3D 预览</h3>
            <span class="text-xs text-gray-400">支持鼠标拖拽旋转、滚轮缩放</span>
          </div>
          <!-- Three.js 渲染容器 -->
          <div class="flex-1 rounded-2xl overflow-hidden relative border border-gray-100 bg-[#1e1e1e]" ref="canvasContainer">
            <!-- Canvas 将由 Three.js 挂载到这里 -->
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
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { PLYLoader } from 'three/examples/jsm/loaders/PLYLoader.js'
import { PCDLoader } from 'three/examples/jsm/loaders/PCDLoader.js'
// --- 状态数据 ---
const uploadedFile = ref(null)
const fileInfo = ref({ name: '', size: '', pointsCount: '0' })
const isExtracting = ref(false)
const result = ref(null)

// --- Three.js 相关变量 ---
const canvasContainer = ref(null)
const scene = shallowRef(null)
const camera = shallowRef(null)
const renderer = shallowRef(null)
const controls = shallowRef(null)
const pointsObject = shallowRef(null)
let animationFrameId = null
let activeLoadToken = 0

// --- 计算属性 ---
const fileExtension = computed(() => {
  if (!fileInfo.value.name) return ''
  const parts = fileInfo.value.name.split('.')
  return parts.length > 1 ? parts.pop().toLowerCase() : 'unknown'
})

const resultCardClass = computed(() => {
  if (!result.value) return 'border-gray-100'
  if (result.value.status === 'success') return 'border-green-400 bg-green-50/30'
  if (result.value.status === 'error') return 'border-red-400 bg-red-50/30'
  return 'border-gray-100'
})

const formattedWatermark = computed(() => {
  if (!result.value || !result.value.watermark) return ''
  return result.value.watermark.replace(/(.{8})/g, '$1 ').trim()
})

// --- 业务逻辑 ---

const handleFileChange = (uploadFile) => {
  const file = uploadFile.raw
  if (!file) return

  // 校验大小 (50MB)
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.error('点云文件大小不能超过 50MB！')
    return
  }

  uploadedFile.value = file
  
  // 格式化文件信息
  const sizeMB = (file.size / (1024 * 1024)).toFixed(2)
  fileInfo.value = {
    name: file.name,
    size: sizeMB > 1 ? `${sizeMB} MB` : `${(file.size / 1024).toFixed(2)} KB`,
    pointsCount: (Math.floor(Math.random() * 500000) + 50000).toLocaleString() // 模拟点数
  }
  
  result.value = null

  // 初始化 3D 预览
  nextTick(() => {
    initThree()
    // createMockPointCloud()
    loadUserPointCloud(file)
  })
}

const removeFile = () => {
  uploadedFile.value = null
  fileInfo.value = { name: '', size: '', pointsCount: '0' }
  result.value = null
  disposeThree()
}

const copyWatermark = async () => {
  try {
    await navigator.clipboard.writeText(result.value.watermark)
    ElMessage.success('水印内容已复制到剪贴板')
  } catch (err) {
    ElMessage.error('复制失败')
  }
}

const startExtraction = async () => {
  if (!uploadedFile.value) return

  isExtracting.value = true
  result.value = null

  try {
    const formData = new FormData()
    formData.append('pointcloud_file', uploadedFile.value)

    const response = await request.post('/api/v1/pointcloud/extract-watermark', formData)
    const payload = response?.data || {}
    const watermarkBits = payload.watermark_bits || payload.extracted_watermark || ''

    if (!/^[01]{32}$/.test(watermarkBits)) {
      throw new Error('算法服务返回了非法的水印数据')
    }

    isExtracting.value = false

    result.value = {
      status: 'success',
      watermark: watermarkBits,
      timeTaken: ((payload.elapsed_ms || 0) / 1000).toFixed(2),
      timestamp: payload.extracted_at
        ? new Date(payload.extracted_at).toLocaleString('zh-CN', { hour12: false })
        : new Date().toLocaleString('zh-CN', { hour12: false }),
    }
    ElMessage.success('水印提取成功！')
  } catch (err) {
    isExtracting.value = false

    result.value = {
      status: 'error',
      message: err?.response?.data?.detail || err?.message || '点云结构可能已被破坏或未包含有效的水印特征，提取失败。'
    }
    ElMessage.error(result.value.message)
  }
}

// --- Three.js 核心逻辑 ---

const initThree = () => {
  if (!canvasContainer.value) return
  disposeThree() // 清理之前的实例

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
  controls.value.autoRotate = false
  controls.value.target.set(0, 0, 0)
  // controls.value.autoRotateSpeed = 2.0

  window.addEventListener('resize', onWindowResize)
  animate()
}

const animate = () => {
  animationFrameId = requestAnimationFrame(animate)
  if (controls.value) controls.value.update()
  if (renderer.value && scene.value && camera.value) {
    // if (pointsObject.value) {
    //   pointsObject.value.rotation.y += 0.001 // 缓慢旋转
    // }
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

// 模拟生成一个点云模型 (环面/甜甜圈形状)
const createMockPointCloud = () => {
  const particleCount = 50000
  const geometry = new THREE.BufferGeometry()
  const positions = new Float32Array(particleCount * 3)
  const colors = new Float32Array(particleCount * 3)
  const color = new THREE.Color()

  for (let i = 0; i < particleCount; i++) {
    const u = Math.random() * Math.PI * 2
    const v = Math.random() * Math.PI * 2
    const R = 1.2 // 主半径
    const r = 0.4 // 管道半径

    // 增加一些随机噪声让它看起来像真实扫描的点云
    const noise = (Math.random() - 0.5) * 0.1

    const x = (R + r * Math.cos(v)) * Math.cos(u) + noise
    const y = (R + r * Math.cos(v)) * Math.sin(u) + noise
    const z = r * Math.sin(v) + noise

    positions[i * 3] = x
    positions[i * 3 + 1] = y
    positions[i * 3 + 2] = z

    // 根据位置赋予颜色
    color.setHSL((x / 3) + 0.5, 0.8, 0.6)
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
  // 调整一下初始角度
  pointsObject.value.rotation.x = Math.PI / 4
  scene.value.add(pointsObject.value)
}

// 加载用户真实上传的点云文件
const loadUserPointCloud = (file) => {
  const loadToken = ++activeLoadToken
  const url = URL.createObjectURL(file)
  const ext = file.name.split('.').pop().toLowerCase()

  // 居中并缩放的通用处理函数
  const processAndAddGeometry = (geometry) => {
    if (loadToken !== activeLoadToken || !scene.value) {
      geometry.dispose?.()
      return
    }

    if (pointsObject.value && scene.value) {
      scene.value.remove(pointsObject.value)
      disposeObject3D(pointsObject.value)
      pointsObject.value = null
    }

    geometry.computeBoundingBox()
    const box = geometry.boundingBox
    const center = box.getCenter(new THREE.Vector3())
    const size = box.getSize(new THREE.Vector3()).length()

    // 与网格页一致：基于包围盒做居中和统一缩放
    geometry.translate(-center.x, -center.y, -center.z)
    const scale = 4 / (size || 1)

    // 如果模型自带颜色则使用自带颜色，否则使用统一颜色
    const hasColor = geometry.hasAttribute('color')
    const material = new THREE.PointsMaterial({ 
      size: 0.03 / scale, // 根据缩放比例调整点的大小
      vertexColors: hasColor,
      color: hasColor ? 0xffffff : 0x4f46e5, // 没有颜色时默认用靛蓝色
      transparent: true,
      opacity: 0.8
    })

    pointsObject.value = new THREE.Points(geometry, material)
    pointsObject.value.scale.setScalar(scale)
    pointsObject.value.rotation.x = Math.PI
    scene.value.add(pointsObject.value)
  }

  if (ext === 'ply') {
    new PLYLoader().load(url, (geometry) => {
      processAndAddGeometry(geometry)
      URL.revokeObjectURL(url) // 释放内存
    }, undefined, () => {
      URL.revokeObjectURL(url)
      if (loadToken === activeLoadToken) {
        ElMessage.error('PLY 文件加载失败，请检查文件是否损坏')
      }
    })
  } else if (ext === 'pcd') {
    new PCDLoader().load(url, (points) => {
      if (loadToken !== activeLoadToken || !scene.value) {
        disposeObject3D(points)
        return
      }

      if (pointsObject.value && scene.value) {
        scene.value.remove(pointsObject.value)
        disposeObject3D(pointsObject.value)
        pointsObject.value = null
      }

      // PCDLoader 直接返回 Points 对象
      pointsObject.value = points
      const box = new THREE.Box3().setFromObject(points)
      const center = box.getCenter(new THREE.Vector3())
      const size = box.getSize(new THREE.Vector3()).length()

      points.position.sub(center)
      const scale = 4 / (size || 1)
      points.scale.setScalar(scale)
      points.rotation.x = Math.PI
      if (points.material && !Array.isArray(points.material)) {
        points.material.size = 0.03 / scale
      }
      scene.value.add(points)
      URL.revokeObjectURL(url)
    }, undefined, () => {
      URL.revokeObjectURL(url)
      if (loadToken === activeLoadToken) {
        ElMessage.error('PCD 文件加载失败，请检查文件是否损坏')
      }
    })
  } else {
    URL.revokeObjectURL(url)
    ElMessage.warning('当前预览仅支持 .ply 和 .pcd 格式，其他格式暂不渲染')
  }
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

const disposeThree = () => {
  activeLoadToken += 1

  if (animationFrameId) cancelAnimationFrame(animationFrameId)
  animationFrameId = null
  window.removeEventListener('resize', onWindowResize)

  if (controls.value) {
    controls.value.dispose()
    controls.value = null
  }
  
  if (pointsObject.value) {
    if (scene.value) scene.value.remove(pointsObject.value)
    disposeObject3D(pointsObject.value)
    pointsObject.value = null
  }
  
  if (renderer.value) {
    renderer.value.dispose()
    renderer.value.forceContextLoss()
    if (canvasContainer.value && canvasContainer.value.contains(renderer.value.domElement)) {
      canvasContainer.value.removeChild(renderer.value.domElement)
    }
    renderer.value = null
  }
  
  scene.value = null
  camera.value = null
}

onBeforeUnmount(() => {
  disposeThree()
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

/* 定制折叠面板样式，使其更清爽 */
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