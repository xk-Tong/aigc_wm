<template>
  <div class="max-w-[1400px] mx-auto pb-8 pt-2">
    <div class="flex items-center gap-3 mb-6 px-2">
      <div class="w-10 h-10 rounded-xl bg-teal-100 flex items-center justify-center text-teal-600">
        <el-icon class="text-xl"><Crop /></el-icon>
      </div>
      <h2 class="text-2xl font-bold text-gray-800 tracking-tight">网格水印提取</h2>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

      <!-- ================= 左侧栏：网格上传区域 ================= -->
      <div class="lg:col-span-5 space-y-6">
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <div class="flex justify-between items-center mb-5">
            <h3 class="text-lg font-bold text-gray-800">网格模型上传</h3>
            <el-button v-if="uploadedFile" type="primary" link @click="removeFile">重新上传</el-button>
          </div>

          <el-upload
            v-if="!uploadedFile"
            class="custom-upload"
            drag
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            accept=".obj,.stl,.gltf,.glb"
            @change="handleFileChange"
          >
            <el-icon class="el-icon--upload text-teal-400"><UploadFilled /></el-icon>
            <div class="el-upload__text text-gray-600">将网格文件拖拽到此处，或 <em class="text-teal-500 font-bold not-italic">点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip text-gray-400 text-center mt-3">支持 .obj, .stl, .gltf, .glb 格式，最大不超过 100MB</div>
            </template>
          </el-upload>

          <div v-else class="bg-gray-50 rounded-2xl p-4 border border-gray-200">
            <div class="flex flex-col items-center">
              <!-- <div class="w-full h-[160px] rounded-xl bg-linear-to-br from-teal-900 to-gray-900 mb-4 flex items-center justify-center relative overflow-hidden shadow-inner">
                <div class="absolute inset-0 opacity-20" style="background-image: linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px); background-size: 20px 20px;"></div>
                <el-icon class="text-5xl text-teal-300/80 z-10"><Box /></el-icon>
              </div> -->

              <div class="w-full flex items-center justify-between bg-white p-3 rounded-xl border border-gray-100 shadow-sm">
                <div class="flex items-center gap-3 overflow-hidden">
                  <div class="w-10 h-10 rounded-lg bg-teal-50 flex items-center justify-center text-teal-500 shrink-0">
                    <span class="text-xs font-bold">{{ fileExtension }}</span>
                  </div>
                  <div class="overflow-hidden">
                    <p class="text-sm font-bold text-gray-800 truncate" :title="fileInfo.name">{{ fileInfo.name }}</p>
                    <div class="flex items-center gap-2 text-xs text-gray-400 mt-0.5">
                      <span>{{ fileInfo.size }}</span>
                      <span class="w-1 h-1 rounded-full bg-gray-300"></span>
                      <span>约 {{ fileInfo.facesCount }} 个面</span>
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
                  <p><strong>.obj:</strong> 最通用的 3D 模型格式，支持几何体和简单的材质信息。</p>
                  <p><strong>.stl:</strong> 常用于 3D 打印，仅包含表面几何信息（三角面片）。</p>
                  <p><strong>.gltf / .glb:</strong> 现代 Web 3D 标准格式，体积小，支持完整的场景、材质和动画。</p>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>
      </div>

      <!-- ================= 右侧栏：提取结果与 3D 预览 ================= -->
      <div class="lg:col-span-7 space-y-6">
        <el-button
          type="primary" size="large" class="w-full h-14! text-lg! rounded-xl! shadow-lg shadow-teal-500/30 bg-teal-600! hover:bg-teal-700! border-none! transition-all"
          :disabled="!uploadedFile" :loading="isExtracting" @click="startExtraction"
        >
          <el-icon class="mr-2" v-if="!isExtracting"><Search /></el-icon>
          {{ isExtracting ? '正在解析网格拓扑特征...' : '提取水印' }}
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
              <span><el-icon class="mr-1 align-middle"><DataAnalysis /></el-icon> 面片数: <span class="font-bold text-gray-800">{{ fileInfo.facesCount }}</span></span>
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
            <h3 class="text-md font-bold text-gray-800">网格 3D 预览</h3>
            <el-button size="small" @click="toggleWireframe"><el-icon><Grid /></el-icon> 切换线框</el-button>
          </div>
          <div class="flex-1 rounded-2xl overflow-hidden relative border border-gray-100 bg-[#1e1e1e]" ref="canvasContainer"></div>
        </div>
      </div>
    </div>

    <!-- 近期记录面板 -->
    <RecentRecords
      :records="recentRecords"
      operation-type="extract"
      theme-color="teal"
      subtitle="最近 5 条网格提取记录"
    />
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, onMounted, shallowRef, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'
import RecentRecords from '../components/RecentRecords.vue'

// ==================== Three.js 动态加载（避免顶层 import 阻塞路由切换） ====================

let _THREE = null
let _TrackballControls = null
let _OBJLoader = null
let _STLLoader = null
let _GLTFLoader = null

const ensureThreeLoaded = async () => {
  if (!_THREE) {
    const [THREE, controlsMod, objMod, stlMod, gltfMod] = await Promise.all([
      import('three'),
      import('three/examples/jsm/controls/TrackballControls.js'),
      import('three/examples/jsm/loaders/OBJLoader.js'),
      import('three/examples/jsm/loaders/STLLoader.js'),
      import('three/examples/jsm/loaders/GLTFLoader.js'),
    ])
    _THREE = THREE
    _TrackballControls = controlsMod.TrackballControls
    _OBJLoader = objMod.OBJLoader
    _STLLoader = stlMod.STLLoader
    _GLTFLoader = gltfMod.GLTFLoader
  }
  return { THREE: _THREE, TrackballControls: _TrackballControls, OBJLoader: _OBJLoader, STLLoader: _STLLoader, GLTFLoader: _GLTFLoader }
}

// ==================== 响应式状态 ====================

const uploadedFile = ref(null)
const fileInfo = ref({ name: '', size: '', facesCount: '0' })
const isExtracting = ref(false)
const result = ref(null)

// ==================== Three.js ====================

const canvasContainer = ref(null)
const scene = shallowRef(null)
const camera = shallowRef(null)
const renderer = shallowRef(null)
const controls = shallowRef(null)
const meshObject = shallowRef(null)
let animationFrameId = null
let activeLoadToken = 0

// ==================== 计算属性 ====================

const fileExtension = computed(() => fileInfo.value.name ? fileInfo.value.name.split('.').pop().toLowerCase() : '')

const resultCardClass = computed(() => {
  if (!result.value) return 'border-gray-100'
  return result.value.status === 'success' ? 'border-green-400 bg-green-50/30' : 'border-red-400 bg-red-50/30'
})

// ==================== 文件处理 ====================

const handleFileChange = async (uploadFile) => {
  const file = uploadFile.raw
  if (!file) return

  if (file.size > 100 * 1024 * 1024) {
    ElMessage.error('网格文件大小不能超过 100MB！')
    return
  }

  uploadedFile.value = file

  const sizeMB = (file.size / (1024 * 1024)).toFixed(2)
  fileInfo.value = {
    name: file.name,
    size: sizeMB > 1 ? `${sizeMB} MB` : `${(file.size / 1024).toFixed(2)} KB`,
    facesCount: '计算中...'
  }

  result.value = null

  await nextTick()
  await initThree()
  loadUserMesh(file)
}

const removeFile = () => {
  uploadedFile.value = null
  result.value = null
  disposeThree()
}

// ==================== 水印提取 ====================

const binaryToHex = (binary) => parseInt(binary, 2).toString(16).toUpperCase().padStart(8, '0')

const copyWatermark = async () => {
  await navigator.clipboard.writeText(result.value.watermark)
  ElMessage.success('水印内容已复制')
}

// 近期记录
const recentRecords = ref([])

const fetchRecentRecords = async () => {
  try {
    const res = await request.get('/api/v1/records', {
      params: { media_type: 'mesh', operation_type: 'extract', size: 5, page: 1 }
    })
    if (res?.data?.code === 200) {
      recentRecords.value = res.data.data.items
    }
  } catch { /* ignore */ }
}

const startExtraction = async () => {
  if (!uploadedFile.value) return

  isExtracting.value = true
  result.value = null

  try {
    const formData = new FormData()
    formData.append('mesh_file', uploadedFile.value)

    const response = await request.post('/api/v1/mesh/extract-watermark', formData)
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
    fetchRecentRecords()
  } catch (err) {
    isExtracting.value = false
    const message = err?.response?.data?.detail || err?.message || '网格结构可能已被破坏或未包含有效的水印特征，提取失败。'
    result.value = { status: 'error', message }
    ElMessage.error(message)
  }
}

// ==================== Three.js 渲染逻辑 ====================

const calculateFaces = (geometry) => {
  if (geometry.index) return geometry.index.count / 3
  if (geometry.attributes.position) return geometry.attributes.position.count / 3
  return 0
}

const initThree = async () => {
  if (!canvasContainer.value) return

  const { THREE, TrackballControls } = await ensureThreeLoaded()

  // 先同步停掉旧的渲染循环，避免 CPU/GPU 叠加，并清理旧 DOM
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }
  window.removeEventListener('resize', onWindowResize)
  if (controls.value) {
    controls.value.dispose()
    controls.value = null
  }
  if (renderer.value) {
    renderer.value.dispose()
    if (canvasContainer.value) canvasContainer.value.innerHTML = ''
    renderer.value = null
  }
  scene.value = null
  camera.value = null

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

const processAndAddObject = (object) => {
  if (!scene.value || !_THREE) return

  const THREE = _THREE

  if (meshObject.value && scene.value) {
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
}

const loadUserMesh = (file) => {
  if (!_THREE) return

  const THREE = _THREE
  const loadToken = ++activeLoadToken
  const url = URL.createObjectURL(file)
  const ext = file.name.split('.').pop().toLowerCase()

  const defaultMaterial = new THREE.MeshStandardMaterial({
    color: 0x0d9488,
    roughness: 0.4,
    metalness: 0.1,
    side: THREE.DoubleSide,
  })

  const onDone = () => URL.revokeObjectURL(url)

  if (ext === 'obj') {
    new _OBJLoader().load(url, (group) => {
      let totalFaces = 0
      group.traverse((child) => {
        if (child.isMesh) {
          child.material = defaultMaterial
          totalFaces += calculateFaces(child.geometry)
        }
      })
      if (loadToken === activeLoadToken) {
        fileInfo.value.facesCount = totalFaces.toLocaleString()
        processAndAddObject(group)
      }
      onDone()
    }, undefined, () => {
      onDone()
      if (loadToken === activeLoadToken) ElMessage.error('OBJ 文件加载失败，请检查文件是否损坏')
    })
  } else if (ext === 'stl') {
    new _STLLoader().load(url, (geometry) => {
      if (loadToken === activeLoadToken) {
        fileInfo.value.facesCount = calculateFaces(geometry).toLocaleString()
        processAndAddObject(new THREE.Mesh(geometry, defaultMaterial))
      }
      onDone()
    }, undefined, () => {
      onDone()
      if (loadToken === activeLoadToken) ElMessage.error('STL 文件加载失败，请检查文件是否损坏')
    })
  } else if (ext === 'gltf' || ext === 'glb') {
    new _GLTFLoader().load(url, (gltf) => {
      let totalFaces = 0
      gltf.scene.traverse((child) => {
        if (child.isMesh) {
          child.material = defaultMaterial
          totalFaces += calculateFaces(child.geometry)
        }
      })
      if (loadToken === activeLoadToken) {
        fileInfo.value.facesCount = totalFaces.toLocaleString()
        processAndAddObject(gltf.scene)
      }
      onDone()
    }, undefined, () => {
      onDone()
      if (loadToken === activeLoadToken) ElMessage.error('GLTF/GLB 文件加载失败，请检查文件是否损坏')
    })
  } else {
    onDone()
    ElMessage.warning('当前预览仅支持 .obj, .stl, .gltf, .glb 格式')
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

const disposeThree = () => {
  activeLoadToken += 1
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }
  window.removeEventListener('resize', onWindowResize)

  if (controls.value) {
    controls.value.dispose()
    controls.value = null
  }

  if (meshObject.value) {
    if (scene.value) scene.value.remove(meshObject.value)
    disposeObject3D(meshObject.value)
    meshObject.value = null
  }

  // GPU 资源释放延迟执行，不阻塞当前操作
  const r = renderer.value
  renderer.value = null
  scene.value = null
  camera.value = null
  if (r) {
    if (canvasContainer.value) canvasContainer.value.innerHTML = ''
    const doCleanup = () => {
      r.dispose()
      r.forceContextLoss?.()
    }
    if (typeof requestIdleCallback !== 'undefined') {
      requestIdleCallback(doCleanup, { timeout: 1000 })
    } else {
      setTimeout(doCleanup, 50)
    }
  }
}

onBeforeUnmount(() => disposeThree())

onMounted(() => fetchRecentRecords())
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
  border-color: #0d9488;
  background-color: #f0fdfa;
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
