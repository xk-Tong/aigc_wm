<template>
  <div class="p-8">
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-800">操作日志</h2>
      <p class="text-sm text-gray-500 mt-1">系统操作审计记录，只读</p>
    </div>

    <!-- 筛选栏 -->
    <div class="bg-white rounded-2xl p-6 mb-6 shadow-sm">
      <div class="flex flex-wrap gap-4 items-center">
        <el-select v-model="operation" placeholder="操作类型" clearable class="w-36" @change="handleSearch">
          <el-option label="全部" value="" />
          <el-option label="登录" value="login" />
          <el-option label="登出" value="logout" />
          <el-option label="注册" value="register" />
          <el-option label="嵌入" value="embed" />
          <el-option label="提取" value="extract" />
          <el-option label="用户管理" value="user_manage" />
        </el-select>

        <el-input v-if="isAdmin" v-model="keyword" placeholder="搜索用户名" clearable class="w-48" @keyup.enter="handleSearch">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>

        <el-button type="primary" @click="handleSearch">查询</el-button>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="bg-white rounded-2xl shadow-sm overflow-hidden">
      <el-table :data="logs" stripe v-loading="loading" class="w-full">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="username" label="用户" width="110">
          <template #default="{ row }">{{ row.username || '-' }}</template>
        </el-table-column>
        <el-table-column prop="operation" label="操作类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ operationLabel(row.operation) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="media_type" label="媒体类型" width="90">
          <template #default="{ row }">
            <span v-if="row.media_type">{{ mediaLabel(row.media_type) }}</span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="request_path" label="请求路径" min-width="200">
          <template #default="{ row }">
            <el-tag size="small" type="info" class="font-mono text-xs">{{ row.request_method }}</el-tag>
            <span class="ml-1 text-sm text-gray-600">{{ row.request_path }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP地址" width="140" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'success' ? 'success' : 'danger'">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="flex justify-end p-4">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import request from '../utils/request'

const logs = ref([])
const loading = ref(false)
const operation = ref('')
const keyword = ref('')
const page = ref(1)
const size = ref(20)
const total = ref(0)

const user = computed(() => {
  try { return JSON.parse(localStorage.getItem('user')) || {} } catch { return {} }
})
const isAdmin = computed(() => ['ADMIN', 'SUPER_ADMIN'].includes(user.value.role))

const operationLabel = (op) => ({
  login: '登录', logout: '登出', register: '注册', embed: '嵌入', extract: '提取', user_manage: '用户管理'
}[op] || op)

const mediaLabel = (t) => ({ image: '图像', pointcloud: '点云', mesh: '网格', gs: '3DGS' }[t] || t)

const formatTime = (t) => {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

const handleSearch = async () => {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (operation.value) params.operation = operation.value
    if (keyword.value) params.keyword = keyword.value
    const res = await request.get('/api/v1/logs', { params })
    if (res?.data?.code === 200) {
      const d = res.data.data
      logs.value = d.items
      total.value = d.total
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => handleSearch())
</script>
