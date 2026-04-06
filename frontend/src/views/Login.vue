<template>
  <div class="min-h-screen flex items-center justify-center relative overflow-hidden bg-[#f4f6f8]">
    <!-- 装饰背景图案 -->
    <div class="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-400/20 rounded-full blur-[100px]"></div>
    <div class="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-400/20 rounded-full blur-[100px]"></div>

    <!-- 登录卡片 -->
    <div class="relative z-10 w-full max-w-[420px] p-10 rounded-3xl bg-white/80 backdrop-blur-xl shadow-xl shadow-gray-200/50 border border-white">
      
      <!-- Logo & 标题 -->
      <div class="text-center mb-10 flex flex-col items-center">
        <div class="w-16 h-16 rounded-2xl bg-blue-500 flex items-center justify-center mb-4 shadow-lg shadow-blue-500/30">
          <el-icon class="text-3xl text-white"><Connection /></el-icon>
        </div>
        <h1 class="text-2xl font-bold text-gray-800 tracking-wider">AIGC WM</h1>
        <p class="text-gray-500 mt-2 text-sm">数字水印溯源验真系统</p>
      </div>
      
      <!-- 表单 -->
      <el-form :model="form" @submit.prevent="handleLogin" class="space-y-5">
        <div class="space-y-1.5">
          <label class="text-xs font-medium text-gray-500 ml-1">电子邮箱 / 用户名</label>
          <el-input 
            v-model="form.username" 
            placeholder="admin@example.com" 
            size="large"
            class="custom-input"
          />
        </div>
        
        <div class="space-y-1.5">
          <label class="text-xs font-medium text-gray-500 ml-1">密码</label>
          <el-input 
            v-model="form.password" 
            type="password" 
            placeholder="••••••••" 
            size="large"
            show-password
            class="custom-input"
          />
        </div>
        
        <div class="flex items-center justify-end text-sm pt-1">
          <a href="#" class="text-gray-500 hover:text-blue-600 transition-colors">忘记密码？</a>
        </div>
        
        <el-button 
          type="primary" 
          class="w-full !h-12 !text-base !rounded-xl !mt-4 shadow-lg shadow-blue-500/30 transition-all" 
          @click="handleLogin"
          :loading="loading"
        >
          <el-icon class="mr-2"><Right /></el-icon> 登录账号
        </el-button>
      </el-form>

      <div class="mt-8 text-center text-sm text-gray-500">
        还没有账号？ 
        <router-link to="/register" class="text-blue-600 font-medium hover:text-blue-700 transition-colors">注册一个</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  
  loading.value = true
  try {
    const response = await axios.post('http://localhost:8000/api/v1/auth/login', {
      username: form.username,
      password: form.password
    })
    
    if (response.data.code === 200) {
      ElMessage.success('登录成功')
      
      // 保存 token 和用户信息到 localStorage
      localStorage.setItem('token', response.data.data.accessToken)
      localStorage.setItem('user', JSON.stringify(response.data.data.user))
      
      router.push('/dashboard')
    } else {
      // 后端返回的业务错误 (如：用户名密码错误)
      ElMessage.error(response.data.message || '登录失败')
    }
  } catch (error) {
    ElMessage.error('网络请求失败，请检查服务是否启动')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 自定义输入框样式以匹配轻量化风格 */
:deep(.custom-input .el-input__wrapper) {
  background-color: #f8fafc;
  border-radius: 0.75rem;
  box-shadow: none;
  border: 1px solid #e2e8f0;
  padding: 4px 15px;
  transition: all 0.2s ease;
}
:deep(.custom-input .el-input__wrapper:hover) {
  border-color: #cbd5e1;
}
:deep(.custom-input .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
  background-color: #ffffff;
}
</style>
