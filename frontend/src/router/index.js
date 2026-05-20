import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import request from '../utils/request'

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
          component: () => import('../views/ImageExtract.vue'),
          meta: { title: '图像水印提取' }
        },
        {
          path: 'pointcloud-wm/embed',
          name: 'pointcloud-embed',
          component: () => import('../views/PointcloudEmbed.vue'),
          meta: { title: '点云水印嵌入' }
        },
        {
          path: 'pointcloud-wm/extract',
          name: 'pointcloud-extract',
          component: () => import('../views/PointcloudExtract.vue'),
          meta: { title: '点云水印提取' }
        },
        {
          path: 'mesh-wm/embed',
          name: 'mesh-embed',
          component: () => import('../views/MeshEmbed.vue'),
          meta: { title: '网格水印嵌入' }
        },
        {
          path: 'mesh-wm/extract',
          name: 'mesh-extract',
          component: () => import('../views/MeshExtract.vue'),
          meta: { title: '网格水印提取' }
        },
        {
          path: 'gs-wm/embed',
          name: 'gs-embed',
          component: () => import('../views/GsEmbed.vue'),
          meta: { title: '3DGS水印嵌入' }
        },
        {
          path: 'gs-wm/extract',
          name: 'gs-extract',
          component: () => import('../views/GsExtract.vue'),
          meta: { title: '3DGS水印提取' }
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

const WHITE_LIST = ['/login', '/register']

router.beforeEach(async (to) => {
  const token = localStorage.getItem('token')

  if (WHITE_LIST.includes(to.path)) {
    if (token && to.path === '/login') {
      return '/dashboard'
    }
    return true
  }

  if (!token) {
    return '/login'
  }

  try {
    const response = await request.post('/api/v1/auth/verify-token')
    if (response?.data?.data?.valid) {
      return true
    }
  } catch (error) {
    // ignore and fallback to re-login
  }

  localStorage.removeItem('token')
  localStorage.removeItem('user')
  return '/login'
})

export default router
