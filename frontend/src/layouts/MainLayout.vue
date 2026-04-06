<template>
  <div class="h-screen flex bg-[#f4f6f8] p-4 gap-4 overflow-hidden">
    <!-- 左侧边栏 (悬浮卡片风格) -->
    <aside class="w-[260px] bg-white rounded-3xl shadow-sm flex flex-col shrink-0 overflow-hidden">
      <!-- Logo 区域 -->
      <div class="pt-10 pb-6 flex flex-col items-center justify-center gap-3 cursor-pointer" @click="$router.push('/dashboard')">
        <div class="relative">
          <div class="absolute inset-0 bg-blue-100 rounded-full scale-125"></div>
          <div class="relative w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center text-white shadow-md">
            <el-icon class="text-3xl"><Connection /></el-icon>
          </div>
        </div>
        <div class="text-center mt-2">
          <h1 class="text-2xl font-bold text-gray-800 tracking-tight">AIGC<span class="text-blue-500">WM</span></h1>
          <p class="text-xs text-gray-400 mt-1 font-medium">智能水印溯源系统</p>
        </div>
      </div>
      
      <!-- 导航菜单 -->
      <div class="flex-1 overflow-y-auto px-4 py-2 custom-scrollbar mt-4">
        <el-menu
          class="border-none custom-menu"
          router
          :default-active="$route.path"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Menu /></el-icon>
            <template #title>系统总览</template>
          </el-menu-item>

          <el-sub-menu index="/image-wm">
            <template #title>
              <el-icon><Picture /></el-icon>
              <span>图像水印</span>
            </template>
            <el-menu-item index="/image-wm/embed">水印嵌入</el-menu-item>
            <el-menu-item index="/image-wm/extract">水印提取</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="/pointcloud-wm">
            <template #title>
              <el-icon><Location /></el-icon>
              <span>点云水印</span>
            </template>
            <el-menu-item index="/pointcloud-wm/embed">水印嵌入</el-menu-item>
            <el-menu-item index="/pointcloud-wm/extract">水印提取</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="/mesh-wm">
            <template #title>
              <el-icon><Box /></el-icon>
              <span>网格水印</span>
            </template>
            <el-menu-item index="/mesh-wm/embed">水印嵌入</el-menu-item>
            <el-menu-item index="/mesh-wm/extract">水印提取</el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/tracing">
            <el-icon><Search /></el-icon>
            <template #title>溯源验真</template>
          </el-menu-item>

          <el-sub-menu index="/data">
            <template #title>
              <el-icon><Folder /></el-icon>
              <span>数据管理</span>
            </template>
            <el-menu-item index="/data/registry">水印注册库</el-menu-item>
            <el-menu-item index="/data/logs">操作日志</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="/system">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统管理</span>
            </template>
            <el-menu-item index="/system/users">用户管理</el-menu-item>
            <el-menu-item index="/system/config">系统配置</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </div>

      <!-- 底部用户信息 -->
      <div class="p-4 mt-auto border-t border-gray-50">
        <div class="flex items-center gap-3 p-3 rounded-2xl bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer" @click="handleLogout">
          <div class="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-lg">
            A
          </div>
          <div class="flex-1 overflow-hidden">
            <p class="text-sm font-bold text-gray-800 truncate">Admin</p>
            <p class="text-xs text-gray-500 truncate">普通用户</p>
          </div>
          <el-icon class="text-gray-400 hover:text-red-500 transition-colors"><SwitchButton /></el-icon>
        </div>
      </div>
    </aside>
    
    <!-- 主内容区 -->
    <main class="flex-1 overflow-y-auto rounded-3xl relative custom-scrollbar">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const handleLogout = () => {
  router.push('/login')
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 自定义菜单样式，匹配参考图的圆角和颜色 */
:deep(.custom-menu) {
  background-color: transparent;
}
:deep(.custom-menu .el-menu-item),
:deep(.custom-menu .el-sub-menu__title) {
  border-radius: 9999px; /* 完全圆角 (Pill shape) */
  margin-bottom: 8px;
  height: 52px;
  line-height: 52px;
  color: #334155;
  font-weight: 600;
  font-size: 15px;
  padding-left: 24px !important;
}
:deep(.custom-menu .el-menu-item:hover),
:deep(.custom-menu .el-sub-menu__title:hover) {
  background-color: #f8fafc;
}
:deep(.custom-menu .el-menu-item.is-active) {
  background-color: #e0e7ff; /* 更柔和的蓝紫色背景 */
  color: #4338ca; /* 更深的蓝紫色文字 */
}
:deep(.custom-menu .el-sub-menu.is-active > .el-sub-menu__title) {
  color: #4338ca;
}
:deep(.custom-menu .el-icon) {
  font-size: 20px;
  margin-right: 12px;
  color: inherit;
}

/* 隐藏滚动条但保留功能 */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #e2e8f0;
  border-radius: 10px;
}
</style>
