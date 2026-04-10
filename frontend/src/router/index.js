import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue')
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/Register.vue')
    },
    {
      path: '/',
      component: MainLayout,
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('../views/Dashboard.vue'),
          meta: { title: '系统总览' }
        },
        {
          path: 'image-wm/embed',
          name: 'image-embed',
          component: () => import('../views/ImageEmbed.vue'),
          meta: { title: '图像水印嵌入' }
        },
        {
          path: 'image-wm/extract',
          name: 'image-extract',
          component: () => import('../views/Placeholder.vue'),
          meta: { title: '图像水印提取' }
        },
        {
          path: 'pointcloud-wm/embed',
          name: 'pointcloud-embed',
          component: () => import('../views/Placeholder.vue'),
          meta: { title: '点云水印嵌入' }
        },
        {
          path: 'pointcloud-wm/extract',
          name: 'pointcloud-extract',
          component: () => import('../views/Placeholder.vue'),
          meta: { title: '点云水印提取' }
        },
        {
          path: 'mesh-wm/embed',
          name: 'mesh-embed',
          component: () => import('../views/Placeholder.vue'),
          meta: { title: '网格水印嵌入' }
        },
        {
          path: 'mesh-wm/extract',
          name: 'mesh-extract',
          component: () => import('../views/Placeholder.vue'),
          meta: { title: '网格水印提取' }
        },
        {
          path: 'tracing',
          name: 'tracing',
          component: () => import('../views/Placeholder.vue'),
          meta: { title: '溯源验真' }
        },
        {
          path: 'data/registry',
          name: 'data-registry',
          component: () => import('../views/Placeholder.vue'),
          meta: { title: '水印注册库' }
        },
        {
          path: 'data/logs',
          name: 'data-logs',
          component: () => import('../views/Placeholder.vue'),
          meta: { title: '操作日志' }
        },
        {
          path: 'system/users',
          name: 'system-users',
          component: () => import('../views/Placeholder.vue'),
          meta: { title: '用户管理' }
        },
        {
          path: 'system/config',
          name: 'system-config',
          component: () => import('../views/Placeholder.vue'),
          meta: { title: '系统配置' }
        }
      ]
    }
  ]
})

export default router
