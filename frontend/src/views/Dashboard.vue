<template>
  <div class="max-w-[1400px] mx-auto pb-8 pt-2">
    
    <!-- Bento Grid Layout -->
    <div class="grid grid-cols-12 gap-6">
      
      <!-- Top Left: Image Watermark Stats (参考左上角进度条卡片) -->
      <div class="col-span-12 lg:col-span-4 bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col justify-between hover:shadow-md transition-shadow">
        <div>
          <div class="flex items-center gap-3 mb-6">
            <div class="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
              <el-icon class="text-xl"><Picture /></el-icon>
            </div>
            <h3 class="font-bold text-gray-800 text-lg">图像水印处理</h3>
          </div>
          
          <div class="space-y-5">
            <div class="flex justify-between items-end">
              <span class="text-sm text-gray-500 font-medium">已完成嵌入</span>
              <span class="text-2xl font-bold text-gray-800">1,284 <span class="text-xs font-normal text-gray-400 ml-1">张</span></span>
            </div>
            <div class="flex justify-between items-end">
              <span class="text-sm text-gray-500 font-medium">待处理任务</span>
              <span class="text-2xl font-bold text-blue-600">0 <span class="text-xs font-normal text-gray-400 ml-1">项</span></span>
            </div>
          </div>
        </div>

        <div class="pt-6 mt-6 border-t border-gray-50">
          <div class="flex justify-between text-xs mb-2">
            <span class="text-gray-500">系统处理负载</span>
            <span class="font-bold text-blue-600">16.89%</span>
          </div>
          <el-progress :percentage="16.89" :show-text="false" color="#3b82f6" :stroke-width="8" />
          <div class="flex gap-3 mt-5">
            <el-button class="flex-1 !rounded-xl" @click="$router.push('/image-wm/embed')">新建嵌入</el-button>
            <el-button type="primary" class="flex-1 !rounded-xl" @click="$router.push('/image-wm/extract')">提取水印</el-button>
          </div>
        </div>
      </div>

      <!-- Top Right: Banner (系统公告) -->
      <div class="col-span-12 lg:col-span-8 bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col justify-between hover:shadow-md transition-shadow">
        <div class="flex items-start justify-between mb-2">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center text-red-500">
              <el-icon class="text-xl"><Bell /></el-icon>
            </div>
            <h3 class="font-bold text-gray-800 text-lg">系统公告</h3>
          </div>
          <span class="px-3 py-1 bg-red-100 text-red-600 text-xs font-bold rounded-lg">最新</span>
        </div>
        
        <div class="flex-1 flex flex-col justify-center py-4">
          <h2 class="text-2xl font-bold text-gray-800 mb-3">更新日志</h2>
          <p class="text-gray-500 leading-relaxed text-sm max-w-2xl">
            
          </p>
        </div>
        
        <div class="flex justify-start mt-2">
          <el-button type="primary" round class="!px-6 shadow-sm">查看更新详情</el-button>
        </div>
      </div>

      <!-- Middle Left: 3D Watermark Stats (参考中间左侧复杂卡片) -->
      <div class="col-span-12 lg:col-span-8 bg-white rounded-3xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
        <div class="flex items-center gap-3 mb-6">
          <div class="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600">
            <el-icon class="text-xl"><Box /></el-icon>
          </div>
          <h3 class="font-bold text-gray-800 text-lg">三维数据水印 (点云 & 网格)</h3>
        </div>
        
        <!-- 顶部按钮组 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <el-button class="!h-14 !rounded-2xl !border-gray-200 hover:!border-indigo-500 hover:!text-indigo-600 !text-base" @click="$router.push('/pointcloud-wm/embed')">
            <el-icon class="mr-2 text-lg"><Location /></el-icon> 嵌入点云水印
          </el-button>
          <el-button class="!h-14 !rounded-2xl !border-gray-200 hover:!border-teal-500 hover:!text-teal-600 !text-base" @click="$router.push('/mesh-wm/embed')">
            <el-icon class="mr-2 text-lg"><Box /></el-icon> 嵌入网格水印
          </el-button>
        </div>
        
        <div class="flex items-center gap-4 mb-6">
          <div class="h-px bg-gray-100 flex-1"></div>
          <span class="text-xs text-gray-400 font-medium tracking-widest">STATISTICS</span>
          <div class="h-px bg-gray-100 flex-1"></div>
        </div>

        <!-- 2x2 统计网格 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="bg-gray-50 rounded-2xl p-4 flex items-center justify-between hover:bg-indigo-50 transition-colors cursor-pointer border border-transparent hover:border-indigo-100">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-white shadow-sm flex items-center justify-center text-indigo-500"><el-icon><Location /></el-icon></div>
              <span class="text-sm font-medium text-gray-700">点云已完成</span>
            </div>
            <span class="font-bold text-gray-900 text-xl">320</span>
          </div>
          <div class="bg-gray-50 rounded-2xl p-4 flex items-center justify-between hover:bg-indigo-50 transition-colors cursor-pointer border border-transparent hover:border-indigo-100">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-white shadow-sm flex items-center justify-center text-indigo-500"><el-icon><Loading /></el-icon></div>
              <span class="text-sm font-medium text-gray-700">点云待处理</span>
            </div>
            <span class="font-bold text-indigo-600 text-xl">3</span>
          </div>
          <div class="bg-gray-50 rounded-2xl p-4 flex items-center justify-between hover:bg-teal-50 transition-colors cursor-pointer border border-transparent hover:border-teal-100">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-white shadow-sm flex items-center justify-center text-teal-500"><el-icon><Box /></el-icon></div>
              <span class="text-sm font-medium text-gray-700">网格已完成</span>
            </div>
            <span class="font-bold text-gray-900 text-xl">512</span>
          </div>
          <div class="bg-gray-50 rounded-2xl p-4 flex items-center justify-between hover:bg-teal-50 transition-colors cursor-pointer border border-transparent hover:border-teal-100">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-white shadow-sm flex items-center justify-center text-teal-500"><el-icon><Loading /></el-icon></div>
              <span class="text-sm font-medium text-gray-700">网格待处理</span>
            </div>
            <span class="font-bold text-teal-600 text-xl">0</span>
          </div>
        </div>
      </div>

      <!-- Middle Right: Tracing Actions (参考中间右侧列表卡片) -->
      <div class="col-span-12 lg:col-span-4 bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col hover:shadow-md transition-shadow">
        <div class="flex items-center gap-3 mb-6">
          <div class="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center text-purple-600">
            <el-icon class="text-xl"><Search /></el-icon>
          </div>
          <h3 class="font-bold text-gray-800 text-lg">溯源验真通道</h3>
        </div>
        
        <div class="space-y-3 flex-1 flex flex-col justify-center">
          <div class="p-4 rounded-2xl border border-gray-100 hover:border-blue-200 hover:bg-blue-50 transition-colors cursor-pointer flex items-center justify-between group" @click="$router.push('/tracing')">
            <div class="flex items-center gap-4">
              <div class="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center group-hover:bg-white group-hover:text-blue-500 transition-colors">
                <el-icon class="text-gray-500 group-hover:text-blue-500"><Picture /></el-icon>
              </div>
              <span class="text-sm font-medium text-gray-700 group-hover:text-blue-700">图像溯源验真</span>
            </div>
            <el-icon class="text-gray-300 group-hover:text-blue-500"><ArrowRight /></el-icon>
          </div>
          
          <div class="p-4 rounded-2xl border border-gray-100 hover:border-indigo-200 hover:bg-indigo-50 transition-colors cursor-pointer flex items-center justify-between group" @click="$router.push('/tracing')">
            <div class="flex items-center gap-4">
              <div class="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center group-hover:bg-white group-hover:text-indigo-500 transition-colors">
                <el-icon class="text-gray-500 group-hover:text-indigo-500"><Location /></el-icon>
              </div>
              <span class="text-sm font-medium text-gray-700 group-hover:text-indigo-700">点云溯源验真</span>
            </div>
            <el-icon class="text-gray-300 group-hover:text-indigo-500"><ArrowRight /></el-icon>
          </div>
          
          <div class="p-4 rounded-2xl border border-gray-100 hover:border-teal-200 hover:bg-teal-50 transition-colors cursor-pointer flex items-center justify-between group" @click="$router.push('/tracing')">
            <div class="flex items-center gap-4">
              <div class="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center group-hover:bg-white group-hover:text-teal-500 transition-colors">
                <el-icon class="text-gray-500 group-hover:text-teal-500"><Box /></el-icon>
              </div>
              <span class="text-sm font-medium text-gray-700 group-hover:text-teal-700">网格溯源验真</span>
            </div>
            <el-icon class="text-gray-300 group-hover:text-teal-500"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>

      <!-- Bottom Row: Quick Links (参考底部 4 个小卡片) -->
      <!-- Card 1: Highlighted -->
      <div class="col-span-12 sm:col-span-6 lg:col-span-3 bg-blue-500 rounded-3xl p-6 shadow-md shadow-blue-500/20 text-white cursor-pointer hover:bg-blue-600 transition-colors relative overflow-hidden group" @click="$router.push('/tracing')">
        <el-icon class="absolute top-5 right-5 text-2xl opacity-50 group-hover:opacity-100 group-hover:translate-x-1 group-hover:-translate-y-1 transition-all"><TopRight /></el-icon>
        <div class="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center mb-4 backdrop-blur-sm">
          <el-icon class="text-2xl"><Plus /></el-icon>
        </div>
        <h3 class="font-bold text-lg mb-1">新建溯源任务</h3>
        <p class="text-xs text-blue-100">上传文件，一键提取水印</p>
      </div>

      <!-- Card 2: Normal -->
      <div class="col-span-12 sm:col-span-6 lg:col-span-3 bg-white rounded-3xl p-6 shadow-sm border border-gray-100 cursor-pointer hover:shadow-md transition-all relative group" @click="$router.push('/system/users')">
        <el-icon class="absolute top-5 right-5 text-xl text-gray-300 group-hover:text-blue-500 group-hover:translate-x-1 group-hover:-translate-y-1 transition-all"><TopRight /></el-icon>
        <div class="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center text-gray-600 mb-4 group-hover:bg-blue-50 group-hover:text-blue-500 transition-colors">
          <el-icon class="text-2xl"><User /></el-icon>
        </div>
        <h3 class="font-bold text-gray-800 text-lg mb-1">个人中心</h3>
        <p class="text-xs text-gray-500">查看个人信息，修改密码</p>
      </div>
      
      <!-- Card 3: Normal -->
      <div class="col-span-12 sm:col-span-6 lg:col-span-3 bg-white rounded-3xl p-6 shadow-sm border border-gray-100 cursor-pointer hover:shadow-md transition-all relative group" @click="$router.push('/data/registry')">
        <el-icon class="absolute top-5 right-5 text-xl text-gray-300 group-hover:text-blue-500 group-hover:translate-x-1 group-hover:-translate-y-1 transition-all"><TopRight /></el-icon>
        <div class="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center text-gray-600 mb-4 group-hover:bg-blue-50 group-hover:text-blue-500 transition-colors">
          <el-icon class="text-2xl"><Folder /></el-icon>
        </div>
        <h3 class="font-bold text-gray-800 text-lg mb-1">水印注册库</h3>
        <p class="text-xs text-gray-500">管理已注册的水印信息</p>
      </div>

      <!-- Card 4: Normal -->
      <div class="col-span-12 sm:col-span-6 lg:col-span-3 bg-white rounded-3xl p-6 shadow-sm border border-gray-100 cursor-pointer hover:shadow-md transition-all relative group" @click="$router.push('/data/logs')">
        <el-icon class="absolute top-5 right-5 text-xl text-gray-300 group-hover:text-blue-500 group-hover:translate-x-1 group-hover:-translate-y-1 transition-all"><TopRight /></el-icon>
        <div class="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center text-gray-600 mb-4 group-hover:bg-blue-50 group-hover:text-blue-500 transition-colors">
          <el-icon class="text-2xl"><Document /></el-icon>
        </div>
        <h3 class="font-bold text-gray-800 text-lg mb-1">操作日志</h3>
        <p class="text-xs text-gray-500">查看系统运行与操作记录</p>
      </div>

    </div>
  </div>
</template>

<script setup>
// Dashboard logic
</script>
