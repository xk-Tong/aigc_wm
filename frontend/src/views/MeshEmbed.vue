<template>
  <div class="max-w-[1400px] mx-auto pb-8 pt-2">
    <!-- 页面标题区域：包含图标和标题文字 -->
    <div class="flex items-center gap-3 mb-6 px-2">
      <div class="w-10 h-10 rounded-xl bg-teal-100 flex items-center justify-center text-teal-600">
        <el-icon class="text-xl"><Box /></el-icon>
      </div>
      <h2 class="text-2xl font-bold text-gray-800 tracking-tight">网格水印嵌入</h2>
    </div>

    <!-- 左右两栏布局：左侧参数配置 + 右侧结果预览 -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

      <!-- ================= 左侧栏：参数配置区域 ================= -->
      <div class="lg:col-span-5 space-y-6">
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <h3 class="text-lg font-bold text-gray-800 mb-5">生成参数配置</h3>

          <!-- 表单区域：使用 Element Plus 的 form 组件 -->
          <el-form label-position="top" class="space-y-4">
            <!-- 1. 输入类型切换：文字描述 vs 参考图像 -->
            <el-form-item label="输入模式">
              <el-radio-group v-model="formData.inputType" class="w-full">
                <el-radio-button label="text" class="flex-1 text-center">文字描述</el-radio-button>
                <el-radio-button label="image" class="flex-1 text-center">参考图像</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <!-- 2. 文字输入模式：当 inputType === 'text' 时显示 -->
            <!-- Prompt 是用于描述期望生成的 3D 模型特征的文本 -->
            <el-form-item v-if="formData.inputType === 'text'" label="网格描述 (Prompt)">
              <el-input
                v-model="formData.prompt"
                type="textarea"
                :rows="4"
                maxlength="1000"
                show-word-limit
                placeholder="请输入网格模型描述，如：一个精致的青花瓷瓶..."
                class="custom-textarea"
              />
            </el-form-item>

            <!-- 3. 图像输入模式：当 inputType === 'image' 时显示 -->
            <!-- 用户可以上传参考图像，系统会根据图像特征生成 3D 模型 -->
            <el-form-item v-if="formData.inputType === 'image'" label="参考图像">
              <!-- 未上传时显示拖拽上传区域 -->
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
                <el-icon class="el-icon--upload text-teal-400"><UploadFilled /></el-icon>
                <div class="el-upload__text text-gray-600">
                  将图像拖拽到此处，或 <em class="text-teal-500 font-bold not-italic">点击上传</em>
                </div>
              </el-upload>

              <!-- 已上传图像预览：显示缩略图和删除按钮 -->
              <div v-else class="relative rounded-xl overflow-hidden border border-gray-200 group">
                <img :src="uploadedImageUrl" class="w-full h-40 object-cover" />
                <!-- 悬停时显示半透明黑色遮罩和删除按钮 -->
                <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <el-button type="danger" circle @click="removeImage">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </el-form-item>

            <!-- 4. 模型选择：选择用于生成网格的 AI 模型 -->
            <el-form-item label="生成模型">
              <el-select v-model="formData.model" size="large" class="w-full">
                <el-option label="Trellis (推荐)" value="trellis" />
                <el-option label="ShapE" value="shapE" />
              </el-select>
            </el-form-item>

            <!-- 5. 水印信息输入：用户输入 32 位二进制水印 -->
            <el-form-item label="水印信息 (32位二进制)">
              <div class="flex gap-2 w-full">
                <!-- 水印输入框：使用等宽字体显示 -->
                <el-input
                  v-model="formData.watermark"
                  placeholder="请输入32位二进制水印..."
                  size="large"
                  maxlength="32"
                  class="flex-1 font-mono"
                />
                <!-- 随机生成按钮：一键生成随机水印 -->
                <el-button size="large" @click="generateRandomWatermark" class="shrink-0">
                  <el-icon class="mr-1"><Refresh /></el-icon> 随机生成
                </el-button>
              </div>
            </el-form-item>

            <!-- 6. 生成按钮：主操作按钮 -->
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

        <!-- 3D 预览区域：显示生成的网格模型 -->
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col h-[500px]" ref="fullscreenContainer">
          <!-- 预览区标题栏：包含标题和工具按钮 -->
          <div class="flex justify-between items-center mb-4 shrink-0">
            <h3 class="text-lg font-bold text-gray-800">网格 3D 预览</h3>
            <!-- 工具栏按钮组：仅在有生成结果时显示 -->
            <el-button-group v-if="result">
              <el-button size="small" title="重置视角" @click="resetView"><el-icon><RefreshLeft /></el-icon></el-button>
              <el-button size="small" title="切换线框模式" @click="toggleWireframe"><el-icon><Grid /></el-icon></el-button>
              <el-button size="small" title="全屏预览" @click="toggleFullscreen"><el-icon><FullScreen /></el-icon></el-button>
            </el-button-group>
          </div>

          <!-- Three.js 渲染容器：实际绘制 3D 网格的位置 -->
          <div class="flex-1 rounded-2xl overflow-hidden relative border border-gray-100 bg-[#1e1e1e]" ref="canvasContainer">
            <!-- 空白状态：未生成时显示 -->
            <div v-if="!result && !isGenerating" class="absolute inset-0 flex flex-col items-center justify-center text-gray-400 bg-[#f8fafc] z-10">
              <el-icon class="text-5xl mb-2 opacity-50"><Box /></el-icon>
              <p>等待生成</p>
            </div>

            <!-- 加载状态：生成过程中显示进度 -->
            <div v-else-if="isGenerating" class="absolute inset-0 flex flex-col items-center justify-center bg-[#f8fafc]/90 backdrop-blur-sm z-10">
              <!-- 环形进度条：显示生成进度百分比 -->
              <el-progress type="dashboard" :percentage="generateProgress" color="#0d9488" />
              <p class="text-sm font-medium text-teal-600 mt-4 animate-pulse">正在构建 3D 网格并嵌入水印...</p>
            </div>
          </div>
        </div>

        <!-- 生成完成后的信息与操作区域 -->
        <transition name="el-fade-in-linear">
          <div v-if="result" class="space-y-6">

            <!-- 模型信息行 & 操作按钮 -->
            <div class="flex flex-wrap items-center justify-between bg-white rounded-2xl p-4 shadow-sm border border-gray-100 gap-4">
              <!-- 统计信息：面片数、生成耗时 -->
              <div class="flex items-center gap-4 text-sm text-gray-600 font-medium ml-2">
                <span><el-icon class="mr-1 align-middle"><DataAnalysis /></el-icon> 面片数: <span class="text-gray-800 font-bold">{{ result.facesCount.toLocaleString() }}</span></span>
                <el-divider direction="vertical" />
                <span><el-icon class="mr-1 align-middle"><Timer /></el-icon> 耗时: <span class="text-gray-800 font-bold">{{ result.timeTaken }}s</span></span>
              </div>

              <!-- 操作按钮：重新生成 + 下载模型 -->
              <div class="flex gap-3">
                <el-button plain round @click="handleGenerate">重新生成</el-button>
                <!-- 下载下拉菜单：支持 OBJ、STL、GLTF 格式 -->
                <el-dropdown @command="handleDownload">
                  <el-button type="primary" round class="shadow-md shadow-teal-500/20 bg-teal-600! border-none!">
                    <el-icon class="mr-1"><Download /></el-icon> 下载模型<el-icon class="el-icon--right"><arrow-down /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="obj">下载 .obj 格式</el-dropdown-item>
                      <el-dropdown-item command="stl">下载 .stl 格式</el-dropdown-item>
                      <el-dropdown-item command="gltf">下载 .gltf 格式</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>

            <!-- 水印信息卡片：显示已嵌入的水印 -->
            <div class="bg-teal-50/50 rounded-3xl p-6 border border-teal-100 relative overflow-hidden">
              <!-- 装饰性背景模糊效果 -->
              <div class="absolute top-0 right-0 w-32 h-32 bg-teal-500/5 rounded-full blur-2xl -mr-10 -mt-10"></div>

              <h4 class="text-sm font-bold text-teal-800 mb-4 flex items-center">
                <el-icon class="mr-2 text-lg"><Key /></el-icon> 已嵌入水印信息
              </h4>

              <!-- 水印二进制内容：等宽字体显示，每 8 位空格分隔 -->
              <div class="bg-white rounded-xl p-4 border border-teal-100/50 flex justify-between items-center shadow-sm mb-4">
                <span class="font-mono text-lg text-gray-800 tracking-widest font-bold">
                  {{ formattedWatermark }}
                </span>
                <!-- 复制按钮：点击复制水印到剪贴板 -->
                <el-button circle size="small" @click="copyWatermark" title="复制水印">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </div>

              <!-- 嵌入时间 -->
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
/**
 * 网格水印嵌入页面
 *
 * 功能说明：
 * 1. 用户输入文字描述或上传参考图像
 * 2. 系统根据输入生成 3D 网格模型
 * 3. 用户输入 32 位二进制水印信息
 * 4. 系统将水印嵌入到网格拓扑结构中
 * 5. 用户可以下载嵌入水印后的 3D 模型
 *
 * 技术栈：
 * - Vue 3 Composition API (setup 语法糖)
 * - Element Plus UI 组件库
 * - Three.js 3D 渲染引擎
 */

import { ref, computed, onBeforeUnmount, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

// ==================== 响应式状态变量 ====================

/**
 * 表单数据对象
 * - inputType: 输入模式，'text' 或 'image'
 * - prompt: 文字描述（当 inputType 为 text 时使用）
 * - model: 选择的生成模型
 * - watermark: 32 位二进制水印字符串
 */
const formData = ref({
  inputType: 'text',
  prompt: '',
  model: 'trellis',
  watermark: ''
})

/** 上传的参考图像的 Blob URL */
const uploadedImageUrl = ref('')

/** 是否正在执行生成操作（控制按钮 loading 状态） */
const isGenerating = ref(false)

/** 生成进度百分比（0-100），用于进度条显示 */
const generateProgress = ref(0)

/** 生成结果：包含 facesCount、watermark、timeTaken、timestamp 等字段 */
const result = ref(null)

// ==================== Three.js 3D 渲染相关变量 ====================

/** Three.js 渲染容器的 DOM 引用 */
const canvasContainer = ref(null)

/** 全屏容器的 DOM 引用（用于全屏功能） */
const fullscreenContainer = ref(null)

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
 * 格式化水印二进制字符串：每 8 位插入一个空格，提高可读性
 * 例如：'1010101010101010' -> '10101010 10101010'
 */
const formattedWatermark = computed(() => {
  if (!result.value || !result.value.watermark) return ''
  return result.value.watermark.replace(/(.{8})/g, '$1 ').trim()
})

// ==================== 水印与图像处理函数 ====================

/**
 * 生成随机的 32 位二进制水印
 * 用于用户一键生成随机水印
 */
const generateRandomWatermark = () => {
  let binaryStr = ''
  for (let i = 0; i < 32; i++) binaryStr += Math.random() > 0.5 ? '1' : '0'
  formData.value.watermark = binaryStr
}

/**
 * 复制水印到剪贴板
 */
const copyWatermark = async () => {
  try {
    await navigator.clipboard.writeText(result.value.watermark)
    ElMessage.success('水印已复制')
  } catch (err) {
    ElMessage.error('复制失败')
  }
}

/**
 * 处理参考图像上传
 * 创建图像的 Blob URL 用于预览
 *
 * @param {Object} uploadFile - Element Plus 上传组件的 file 对象
 */
const handleImageChange = (uploadFile) => {
  uploadedImageUrl.value = URL.createObjectURL(uploadFile.raw)
}

/**
 * 移除已上传的参考图像
 * 释放 Blob URL 内存
 */
const removeImage = () => {
  if (uploadedImageUrl.value) URL.revokeObjectURL(uploadedImageUrl.value)
  uploadedImageUrl.value = ''
}

/**
 * 处理模型下载
 * 根据用户选择的格式触发下载流程
 *
 * @param {string} format - 下载格式，'obj' | 'stl' | 'gltf'
 */
const handleDownload = (format) => {
  ElMessage.success(`开始下载 ${format.toUpperCase()} 格式模型...`)
}

// ==================== Three.js 3D 渲染逻辑 ====================

/**
 * 初始化 Three.js 场景
 * 创建场景、相机、渲染器、光源，并开始渲染循环
 */
const initThree = () => {
  if (!canvasContainer.value) return

  // 创建场景，设置深色背景
  scene.value = new THREE.Scene()
  scene.value.background = new THREE.Color(0x1e1e1e)

  // 获取容器尺寸，创建透视相机
  const width = canvasContainer.value.clientWidth
  const height = canvasContainer.value.clientHeight
  camera.value = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000)
  camera.value.position.set(0, 0, 6) // 相机位置：距离中心 6 个单位

  // 创建 WebGL 渲染器，启动抗锯齿
  renderer.value = new THREE.WebGLRenderer({ antialias: true })
  renderer.value.setSize(width, height)
  renderer.value.setPixelRatio(window.devicePixelRatio) // 支持高分屏
  canvasContainer.value.appendChild(renderer.value.domElement)

  // 创建轨道控制器，支持鼠标交互
  controls.value = new OrbitControls(camera.value, renderer.value.domElement)
  controls.value.enableDamping = true // 启用阻尼效果，使交互更平滑

  // 添加光照：环境光 + 方向光，确保模型可见
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.value.add(ambientLight)
  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(10, 10, 10)
  scene.value.add(directionalLight)

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
    if (meshObject.value) meshObject.value.rotation.y += 0.005
    renderer.value.render(scene.value, camera.value)
  }
}

/**
 * 处理窗口尺寸变化
 * 更新相机宽高比和渲染器尺寸
 */
const onWindowResize = () => {
  if (!canvasContainer.value || !camera.value || !renderer.value) return
  const width = canvasContainer.value.clientWidth
  const height = canvasContainer.value.clientHeight
  camera.value.aspect = width / height
  camera.value.updateProjectionMatrix()
  renderer.value.setSize(width, height)
}

/**
 * 创建模拟网格模型
 * 使用 TorusKnotGeometry（环面纽结）生成复杂的 3D 网格
 * 这是一个视觉效果丰富的参数化几何体，适合展示
 *
 * TorusKnotGeometry 参数：
 * - radius: 环面主半径
 * - tube: 管道半径
 * - radialSegments: 管道横分段数
 * - tubularSegments: 管道长度分段数
 */
const createMockMesh = () => {
  // 如果已有网格，先移除
  if (meshObject.value) {
    scene.value.remove(meshObject.value)
    meshObject.value.geometry.dispose()
    meshObject.value.material.dispose()
  }

  // 创建环面纽结几何体
  const geometry = new THREE.TorusKnotGeometry(1.2, 0.4, 128, 32)
  // Teal 色调的材质，有金属光泽
  const material = new THREE.MeshStandardMaterial({
    color: 0x0d9488,
    roughness: 0.3,  // 较低的粗糙度增加金属感
    metalness: 0.2,  // 轻微的金属质感
    wireframe: false
  })
  meshObject.value = new THREE.Mesh(geometry, material)
  scene.value.add(meshObject.value)
}

/**
 * 重置视角
 * 将相机位置和观察目标恢复到初始状态
 */
const resetView = () => {
  if (camera.value && controls.value) {
    camera.value.position.set(0, 0, 6)
    controls.value.target.set(0, 0, 0)
  }
}

/**
 * 切换线框模式
 * 用于更清晰地查看网格拓扑结构
 */
const toggleWireframe = () => {
  if (meshObject.value) {
    meshObject.value.material.wireframe = !meshObject.value.material.wireframe
  }
}

/**
 * 切换全屏模式
 * 使用浏览器 Fullscreen API 实现全屏预览
 */
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    fullscreenContainer.value?.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

// ==================== 模型生成与水印嵌入 ====================

/**
 * 处理生成按钮点击事件
 * 1. 验证水印输入
 * 2. 模拟生成过程（进度条）
 * 3. 创建 3D 网格并嵌入水印
 * 4. 显示生成结果
 */
const handleGenerate = () => {
  // 验证：检查水印是否为 32 位二进制
  if (!formData.value.watermark || formData.value.watermark.length !== 32) {
    ElMessage.warning('请输入有效的 32 位二进制水印')
    return
  }

  // 重置状态
  isGenerating.value = true
  generateProgress.value = 0
  result.value = null

  // 模拟生成进度
  const interval = setInterval(() => {
    // 随机增加进度（模拟真实的生成过程）
    generateProgress.value += Math.floor(Math.random() * 15)

    if (generateProgress.value >= 100) {
      clearInterval(interval)
      generateProgress.value = 100

      // 完成后延迟 500ms 显示结果（让用户看到 100% 状态）
      setTimeout(() => {
        isGenerating.value = false

        // 如果场景不存在，先初始化
        if (!scene.value) initThree()

        // 创建模拟网格
        createMockMesh()

        // 重置视角
        resetView()

        // 设置结果数据
        result.value = {
          facesCount: 8192,
          watermark: formData.value.watermark,
          timeTaken: (Math.random() * 10 + 20).toFixed(1), // 模拟耗时 20-30 秒
          timestamp: new Date().toLocaleString('zh-CN', { hour12: false })
        }

        ElMessage.success('网格生成并嵌入水印成功！')
      }, 500)
    }
  }, 300)
}

// ==================== 生命周期与清理 ====================

/**
 * 组件卸载前清理
 * 销毁 Three.js 相关资源，防止内存泄漏
 */
onBeforeUnmount(() => {
  // 移除窗口 resize 监听
  window.removeEventListener('resize', onWindowResize)

  // 取消动画帧
  if (animationFrameId) cancelAnimationFrame(animationFrameId)

  // 销毁渲染器
  if (renderer.value) renderer.value.dispose()

  // 释放几何体和材质内存
  if (meshObject.value) {
    meshObject.value.geometry.dispose()
    meshObject.value.material.dispose()
  }
})
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

/* 拖拽区域悬停状态 */
:deep(.custom-upload .el-upload-dragger:hover) {
  border-color: #0d9488;
  background-color: #f0fdfa;
}

/* 文本域输入框样式 */
:deep(.custom-textarea .el-textarea__inner) {
  background-color: #f8fafc;
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid #e2e8f0;
  padding: 12px;
  transition: all 0.2s ease;
}

/* 文本域聚焦状态 */
:deep(.custom-textarea .el-textarea__inner:focus) {
  box-shadow: 0 0 0 2px rgba(13, 148, 136, 0.2);
  border-color: #0d9488;
  background-color: #ffffff;
}

/* 全屏模式背景色 */
:fullscreen {
  background-color: #f4f6f8;
  padding: 24px;
}
</style>
