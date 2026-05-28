<template>
  <div class="max-w-[800px] mx-auto pb-8 pt-2">
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-800">个人中心</h2>
      <p class="text-sm text-gray-500 mt-1">查看个人信息，修改登录密码</p>
    </div>

    <!-- 用户信息卡片 -->
    <div class="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 mb-6">
      <div class="flex items-center gap-4 mb-8">
        <div class="w-16 h-16 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-2xl">
          {{ profile.username ? profile.username.charAt(0).toUpperCase() : 'U' }}
        </div>
        <div>
          <h3 class="text-xl font-bold text-gray-800">{{ profile.username }}</h3>
          <p class="text-sm text-gray-500">{{ profile.email }}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div class="bg-gray-50 rounded-2xl p-4">
          <p class="text-xs text-gray-400 mb-1">角色</p>
          <el-tag size="small" :type="roleTagType(profile.role)">{{ roleLabel(profile.role) }}</el-tag>
        </div>
        <div class="bg-gray-50 rounded-2xl p-4">
          <p class="text-xs text-gray-400 mb-1">账号状态</p>
          <el-tag size="small" :type="profile.status === 1 ? 'success' : 'danger'">
            {{ profile.status === 1 ? '正常' : '已禁用' }}
          </el-tag>
        </div>
        <div class="bg-gray-50 rounded-2xl p-4">
          <p class="text-xs text-gray-400 mb-1">注册时间</p>
          <p class="text-sm font-medium text-gray-800">{{ formatTime(profile.created_at) }}</p>
        </div>
      </div>
    </div>

    <!-- 修改密码卡片 -->
    <div class="bg-white rounded-3xl p-8 shadow-sm border border-gray-100">
      <h3 class="text-lg font-bold text-gray-800 mb-6">修改密码</h3>

      <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-position="top" class="max-w-md">
        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="请输入原密码" size="large" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="至少8位字符" size="large" />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm_password">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password placeholder="再次输入新密码" size="large" />
        </el-form-item>
        <el-button type="primary" size="large" class="!rounded-xl !px-8" :loading="changing" @click="handleChangePassword">
          确认修改
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const profile = reactive({
  username: '', email: '', role: 'USER', status: 1, created_at: null,
})

const changing = ref(false)
const passwordFormRef = ref()
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const validateConfirm = (_rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码至少8位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

const roleLabel = (r) => ({ USER: '普通用户', ADMIN: '管理员', SUPER_ADMIN: '超级管理员' }[r] || r)
const roleTagType = (r) => ({ USER: 'info', ADMIN: 'warning', SUPER_ADMIN: 'danger' }[r] || 'info')
const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'

const fetchProfile = async () => {
  try {
    const res = await request.get('/api/v1/profile')
    if (res?.data?.code === 200) {
      Object.assign(profile, res.data.data)
    }
  } catch { /* ignore */ }
}

const handleChangePassword = async () => {
  try {
    await passwordFormRef.value.validate()
  } catch { return }

  changing.value = true
  try {
    await request.put('/api/v1/profile/password', {
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    setTimeout(() => {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }, 1500)
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '密码修改失败')
  } finally {
    changing.value = false
  }
}

onMounted(() => fetchProfile())
</script>
