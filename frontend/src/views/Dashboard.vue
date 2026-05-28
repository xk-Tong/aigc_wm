<template>
  <div class="max-w-[1400px] mx-auto pb-8 pt-2">
    <div class="mb-6 px-2">
      <h2 class="text-2xl font-bold text-gray-800">系统总览</h2>
      <p class="text-sm text-gray-500 mt-1">欢迎使用智能水印溯源系统</p>
    </div>

    <!-- 水印功能入口区 -->
    <div class="mb-6">
      <h3 class="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4 px-2">水印功能</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md hover:border-blue-200 transition-all cursor-pointer group" @click="$router.push('/image-wm/embed')">
          <div class="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 mb-3 group-hover:bg-blue-100 transition-colors">
            <el-icon class="text-xl"><Picture /></el-icon>
          </div>
          <h4 class="font-bold text-gray-800 mb-1">图像水印</h4>
          <p class="text-xs text-gray-400">生成 / 提取图像水印</p>
        </div>

        <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md hover:border-indigo-200 transition-all cursor-pointer group" @click="$router.push('/pointcloud-wm/embed')">
          <div class="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 mb-3 group-hover:bg-indigo-100 transition-colors">
            <el-icon class="text-xl"><Location /></el-icon>
          </div>
          <h4 class="font-bold text-gray-800 mb-1">点云水印</h4>
          <p class="text-xs text-gray-400">生成 / 提取点云水印</p>
        </div>

        <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md hover:border-teal-200 transition-all cursor-pointer group" @click="$router.push('/mesh-wm/embed')">
          <div class="w-10 h-10 rounded-xl bg-teal-50 flex items-center justify-center text-teal-600 mb-3 group-hover:bg-teal-100 transition-colors">
            <el-icon class="text-xl"><Box /></el-icon>
          </div>
          <h4 class="font-bold text-gray-800 mb-1">网格水印</h4>
          <p class="text-xs text-gray-400">生成 / 提取网格水印</p>
        </div>

        <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md hover:border-violet-200 transition-all cursor-pointer group" @click="$router.push('/gs-wm/embed')">
          <div class="w-10 h-10 rounded-xl bg-violet-50 flex items-center justify-center text-violet-600 mb-3 group-hover:bg-violet-100 transition-colors">
            <el-icon class="text-xl"><Histogram /></el-icon>
          </div>
          <h4 class="font-bold text-gray-800 mb-1">3DGS水印</h4>
          <p class="text-xs text-gray-400">生成 / 提取 3DGS水印</p>
        </div>
      </div>
    </div>

    <!-- 数据管理入口区 -->
    <div class="mb-6">
      <h3 class="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4 px-2">数据管理</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-all cursor-pointer group" @click="$router.push('/data/history')">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center text-amber-600 group-hover:bg-amber-100 transition-colors">
              <el-icon class="text-xl"><Clock /></el-icon>
            </div>
            <div>
              <h4 class="font-bold text-gray-800">我的历史</h4>
              <p class="text-xs text-gray-400">查看水印操作记录</p>
            </div>
          </div>
        </div>

        <div v-if="isAdmin" class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-all cursor-pointer group" @click="$router.push('/data/registry')">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-cyan-50 flex items-center justify-center text-cyan-600 group-hover:bg-cyan-100 transition-colors">
              <el-icon class="text-xl"><Folder /></el-icon>
            </div>
            <div>
              <h4 class="font-bold text-gray-800">水印注册库</h4>
              <p class="text-xs text-gray-400">浏览已嵌入的水印记录</p>
            </div>
          </div>
        </div>

        <div v-if="isAdmin" class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-all cursor-pointer group" @click="$router.push('/data/logs')">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-rose-50 flex items-center justify-center text-rose-600 group-hover:bg-rose-100 transition-colors">
              <el-icon class="text-xl"><Document /></el-icon>
            </div>
            <div>
              <h4 class="font-bold text-gray-800">操作日志</h4>
              <p class="text-xs text-gray-400">系统操作审计记录</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 系统管理入口区（仅管理员可见） -->
    <div v-if="isAdmin" class="mb-6">
      <h3 class="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4 px-2">系统管理</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-all cursor-pointer group" @click="$router.push('/system/users')">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600 group-hover:bg-emerald-100 transition-colors">
              <el-icon class="text-xl"><User /></el-icon>
            </div>
            <div>
              <h4 class="font-bold text-gray-800">用户管理</h4>
              <p class="text-xs text-gray-400">管理用户和角色权限</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-all cursor-pointer group" @click="$router.push('/profile')">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center text-purple-600 group-hover:bg-purple-100 transition-colors">
              <el-icon class="text-xl"><UserFilled /></el-icon>
            </div>
            <div>
              <h4 class="font-bold text-gray-800">个人中心</h4>
              <p class="text-xs text-gray-400">查看信息，修改密码</p>
            </div>
          </div>
        </div>

        <div v-if="isSuperAdmin" class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-all cursor-pointer group" @click="$router.push('/system/config')">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-slate-600 group-hover:bg-slate-200 transition-colors">
              <el-icon class="text-xl"><Setting /></el-icon>
            </div>
            <div>
              <h4 class="font-bold text-gray-800">系统配置</h4>
              <p class="text-xs text-gray-400">全局参数与设置</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const user = computed(() => {
  try { return JSON.parse(localStorage.getItem('user')) || {} } catch { return {} }
})
const isAdmin = computed(() => ['ADMIN', 'SUPER_ADMIN'].includes(user.value.role))
const isSuperAdmin = computed(() => user.value.role === 'SUPER_ADMIN')
</script>
