<template>
  <div class="mt-8 recent-records-panel">
    <!-- 自定义面板头部（不使用 el-collapse，改为自定义手风琴） -->
    <div class="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden transition-all duration-300"
         :class="{ 'shadow-md': isExpanded }">

      <!-- 面板头部 -->
      <button
        @click="isExpanded = !isExpanded"
        class="w-full flex items-center justify-between px-7 py-5 cursor-pointer transition-colors duration-200 hover:bg-gray-50/60 group"
      >
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-300"
               :class="themeClasses.iconBg">
            <el-icon class="text-base" :class="themeClasses.iconColor">
              <Clock />
            </el-icon>
          </div>
          <div class="text-left">
            <h3 class="text-[15px] font-semibold text-gray-800 tracking-tight leading-tight">近期记录</h3>
            <p class="text-xs text-gray-400 mt-0.5 font-medium">{{ subtitle }}</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <span v-if="records.length > 0" class="text-xs font-semibold px-2.5 py-1 rounded-full transition-colors"
                :class="themeClasses.badge">
            {{ records.length }} 条记录
          </span>
          <div class="w-7 h-7 rounded-lg bg-gray-100 group-hover:bg-gray-200 flex items-center justify-center transition-all duration-300"
               :class="{ 'rotate-180': isExpanded }">
            <el-icon class="text-xs text-gray-500"><ArrowDown /></el-icon>
          </div>
        </div>
      </button>

      <!-- 展开内容 -->
      <transition
        @before-enter="onBeforeEnter"
        @enter="onEnter"
        @after-enter="onAfterEnter"
        @before-leave="onBeforeLeave"
        @leave="onLeave"
        @after-leave="onAfterLeave"
      >
        <div v-show="isExpanded" ref="contentRef">
          <div class="border-t border-gray-100/80">
            <!-- 空状态 -->
            <div v-if="records.length === 0" class="flex flex-col items-center justify-center py-12 px-6">
              <div class="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
                   :class="themeClasses.emptyBg">
                <el-icon class="text-2xl" :class="themeClasses.emptyIcon"><Document /></el-icon>
              </div>
              <p class="text-sm font-medium text-gray-400">暂无操作记录</p>
              <p class="text-xs text-gray-300 mt-1">完成操作后记录将显示在此处</p>
            </div>

            <!-- 记录列表 (卡片式) -->
            <div v-else class="px-5 pt-3 pb-4 space-y-2.5">
              <div
                v-for="(row, index) in records"
                :key="row.id || index"
                class="record-card group flex items-center gap-4 px-4 py-3.5 rounded-2xl border border-transparent hover:border-gray-100 hover:bg-gray-50/60 transition-all duration-200 cursor-default"
                :style="{ animationDelay: `${index * 40}ms` }"
              >
                <!-- 序号指示器 -->
                <div class="w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold shrink-0 transition-colors"
                     :class="themeClasses.indexBg">
                  {{ index + 1 }}
                </div>

                <!-- 主内容区 -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <!-- 水印值 -->
                    <span class="font-mono text-sm font-semibold text-gray-800 tracking-wider">
                      {{ getWatermarkDisplay(row) }}
                    </span>
                    <!-- 状态标签 -->
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold leading-tight"
                          :class="row.status === 'success' ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-500'">
                      <span class="w-1.5 h-1.5 rounded-full" :class="row.status === 'success' ? 'bg-emerald-400' : 'bg-red-400'"></span>
                      {{ row.status === 'success' ? '成功' : '失败' }}
                    </span>
                  </div>
                  <div class="flex items-center gap-3 text-xs text-gray-400 font-medium">
                    <span v-if="getSecondaryInfo(row)" class="truncate max-w-[160px]" :title="getSecondaryInfo(row)">
                      {{ getSecondaryInfo(row) }}
                    </span>
                    <span v-if="getSecondaryInfo(row)" class="w-0.5 h-0.5 rounded-full bg-gray-300 shrink-0"></span>
                    <span v-if="row.elapsed_ms" class="shrink-0">{{ (row.elapsed_ms / 1000).toFixed(1) }}s</span>
                    <span v-if="row.elapsed_ms" class="w-0.5 h-0.5 rounded-full bg-gray-300 shrink-0"></span>
                    <span class="shrink-0">{{ formatTime(row.created_at) }}</span>
                  </div>
                </div>

                <!-- 右侧 ID 标记 -->
                <div class="text-xs text-gray-300 font-mono shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                  #{{ row.id }}
                </div>
              </div>

              <!-- 查看全部按钮 -->
              <div class="pt-2 flex justify-center">
                <button
                  @click="$router.push('/data/history')"
                  class="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 hover:shadow-sm"
                  :class="themeClasses.viewAllBtn"
                >
                  查看全部历史
                  <el-icon class="text-sm"><ArrowRight /></el-icon>
                </button>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ArrowDown, ArrowRight, Clock, Document } from '@element-plus/icons-vue'

const props = defineProps({
  /** 记录数组 */
  records: {
    type: Array,
    default: () => [],
  },
  /** 操作类型: 'embed' | 'extract' */
  operationType: {
    type: String,
    default: 'embed',
  },
  /** 主题色: 'blue' | 'indigo' | 'teal' | 'violet' */
  themeColor: {
    type: String,
    default: 'blue',
  },
  /** 副标题 */
  subtitle: {
    type: String,
    default: '最近 5 条操作记录',
  },
})

const isExpanded = ref(false)
const contentRef = ref(null)

// 主题色映射
const themeMap = {
  blue: {
    iconBg: 'bg-blue-50',
    iconColor: 'text-blue-500',
    badge: 'bg-blue-50 text-blue-600',
    emptyBg: 'bg-blue-50/60',
    emptyIcon: 'text-blue-300',
    indexBg: 'bg-blue-50 text-blue-500',
    viewAllBtn: 'text-blue-600 bg-blue-50 hover:bg-blue-100',
  },
  indigo: {
    iconBg: 'bg-indigo-50',
    iconColor: 'text-indigo-500',
    badge: 'bg-indigo-50 text-indigo-600',
    emptyBg: 'bg-indigo-50/60',
    emptyIcon: 'text-indigo-300',
    indexBg: 'bg-indigo-50 text-indigo-500',
    viewAllBtn: 'text-indigo-600 bg-indigo-50 hover:bg-indigo-100',
  },
  teal: {
    iconBg: 'bg-teal-50',
    iconColor: 'text-teal-500',
    badge: 'bg-teal-50 text-teal-600',
    emptyBg: 'bg-teal-50/60',
    emptyIcon: 'text-teal-300',
    indexBg: 'bg-teal-50 text-teal-500',
    viewAllBtn: 'text-teal-600 bg-teal-50 hover:bg-teal-100',
  },
  violet: {
    iconBg: 'bg-violet-50',
    iconColor: 'text-violet-500',
    badge: 'bg-violet-50 text-violet-600',
    emptyBg: 'bg-violet-50/60',
    emptyIcon: 'text-violet-300',
    indexBg: 'bg-violet-50 text-violet-500',
    viewAllBtn: 'text-violet-600 bg-violet-50 hover:bg-violet-100',
  },
}

const themeClasses = computed(() => themeMap[props.themeColor] || themeMap.blue)

// 获取水印显示值
const getWatermarkDisplay = (row) => {
  if (props.operationType === 'embed') {
    return row.watermark_bits || '-'
  }
  return row.extracted_bits || '-'
}

// 获取第二行辅助信息（embed 显示模型，extract 显示文件名）
const getSecondaryInfo = (row) => {
  if (props.operationType === 'embed') {
    return row.model || null
  }
  return row.source_file_name || null
}

// 时间格式化
const formatTime = (t) => {
  if (!t) return '-'
  const d = new Date(t)
  const now = new Date()
  const diff = now - d

  // 1小时内
  if (diff < 60 * 60 * 1000) {
    const mins = Math.floor(diff / 60000)
    return mins <= 0 ? '刚刚' : `${mins} 分钟前`
  }
  // 24小时内
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    return `${hours} 小时前`
  }
  // 7天内
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = Math.floor(diff / (24 * 60 * 60 * 1000))
    return `${days} 天前`
  }
  // 超过7天显示日期
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hours}:${minutes}`
}

// 手风琴展开/收起动画（平滑高度过渡）
const onBeforeEnter = (el) => {
  el.style.height = '0'
  el.style.overflow = 'hidden'
}
const onEnter = (el) => {
  el.style.height = el.scrollHeight + 'px'
  el.style.transition = 'height 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
}
const onAfterEnter = (el) => {
  el.style.height = ''
  el.style.overflow = ''
  el.style.transition = ''
}
const onBeforeLeave = (el) => {
  el.style.height = el.scrollHeight + 'px'
  el.style.overflow = 'hidden'
}
const onLeave = (el) => {
  // 强制重绘
  void el.offsetHeight
  el.style.height = '0'
  el.style.transition = 'height 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
}
const onAfterLeave = (el) => {
  el.style.height = ''
  el.style.overflow = ''
  el.style.transition = ''
}
</script>

<style scoped>
/* 记录卡片入场动画 */
.record-card {
  animation: recordSlideIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes recordSlideIn {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 展开箭头旋转 */
.rotate-180 {
  transform: rotate(180deg);
}
</style>
