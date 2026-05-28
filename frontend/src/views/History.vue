<template>
  <div class="p-8">
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-800">我的历史</h2>
      <p class="text-sm text-gray-500 mt-1">查看所有水印嵌入和提取操作记录</p>
    </div>

    <!-- 筛选栏 -->
    <div class="bg-white rounded-2xl p-6 mb-6 shadow-sm">
      <div class="flex flex-wrap gap-4 items-center">
        <el-radio-group v-model="mediaType" @change="handleSearch">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="image">图像</el-radio-button>
          <el-radio-button value="pointcloud">点云</el-radio-button>
          <el-radio-button value="mesh">网格</el-radio-button>
          <el-radio-button value="gs">3DGS</el-radio-button>
        </el-radio-group>

        <el-select v-model="operationType" placeholder="操作类型" clearable class="w-32" @change="handleSearch">
          <el-option label="全部" value="" />
          <el-option label="嵌入" value="embed" />
          <el-option label="提取" value="extract" />
        </el-select>

        <el-input v-if="isAdmin" v-model="keyword" placeholder="搜索用户名/水印值" clearable class="w-56" @clear="handleSearch" @keyup.enter="handleSearch">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>

        <el-button type="primary" @click="handleSearch">查询</el-button>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="bg-white rounded-2xl shadow-sm overflow-hidden">
      <el-table :data="records" stripe v-loading="loading" class="w-full">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column v-if="isAdmin" prop="username" label="用户" width="100" />
        <el-table-column prop="media_type" label="媒体类型" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="mediaTagType(row.media_type)">{{ mediaLabel(row.media_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operation_type" label="操作" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.operation_type === 'embed' ? 'success' : 'warning'">
              {{ row.operation_type === 'embed' ? '嵌入' : '提取' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="watermark_bits" label="水印值" width="130">
          <template #default="{ row }">
            <span class="font-mono text-sm">{{ row.watermark_bits || row.extracted_bits || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'success' ? 'success' : 'danger'">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="elapsed_ms" label="耗时" width="100">
          <template #default="{ row }">{{ row.elapsed_ms ? `${(row.elapsed_ms / 1000).toFixed(1)}s` : '-' }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.download_url" link type="primary" size="small" @click="downloadFile(row.download_url)">
              下载
            </el-button>
            <span v-else class="text-gray-400 text-sm">-</span>
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

const records = ref([])
const loading = ref(false)
const mediaType = ref('')
const operationType = ref('')
const keyword = ref('')
const page = ref(1)
const size = ref(20)
const total = ref(0)

const user = computed(() => {
  try { return JSON.parse(localStorage.getItem('user')) || {} } catch { return {} }
})
const isAdmin = computed(() => ['ADMIN', 'SUPER_ADMIN'].includes(user.value.role))

const mediaLabel = (t) => ({ image: '图像', pointcloud: '点云', mesh: '网格', gs: '3DGS' }[t] || t)
const mediaTagType = (t) => ({ image: 'primary', pointcloud: 'success', mesh: 'warning', gs: 'danger' }[t] || 'info')

const formatTime = (t) => {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

const downloadFile = (url) => {
  window.open(url, '_blank')
}

const handleSearch = async () => {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (mediaType.value) params.media_type = mediaType.value
    if (operationType.value) params.operation_type = operationType.value
    if (keyword.value) params.keyword = keyword.value
    const res = await request.get('/api/v1/records', { params })
    if (res?.data?.code === 200) {
      const d = res.data.data
      records.value = d.items
      total.value = d.total
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => handleSearch())
</script>
