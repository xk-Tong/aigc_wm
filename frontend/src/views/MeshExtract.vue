<template>
  <div class="max-w-[1400px] mx-auto pb-8 pt-2">
    <!-- 页面标题区域：包含图标和标题文字 -->
    <div class="flex items-center gap-3 mb-6 px-2">
      <div class="w-10 h-10 rounded-xl bg-teal-100 flex items-center justify-center text-teal-600">
        <el-icon class="text-xl"><Crop /></el-icon>
      </div>
      <h2 class="text-2xl font-bold text-gray-800 tracking-tight">网格水印提取</h2>
    </div>

    <!-- 左右两栏布局：左侧上传 + 右侧结果预览 -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

      <!-- ================= 左侧栏：网格上传区域 ================= -->
      <div class="lg:col-span-5 space-y-6">
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <!-- 标题栏：包含主标题和重新上传按钮 -->
          <div class="flex justify-between items-center mb-5">
            <h3 class="text-lg font-bold text-gray-800">网格模型上传</h3>
            <!-- 仅在已上传文件时显示重新上传按钮 -->
            <el-button v-if="uploadedFile" type="primary" link @click="removeFile">重新上传</el-button>
          </div>

          <!-- 文件上传组件：拖拽上传区域 -->
          <!-- v-if="!uploadedFile" 控制：已上传时隐藏上传框，显示文件信息卡片 -->
          <el-upload
            v-if="!uploadedFile"
            class="custom-upload"
            drag
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            accept=".obj,.stl,.gltf,.glb,.fbx"
            @change="handleFileChange"
          >
            <el-icon class="el-icon--upload text-teal-400"><UploadFilled /></el-icon>
            <div class="el-upload__text text-gray-600">将网格文件拖拽到此处，或 <em class="text-teal-500 font-bold not-italic">点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip text-gray-400 text-center mt-3">支持 .obj, .stl, .gltf, .fbx 格式，最大不超过 100MB</div>
            </template>
          </el-upload>

          <!-- 已上传文件的预览卡片：显示文件缩略图和信息 -->
          <div v-else class="bg-gray-50 rounded-2xl p-4 border border-gray-200">
            <div class="flex flex-col items-center">
              <!-- 文件预览区域：深色背景搭配网格图案 -->
              <div class="w-full h-[160px] rounded-xl bg-linear-to-br from-teal-900 to-gray-900 mb-4 flex items-center justify-center relative overflow-hidden shadow-inner">
                <!-- 网格背景图案：增加科技感 -->
                <div class="absolute inset-0 opacity-20" style="background-image: linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px); background-size: 20px 20px;"></div>
                <!-- 3D 盒子图标 -->
                <el-icon class="text-5xl text-teal-300/80 z-10"><Box /></el-icon>
              </div>

              <!-- 文件信息行：图标 + 文件名 + 文件大小 + 面片数 -->
              <div class="w-full flex items-center justify-between bg-white p-3 rounded-xl border border-gray-100 shadow-sm">
                <div class="flex items-center gap-3 overflow-hidden">
                  <!-- 文件类型标签（如 OBJ、STL） -->
                  <div class="w-10 h-10 rounded-lg bg-teal-50 flex items-center justify-center text-teal-500 shrink-0">
                    <span class="text-xs font-bold">{{ fileExtension }}</span>
                  </div>
                  <!-- 文件详情：名称、大小、面片数估计 -->
                  <div class="overflow-hidden">
                    <p class="text-sm font-bold text-gray-800 truncate" :title="fileInfo.name">{{ fileInfo.name }}</p>
                    <div class="flex items-center gap-2 text-xs text-gray-400 mt-0.5">
                      <span>{{ fileInfo.size }}</span>
                      <span class="w-1 h-1 rounded-full bg-gray-300"></span>
                      <span>约 {{ fileInfo.facesCount }} 个面</span>
                    </div>
                  </div>
                </div>
                <!-- 删除按钮：圆形危险按钮 -->
                <el-button type="danger" plain circle size="small" @click="removeFile" class="shrink-0 ml-2"><el-icon><Delete /></el-icon></el-button>
              </div>
            </div>
          </div>

          <!-- 支持格式说明：可折叠面板 -->
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
        <!-- 提取按钮：主操作按钮，禁用状态取决于是否已上传文件 -->
        <el-button
          type="primary" size="large" class="w-full h-14! text-lg! rounded-xl! shadow-lg shadow-teal-500/30 bg-teal-600! hover:bg-teal-700! border-none! transition-all"
          :disabled="!uploadedFile" :loading="isExtracting" @click="startExtraction"
        >
          <el-icon class="mr-2" v-if="!isExtracting"><Search /></el-icon>
          {{ isExtracting ? '正在解析网格拓扑特征...' : '提取水印' }}
        </el-button>

        <!-- 结果展示卡片：根据提取状态显示不同内容 -->
        <!-- 状态 1: 空白状态 - 等待提取 -->
        <!-- 状态 2: 成功状态 - 显示水印信息 -->
        <!-- 状态 3: 失败状态 - 显示错误信息 -->
        <div class="bg-white rounded-3xl p-6 shadow-sm border-2 transition-all duration-300 min-h-[220px] flex flex-col justify-center relative overflow-hidden" :class="resultCardClass">
          <!-- 空白状态：未提取时显示 -->
          <div v-if="!result && !isExtracting" class="text-center text-gray-400">
            <el-icon class="text-5xl mb-3 opacity-30"><DocumentScanner /></el-icon>
            <p class="font-medium">等待提取</p>
          </div>

          <!-- 成功状态：成功提取到水印 -->
          <div v-else-if="result && result.status === 'success'" class="relative z-10">
            <!-- 状态头部：成功图标 + 标题 + 复制按钮 -->
            <div class="flex items-center justify-between mb-6">
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600"><el-icon><Select /></el-icon></div>
                <h3 class="text-lg font-bold text-green-700">提取成功</h3>
              </div>
              <el-button size="small" round @click="copyWatermark"><el-icon class="mr-1"><CopyDocument /></el-icon> 复制水印</el-button>
            </div>
            <!-- 水印信息卡片：二进制水印内容 -->
            <div class="bg-gray-50 rounded-2xl p-5 border border-gray-100 mb-5">
              <p class="text-xs text-gray-500 mb-2 font-medium">解析到的水印内容 (易读格式)：</p>
              <p class="font-mono text-2xl text-gray-800 tracking-widest font-bold mb-3">{{ formattedWatermark }}</p>
              <p class="text-xs text-gray-400 font-mono break-all">原始二进制: {{ result.watermark }}</p>
            </div>
            <!-- 统计信息：提取耗时、面片数 -->
            <div class="flex flex-wrap items-center gap-4 text-sm text-gray-500">
              <span><el-icon class="mr-1 align-middle"><Timer /></el-icon> 提取耗时: <span class="font-bold text-gray-800">{{ result.timeTaken }}s</span></span>
              <el-divider direction="vertical" />
              <span><el-icon class="mr-1 align-middle"><DataAnalysis /></el-icon> 面片数: <span class="font-bold text-gray-800">{{ fileInfo.facesCount }}</span></span>
            </div>
          </div>

          <!-- 失败状态：提取失败时显示 -->
          <div v-else-if="result && result.status === 'error'" class="text-center relative z-10">
            <div class="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center text-red-500 mx-auto mb-4"><el-icon class="text-3xl"><WarningFilled /></el-icon></div>
            <h3 class="text-lg font-bold text-red-600 mb-2">提取失败</h3>
            <p class="text-sm text-gray-600">{{ result.message }}</p>
          </div>
          <!-- 成功状态时的装饰性背景模糊效果 -->
          <div v-if="result && result.status === 'success'" class="absolute -right-10 -bottom-10 w-40 h-40 bg-green-400/10 rounded-full blur-3xl pointer-events-none"></div>
        </div>

        <!-- 3D 预览卡片：上传文件后显示，用于可视化网格模型 -->
        <div v-show="uploadedFile" class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col h-[400px]">
          <!-- 预览卡片标题栏 -->
          <div class="flex justify-between items-center mb-4 shrink-0">
            <h3 class="text-md font-bold text-gray-800">网格 3D 预览</h3>
            <el-button size="small" @click="toggleWireframe"><el-icon><Grid /></el-icon> 切换线框</el-button>
          </div>
          <!-- Three.js 渲染容器：实际绘制 3D 网格的位置 -->
          <div class="flex-1 rounded-2xl overflow-hidden relative border border-gray-100 bg-[#1e1e1e]" ref="canvasContainer"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 网格水印提取页面
 *
 * 功能说明：
 * 1. 用户上传 3D 网格模型文件（OBJ/STL/GLTF 等格式）
 * 2. 系统分析网格的拓扑结构，提取可能嵌入的水印信息
 * 3. 在右侧区域实时预览上传的 3D 模型
 *
 * 技术栈：
 * - Vue 3 Composition API (setup 语法糖)
 * - Element Plus UI 组件库
 * - Three.js 3D 渲染引擎
 */

import { ref, computed, onBeforeUnmount, shallowRef, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
// ==================== 响应式状态变量 ====================

/** 已上传的文件对象（Element Plus UploadFile 类型） */
const uploadedFile = ref(null)

/** 文件信息：包含文件名、文件大小、估计面片数 */
const fileInfo = ref({ name: '', size: '', facesCount: '0' })

/** 是否正在执行提取操作（控制按钮 loading 状态） */
const isExtracting = ref(false)

/** 提取结果：包含 status('success'|'error')、watermark、timeTaken 等字段 */
const result = ref(null)

// ==================== Three.js 3D 渲染相关变量 ====================

/** Three.js 渲染容器的 DOM 引用 */
const canvasContainer = ref(null)

/** Three.js 场景对象：包含所有 3D 对象、光源等 */
const scene = shallowRef(null)

/** Three.js 透视相机：决定观察角度和视野范围 */
const camera = shallowRef(null)

/** Three.js WebGL 渲染器：负责将场景渲染到画布 */
const renderer = shallowRef(null)

/** Three.js 轨道控制器：支持鼠标拖拽旋转、滚轮缩放等交互 */
const controls = shallowRef(null)

/** 当前显示的网格 3D 对象 */
const meshObject = shallowRef(null)

/** requestAnimationFrame 返回的动画帧 ID，用于组件卸载时取消动画 */
let animationFrameId = null

// ==================== 计算属性 ====================

/**
 * 从文件名中提取扩展名
 * 例如：'model.obj' -> 'obj'
 */
const fileExtension = computed(() => fileInfo.value.name ? fileInfo.value.name.split('.').pop().toLowerCase() : '')

/**
 * 根据提取结果状态动态计算卡片样式类
 * - 空白状态：灰色边框
 * - 成功状态：绿色边框 + 浅绿背景
 * - 失败状态：红色边框 + 浅红背景
 */
const resultCardClass = computed(() => {
  if (!result.value) return 'border-gray-100'
  return result.value.status === 'success' ? 'border-green-400 bg-green-50/30' : 'border-red-400 bg-red-50/30'
})

/**
 * 格式化水印二进制字符串：每 8 位插入一个空格，提高可读性
 * 例如：'1010101010101010' -> '10101010 10101010'
 */
const formattedWatermark = computed(() => result.value?.watermark ? result.value.watermark.replace(/(.{8})/g, '$1 ').trim() : '')

// ==================== 文件处理函数 ====================

/**
 * 处理文件上传事件
 * 1. 保存文件对象
 * 2. 解析文件信息（大小、名称、面片数估计）
 * 3. 初始化 Three.js 场景并渲染模型
 *
 * @param {Object} uploadFile - Element Plus 上传组件的 file 对象
 */
const handleFileChange = (uploadFile) => {
  uploadedFile.value = uploadFile.raw

  // 计算文件大小，支持 MB 和 KB 两种单位
  const sizeMB = (uploadFile.raw.size / (1024 * 1024)).toFixed(2)
  fileInfo.value = {
    name: uploadFile.raw.name,
    size: sizeMB > 1 ? `${sizeMB} MB` : `${(uploadFile.raw.size / 1024).toFixed(2)} KB`,
    // 模拟面片数：实际项目中应从文件解析得出
    facesCount: (Math.floor(Math.random() * 20000) + 5000).toLocaleString()
  }

  // 清空之前的提取结果
  result.value = null

  // 等待 DOM 更新后初始化 Three.js
  nextTick(() => { initThree(); loadUserMesh(uploadFile.raw) })
}

/**
 * 移除已上传的文件
 * 清理文件状态、提取结果，并销毁 Three.js 场景
 */
const removeFile = () => {
  uploadedFile.value = null
  result.value = null
  disposeThree()
}

// ==================== 水印提取相关函数 ====================

/**
 * 复制水印到剪贴板
 */
const copyWatermark = async () => {
  await navigator.clipboard.writeText(result.value.watermark)
  ElMessage.success('水印内容已复制')
}

/**
 * 启动水印提取流程
 * 模拟实际提取过程（包含加载状态）
 */
const startExtraction = () => {
  isExtracting.value = true
  result.value = null

  // 模拟 2.5 秒的提取过程
  setTimeout(() => {
    isExtracting.value = false

    // 模拟 85% 成功率（实际项目中取决于水印检测算法）
    if (Math.random() > 0.15) {
      // 生成随机的 32 位二进制水印（模拟真实水印）
      let binaryStr = ''
      for (let i = 0; i < 32; i++) binaryStr += Math.random() > 0.5 ? '1' : '0'
      result.value = {
        status: 'success',
        watermark: binaryStr,
        timeTaken: (Math.random() * 3 + 2).toFixed(1) // 模拟耗时 2-5 秒
      }
      ElMessage.success('水印提取成功！')
    } else {
      // 提取失败情况
      result.value = { status: 'error', message: '网格拓扑结构可能已被破坏，提取失败。' }
      ElMessage.error('提取失败')
    }
  }, 2500)
}

// ==================== Three.js 3D 渲染逻辑 ====================

/**
 * 初始化 Three.js 场景
 * 创建场景、相机、渲染器、光源，并开始渲染循环
 */
const initThree = () => {
  if (!canvasContainer.value) return

  // 清理旧资源（防止重复初始化）
  disposeThree()

  // 创建场景，设置深色背景
  scene.value = new THREE.Scene()
  scene.value.background = new THREE.Color(0x1e1e1e)

  // 获取容器尺寸，创建透视相机
  const width = canvasContainer.value.clientWidth
  const height = canvasContainer.value.clientHeight
  camera.value = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000)
  camera.value.position.set(0, 0, 5) // 相机位置：正对前方

  // 创建 WebGL 渲染器，启动抗锯齿
  renderer.value = new THREE.WebGLRenderer({ antialias: true })
  renderer.value.setSize(width, height)
  canvasContainer.value.appendChild(renderer.value.domElement)

  // 创建轨道控制器，支持鼠标交互
  controls.value = new OrbitControls(camera.value, renderer.value.domElement)
  controls.value.enableDamping = true // 启用阻尼效果，使交互更平滑
  // controls.value.autoRotate = true 
  // controls.value.autoRotateSpeed = 2.0
  // 添加光照：环境光 + 方向光，确保模型可见
  scene.value.add(new THREE.AmbientLight(0xffffff, 0.6))
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8)
  dirLight.position.set(5, 5, 5)
  scene.value.add(dirLight)

  // 监听窗口 resize 事件，动态调整渲染尺寸
  window.addEventListener('resize', onWindowResize)

  // 启动渲染循环
  animate()
}

/**
 * 渲染循环函数
 * 每帧更新控制器状态，渲染场景，并让模型缓慢自转
 */
const animate = () => {
  animationFrameId = requestAnimationFrame(animate)
  if (controls.value) controls.value.update()
  if (renderer.value && scene.value && camera.value) {
    // 让模型绕 Y 轴缓慢旋转，增加动态效果
    // if (meshObject.value) meshObject.value.rotation.y += 0.005
    renderer.value.render(scene.value, camera.value)
  }
}

/**
 * 处理窗口尺寸变化
 * 更新相机宽高比和渲染器尺寸
 */
const onWindowResize = () => {
  if (!canvasContainer.value || !camera.value || !renderer.value) return
  camera.value.aspect = canvasContainer.value.clientWidth / canvasContainer.value.clientHeight
  camera.value.updateProjectionMatrix()
  renderer.value.setSize(canvasContainer.value.clientWidth, canvasContainer.value.clientHeight)
}

/**
 * 创建模拟网格模型
 * 使用 IcosahedronGeometry（二十面体）模拟球形网格
 * 实际项目中应解析上传的文件来获取真实几何数据
 */
const createMockMesh = () => {
  // 二十面体几何体，半径 1.5，细节层级 2
  const geometry = new THREE.IcosahedronGeometry(1.5, 2)
  // Teal 色调的材质，粗糙度 0.5
  const material = new THREE.MeshStandardMaterial({
    color: 0x0d9488,
    roughness: 0.5,
    wireframe: false
  })
  meshObject.value = new THREE.Mesh(geometry, material)
  scene.value.add(meshObject.value)
}


// 【修改】加载用户真实上传的网格文件
const loadUserMesh = (file) => {
  const url = URL.createObjectURL(file)
  const ext = file.name.split('.').pop().toLowerCase()

  const defaultMaterial = new THREE.MeshStandardMaterial({ 
    color: 0x0d9488, // 默认青绿色
    roughness: 0.4,
    metalness: 0.1,
    side: THREE.DoubleSide // 双面渲染，防止法线反转导致看不见
  })

  // 居中并缩放的通用处理函数
  const processAndAddObject = (object) => {
    // 计算包围盒
    const box = new THREE.Box3().setFromObject(object)
    const center = box.getCenter(new THREE.Vector3())
    const size = box.getSize(new THREE.Vector3()).length()

    // 居中
    object.position.sub(center)
    
    // 缩放
    const scale = 4 / (size || 1)
    object.scale.setScalar(scale)

    // 为了让旋转中心正确，将 object 放入一个 Group 中
    const group = new THREE.Group()
    group.add(object)
    
    meshObject.value = group
    scene.value.add(meshObject.value)
  }

  if (ext === 'obj') {
    new OBJLoader().load(url, (group) => {
      // OBJLoader 返回的是一个 Group，遍历赋予材质
      group.traverse((child) => {
        if (child.isMesh) child.material = defaultMaterial
      })
      processAndAddObject(group)
      URL.revokeObjectURL(url)
    })
  } else if (ext === 'stl') {
    new STLLoader().load(url, (geometry) => {
      // STLLoader 返回的是 BufferGeometry
      const mesh = new THREE.Mesh(geometry, defaultMaterial)
      processAndAddObject(mesh)
      URL.revokeObjectURL(url)
    })
  } else {
    ElMessage.warning('当前预览仅支持 .obj 和 .stl 格式，其他格式暂不渲染')
  }
}
/**
 * 切换线框模式
 * 用于更清晰地查看网格拓扑结构
 */
// 【修改】兼容 Group 的线框切换逻辑
const toggleWireframe = () => {
  if (meshObject.value) {
    meshObject.value.traverse((child) => {
      if (child.isMesh && child.material) {
        child.material.wireframe = !child.material.wireframe
      }
    })
  }
}

/**
 * 销毁 Three.js 相关资源
 * 清理动画帧、事件监听器、几何体、材质和渲染器
 * 在移除文件或组件卸载时调用
 */
const disposeThree = () => {
  // 取消动画帧
  if (animationFrameId) cancelAnimationFrame(animationFrameId)

  // 移除窗口 resize 监听
  window.removeEventListener('resize', onWindowResize)

  // 释放几何体和材质内存
  if (meshObject.value) {
    meshObject.value.geometry.dispose()
    meshObject.value.material.dispose()
  }

  // 销毁渲染器
  if (renderer.value) {
    renderer.value.dispose()
    // 清空渲染容器的子元素（canvas）
    if (canvasContainer.value) canvasContainer.value.innerHTML = ''
  }
}

/**
 * 组件卸载前清理
 * Vue 组合式 API 的生命周期钩子
 */
onBeforeUnmount(() => disposeThree())
</script>

<style scoped>
/* 上传组件的拖拽区域样式 */
:deep(.custom-upload .el-upload-dragger) {
  background-color: #f8fafc;
  border: 2px dashed #cbd5e1;
  border-radius: 1rem;
  padding: 30px 20px;
  transition: all 0.3s ease;
}

/* 拖拽区域悬停状态：边框变绿色，背景变浅绿 */
:deep(.custom-upload .el-upload-dragger:hover) {
  border-color: #0d9488;
  background-color: #f0fdfa;
}

/* 折叠面板样式调整：去掉顶部和底部的默认边框 */
:deep(.custom-collapse) {
  border-top: none;
  border-bottom: none;
}

/* 折叠面板表头样式 */
:deep(.custom-collapse .el-collapse-item__header) {
  background-color: transparent;
  border-bottom: 1px solid #f1f5f9;
  font-weight: 600;
  color: #475569;
}

/* 折叠面板内容区域样式 */
:deep(.custom-collapse .el-collapse-item__wrap) {
  background-color: transparent;
  border-bottom: none;
}
</style>
