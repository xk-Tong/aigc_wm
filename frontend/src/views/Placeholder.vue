<template>
  <el-card shadow="never" class="border-none rounded-xl min-h-[60vh] flex flex-col items-center justify-center">
    <el-empty :description="`正在开发中: ${$route.meta.title || $route.name}`">
      <template #image>
        <el-icon :size="64" class="text-gray-300"><Tools /></el-icon>
      </template>
      <el-button type="primary" @click="$router.push('/dashboard')">返回总览</el-button>
    </el-empty>
  </el-card>
</template>

<script setup lang="ts">
// Placeholder view for unimplemented routes
</script>
