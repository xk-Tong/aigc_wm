<template>
  <div class="p-8">
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-800">用户管理</h2>
      <p class="text-sm text-gray-500 mt-1">管理系统用户、角色和权限</p>
    </div>

    <div class="bg-white rounded-2xl p-6 mb-6 shadow-sm">
      <div class="flex flex-wrap gap-4 items-center">
        <el-input v-model="keyword" placeholder="搜索用户名/邮箱" clearable class="w-56" @keyup.enter="handleSearch">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="roleFilter" placeholder="角色筛选" clearable class="w-36" @change="handleSearch">
          <el-option label="普通用户" value="USER" />
          <el-option label="管理员" value="ADMIN" />
          <el-option v-if="isSuperAdmin" label="超级管理员" value="SUPER_ADMIN" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="状态筛选" clearable class="w-28" @change="handleSearch">
          <el-option label="正常" :value="1" />
          <el-option label="禁用" :value="0" />
        </el-select>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </div>
    </div>

    <div class="bg-white rounded-2xl shadow-sm overflow-hidden">
      <el-table :data="users" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="role" label="角色" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="roleTagType(row.role)">{{ roleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-switch
              :model-value="row.status === 1"
              :disabled="row.id === currentUserId"
              @change="(val) => handleToggleStatus(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-dropdown v-if="row.id !== currentUserId" @command="(cmd) => handleRoleChange(row, cmd)">
              <el-button link type="primary" size="small">改角色 <el-icon class="ml-1"><ArrowDown /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="USER">普通用户</el-dropdown-item>
                  <el-dropdown-item command="ADMIN">管理员</el-dropdown-item>
                  <el-dropdown-item v-if="isSuperAdmin" command="SUPER_ADMIN">超级管理员</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <span v-else class="text-gray-300 text-sm">-</span>
            <el-button v-if="row.id !== currentUserId" link type="primary" size="small" class="ml-2" @click="showResetDialog(row)">
              重置密码
            </el-button>
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

    <!-- 重置密码对话框 -->
    <el-dialog v-model="resetDialogVisible" title="重置密码" width="400px" center>
      <el-form ref="resetFormRef" :model="resetForm" :rules="resetRules" label-position="top">
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="resetForm.new_password" type="password" show-password placeholder="至少8位字符" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="resetLoading" @click="handleResetPassword">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, ArrowDown } from '@element-plus/icons-vue'
import request from '../utils/request'

const users = ref([])
const loading = ref(false)
const keyword = ref('')
const roleFilter = ref('')
const statusFilter = ref(null)
const page = ref(1)
const size = ref(20)
const total = ref(0)

const resetDialogVisible = ref(false)
const resetLoading = ref(false)
const resetForm = ref({ new_password: '', user_id: null, username: '' })
const resetFormRef = ref()
const resetRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码至少8位', trigger: 'blur' },
  ],
}

const currentUser = computed(() => {
  try { return JSON.parse(localStorage.getItem('user')) || {} } catch { return {} }
})
const currentUserId = computed(() => currentUser.value.id)
const isSuperAdmin = computed(() => currentUser.value.role === 'SUPER_ADMIN')

const roleLabel = (r) => ({ USER: '普通用户', ADMIN: '管理员', SUPER_ADMIN: '超级管理员' }[r] || r)
const roleTagType = (r) => ({ USER: 'info', ADMIN: 'warning', SUPER_ADMIN: 'danger' }[r] || 'info')

const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'

const handleSearch = async () => {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (keyword.value) params.keyword = keyword.value
    if (roleFilter.value) params.role = roleFilter.value
    if (statusFilter.value !== null && statusFilter.value !== '') params.status = statusFilter.value
    const res = await request.get('/api/v1/users', { params })
    if (res?.data?.code === 200) {
      const d = res.data.data
      users.value = d.items
      total.value = d.total
    }
  } finally {
    loading.value = false
  }
}

const handleToggleStatus = async (row, val) => {
  try {
    await request.put(`/api/v1/users/${row.id}/status`, { status: val ? 1 : 0 })
    row.status = val ? 1 : 0
    ElMessage.success(`已${val ? '启用' : '禁用'}用户`)
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '操作失败')
  }
}

const handleRoleChange = async (row, newRole) => {
  if (newRole === row.role) return
  try {
    await request.put(`/api/v1/users/${row.id}/role`, { role: newRole })
    row.role = newRole
    ElMessage.success('角色修改成功')
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '操作失败')
  }
}

const showResetDialog = (row) => {
  resetForm.value = { new_password: '', user_id: row.id, username: row.username }
  resetDialogVisible.value = true
}

const handleResetPassword = async () => {
  try {
    await resetFormRef.value.validate()
  } catch { return }

  resetLoading.value = true
  try {
    await request.post(`/api/v1/users/${resetForm.value.user_id}/reset-password`, {
      new_password: resetForm.value.new_password,
    })
    ElMessage.success('密码重置成功')
    resetDialogVisible.value = false
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '操作失败')
  } finally {
    resetLoading.value = false
  }
}

onMounted(() => handleSearch())
</script>
