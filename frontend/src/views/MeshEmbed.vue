<template>
  <div class="max-w-[1400px] mx-auto pb-8 pt-2">
    <div class="flex items-center gap-3 mb-6 px-2">
      <div class="w-10 h-10 rounded-xl bg-teal-100 flex items-center justify-center text-teal-600">
        <el-icon class="text-xl"><Box /></el-icon>
      </div>
      <h2 class="text-2xl font-bold text-gray-800 tracking-tight">网格水印嵌入</h2>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

      <!-- ================= 左侧栏：参数配置区域 ================= -->
      <div class="lg:col-span-5 space-y-6">
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <h3 class="text-lg font-bold text-gray-800 mb-5">生成参数配置</h3>

          <el-form ref="generateFormRef" label-position="top" :model="formData" :rules="formRules">

            <!-- 网格描述 -->
            <el-form-item label="网格描述 (Prompt)" prop="prompt">
              <el-input
                v-model="formData.prompt"
                type="textarea"
                :rows="4"
                maxlength="2000"
                show-word-limit
                placeholder="请输入网格模型描述，如：一个精致的青花瓷瓶..."
              />
            </el-form-item>

            <!-- 生成模型 -->
            <el-form-item label="生成模型">
              <el-select v-model="formData.model" size="large" class="w-full">
                <el-option label="Trellis (推荐)" value="trellis" />
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
                class="w-full h-14! text-lg! rounded-xl! shadow-lg shadow-teal-500/30 bg-teal-600! hover:bg-teal-700! border-none!"
                :loading="isGenerating"
                @click="handleGenerate"
              >
                <el-icon class="mr-2" v-if="!isGenerating"><MagicStick /></el-icon>
                {{ isGenerating ? '正在生成网格模型...' : '生成网格模型' }}
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
            <h3 class="text-lg font-bold text-gray-800">网格 3D 预览</h3>
            <el-button-group v-if="result">
              <el-button size="small" title="重置视角" @click="resetView"><el-icon><RefreshLeft /></el-icon></el-button>
              <el-button size="small" title="切换线框模式" @click="toggleWireframe"><el-icon><Grid /></el-icon></el-button>
              <el-button size="small" title="全屏预览" @click="toggleFullscreen"><el-icon><FullScreen /></el-icon></el-button>
            </el-button-group>
          </div>

          <div class="flex-1 rounded-2xl overflow-hidden relative border border-gray-100 bg-[#1e1e1e]" ref="canvasContainer">
            <div v-if="!result && !isGenerating" class="absolute inset-0 flex flex-col items-center justify-center text-gray-400 bg-[#f8fafc] z-10">
              <el-icon class="text-5xl mb-2 opacity-50"><Box /></el-icon>
              <p>等待生成</p>
            </div>
            <div v-else-if="isGenerating" class="absolute inset-0 flex flex-col items-center justify-center bg-[#f8fafc]/90 backdrop-blur-sm z-10">
              <el-icon class="text-4xl text-teal-500 mb-3 animate-spin"><Loading /></el-icon>
              <p class="text-sm font-medium text-teal-600">正在构建 3D 网格并嵌入水印...</p>
            </div>
          </div>
        </div>

        <!-- 生成结果信息 -->
        <transition name="el-fade-in-linear">
          <div v-if="result" class="space-y-6">

            <!-- 模型信息行 & 操作按钮 -->
            <div class="flex flex-wrap items-center justify-between bg-white rounded-2xl p-4 shadow-sm border border-gray-100 gap-4">
              <div class="flex items-center gap-4 text-sm text-gray-600 font-medium ml-2">
                <span><el-icon class="mr-1 align-middle"><DataAnalysis /></el-icon> 面片数: <span class="text-gray-800 font-bold">{{ (result.facesCount || 0).toLocaleString() }}</span></span>
                <el-divider direction="vertical" />
                <span><el-icon class="mr-1 align-middle"><Timer /></el-icon> 耗时: <span class="text-gray-800 font-bold">{{ result.timeTaken }}s</span></span>
              </div>

              <div class="flex gap-3">
                <el-button plain round @click="handleGenerate">重新生成</el-button>
                <el-button type="primary" round class="shadow-md shadow-teal-500/20 bg-teal-600! border-none!" @click="handleDownload">
                  <el-icon class="mr-1"><Download /></el-icon> 下载模型
                </el-button>
              </div>
            </div>

            <!-- 水印信息卡片 -->
            <div class="bg-teal-50/50 rounded-3xl p-6 border border-teal-100 relative overflow-hidden">
              <div class="absolute top-0 right-0 w-32 h-32 bg-teal-500/5 rounded-full blur-2xl -mr-10 -mt-10"></div>

              <h4 class="text-sm font-bold text-teal-800 mb-4 flex items-center">
                <el-icon class="mr-2 text-lg"><Key /></el-icon> 已嵌入水印信息
              </h4>

              <div class="bg-white rounded-xl p-4 border border-teal-100/50 flex justify-between items-center shadow-sm mb-4">
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
      theme-color="teal"
      subtitle="最近 5 条网格生成记录"
    />
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, onMounted, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'
import RecentRecords from '../components/RecentRecords.vue'
import * as THREE from 'three'
import { TrackballControls } from 'three/examples/jsm/controls/TrackballControls.js'
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

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
    { required: true, message: '请输入网格模型描述', trigger: 'blur' },
    { min: 1, max: 2000, message: '描述长度需在 1-2000 字符之间', trigger: 'blur' },
  ],
  watermark: [
    { required: true, message: '请输入 8 位十六进制水印', trigger: 'blur' },
    { pattern: /^[0-9A-Fa-f]{8}$/, message: '请输入有效的 8 位十六进制水印', trigger: 'blur' },
  ],
}

const isGenerating = ref(false)
const result = ref(null)

// ==================== Three.js ====================

const canvasContainer = ref(null)
const scene = shallowRef(null)
const camera = shallowRef(null)
const renderer = shallowRef(null)
const controls = shallowRef(null)
const meshObject = shallowRef(null)
let animationFrameId = null

const initThree = () => {
  if (!canvasContainer.value) return

  scene.value = new THREE.Scene()
  scene.value.background = new THREE.Color(0x1e1e1e)

  const width = canvasContainer.value.clientWidth
  const height = canvasContainer.value.clientHeight
  camera.value = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000)
  camera.value.position.set(0, 0, 6)

  renderer.value = new THREE.WebGLRenderer({ antialias: true })
  renderer.value.setSize(width, height)
  renderer.value.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  canvasContainer.value.appendChild(renderer.value.domElement)

  controls.value = new TrackballControls(camera.value, renderer.value.domElement)
  controls.value.rotateSpeed = 3.0
  controls.value.zoomSpeed = 1.2
  controls.value.panSpeed = 0.8
  controls.value.dynamicDampingFactor = 0.15
  controls.value.minDistance = 0.5
  controls.value.maxDistance = 50

  scene.value.add(new THREE.AmbientLight(0xffffff, 0.6))
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8)
  dirLight.position.set(5, 5, 5)
  scene.value.add(dirLight)

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
  camera.value.aspect = canvasContainer.value.clientWidth / canvasContainer.value.clientHeight
  camera.value.updateProjectionMatrix()
  renderer.value.setSize(canvasContainer.value.clientWidth, canvasContainer.value.clientHeight)
  if (controls.value) controls.value.handleResize()
}

// ==================== 3D 对象辅助函数 ====================

const disposeMaterial = (material) => {
  if (!material) return
  if (Array.isArray(material)) {
    material.forEach((item) => item?.dispose?.())
    return
  }
  material.dispose?.()
}

const disposeObject3D = (object) => {
  object.traverse((child) => {
    if (child.isMesh || child.isPoints || child.isLine) {
      child.geometry?.dispose?.()
      disposeMaterial(child.material)
    }
  })
}

const calculateFaces = (geometry) => {
  if (geometry.index) return geometry.index.count / 3
  if (geometry.attributes.position) return geometry.attributes.position.count / 3
  return 0
}

const processAndAddObject = (object) => {
  if (!scene.value) return

  if (meshObject.value) {
    scene.value.remove(meshObject.value)
    disposeObject3D(meshObject.value)
    meshObject.value = null
  }

  const box = new THREE.Box3().setFromObject(object)
  const center = box.getCenter(new THREE.Vector3())
  const size = box.getSize(new THREE.Vector3()).length()
  object.position.sub(center)
  const scale = 4 / (size || 1)
  object.scale.setScalar(scale)

  const group = new THREE.Group()
  group.add(object)
  meshObject.value = group
  scene.value.add(meshObject.value)

  let totalFaces = 0
  object.traverse((child) => {
    if (child.isMesh) totalFaces += calculateFaces(child.geometry)
  })
  if (result.value) result.value.facesCount = Math.round(totalFaces)
}

const loadMeshFromUrl = (url, fileFormat) => {
  if (!scene.value) return

  const defaultMaterial = new THREE.MeshStandardMaterial({
    color: 0x0d9488,
    roughness: 0.4,
    metalness: 0.1,
    side: THREE.DoubleSide,
  })

  const onError = () => ElMessage.error('模型加载失败')

  if (fileFormat === 'stl') {
    new STLLoader().load(url, (geometry) => {
      const mesh = new THREE.Mesh(geometry, defaultMaterial)
      processAndAddObject(mesh)
    }, undefined, onError)
  } else if (fileFormat === 'gltf' || fileFormat === 'glb') {
    new GLTFLoader().load(url, (gltf) => {
      gltf.scene.traverse((child) => {
        if (child.isMesh && (!child.material || child.material === undefined)) {
          child.material = defaultMaterial
        }
      })
      processAndAddObject(gltf.scene)
    }, undefined, onError)
  } else {
    // 默认 obj
    new OBJLoader().load(url, (group) => {
      group.traverse((child) => {
        if (child.isMesh) child.material = defaultMaterial
      })
      processAndAddObject(group)
    }, undefined, onError)
  }
}

// ==================== 交互操作 ====================

const resetView = () => {
  if (camera.value && controls.value) {
    camera.value.position.set(0, 0, 6)
    camera.value.up.set(0, 1, 0)
    controls.value.target.set(0, 0, 0)
    controls.value.reset()
  }
}

const toggleWireframe = () => {
  if (meshObject.value) {
    meshObject.value.traverse((child) => {
      if (child.isMesh && child.material) {
        child.material.wireframe = !child.material.wireframe
      }
    })
  }
}

const toggleFullscreen = () => {
  const el = canvasContainer.value
  if (!el) return
  if (!document.fullscreenElement) {
    el.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

// ==================== 水印与生成 ====================

const hexToBinary = (hex) => parseInt(hex, 16).toString(2).padStart(32, '0')
const binaryToHex = (binary) => parseInt(binary, 2).toString(16).toUpperCase().padStart(8, '0')

const generateRandomWatermark = () => {
  const hexChars = '0123456789ABCDEF'
  let hexStr = ''
  for (let i = 0; i < 8; i++) hexStr += hexChars[Math.floor(Math.random() * 16)]
  formData.value.watermark = hexStr
}

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
      params: { media_type: 'mesh', operation_type: 'embed', size: 5, page: 1 }
    })
    if (res?.data?.code === 200) {
      recentRecords.value = res.data.data.items
    }
  } catch { /* ignore */ }
}

const handleDownload = () => {
  if (!result.value?.downloadUrl) {
    ElMessage.warning('暂无可下载的网格文件')
    return
  }
  window.open(result.value.downloadUrl, '_blank', 'noopener,noreferrer')
}

const handleGenerate = async () => {
  try {
    await generateFormRef.value.validate()
  } catch {
    ElMessage.warning('请先修正参数输入后再生成网格模型')
    return
  }

  isGenerating.value = true
  result.value = null

  try {
    const response = await request.post('/api/v1/mesh/generate-watermarked', {
      prompt: formData.value.prompt,
      model: formData.value.model,
      watermark_bits: hexToBinary(formData.value.watermark),
      seed: formData.value.seed,
    }, { timeout: 200000 })

    const payload = response?.data || {}
    isGenerating.value = false

    if (!scene.value) initThree()
    loadMeshFromUrl(payload.mesh_url, payload.file_format || 'obj')
    resetView()

    const generatedAt = payload.generated_at ? new Date(payload.generated_at) : new Date()
    result.value = {
      facesCount: 0,
      watermark: payload.watermark_bits ? binaryToHex(payload.watermark_bits) : formData.value.watermark,
      timeTaken: ((payload.elapsed_ms || 0) / 1000).toFixed(1),
      timestamp: generatedAt.toLocaleString('zh-CN', { hour12: false }),
      downloadUrl: payload.download_url || payload.mesh_url,
    }

    ElMessage.success('网格模型生成并嵌入水印成功！')
    fetchRecentRecords()
  } catch (err) {
    isGenerating.value = false
    const message = err?.response?.data?.detail || err?.message || '网格模型生成失败，请稍后重试'
    ElMessage.error(message)
  }
}

// ==================== 生命周期清理 ====================

onMounted(() => fetchRecentRecords())

onBeforeUnmount(() => {
  window.removeEventListener('resize', onWindowResize)
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
  if (meshObject.value) {
    if (scene.value) scene.value.remove(meshObject.value)
    disposeObject3D(meshObject.value)
  }
  if (renderer.value) {
    renderer.value.dispose()
    renderer.value.forceContextLoss?.()
  }
  if (controls.value) controls.value.dispose()
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
  border-color: #0d9488;
  background-color: #f0fdfa;
}
</style>
