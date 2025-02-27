import { createRouter, createWebHistory } from 'vue-router'

const Layout = () => import('@/layout/index.vue')

const routes = [
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '仪表盘', icon: 'Odometer' }
      }
    ]
  },
  {
    path: '/proxy',
    component: Layout,
    redirect: '/proxy/list',
    meta: { title: '代理管理', icon: 'Connection' },
    children: [
      {
        path: 'list',
        name: 'ProxyList',
        component: () => import('@/views/proxy/list.vue'),
        meta: { title: '代理节点列表' }
      },
      {
        path: 'create',
        name: 'ProxyCreate',
        component: () => import('@/views/proxy/create.vue'),
        meta: { title: '添加代理节点' }
      }
    ]
  },
  {
    path: '/settings',
    component: Layout,
    redirect: '/settings/schedule',
    meta: { title: '系统设置', icon: 'Setting' },
    children: [
      {
        path: 'schedule',
        name: 'ScheduleSettings',
        component: () => import('@/views/settings/schedule.vue'),
        meta: { title: '调度策略配置' }
      },
      {
        path: 'health',
        name: 'HealthSettings',
        component: () => import('@/views/settings/health.vue'),
        meta: { title: '健康检查配置' }
      }
    ]
  },
  {
    path: '/statistics',
    component: Layout,
    redirect: '/statistics/traffic',
    meta: { title: '统计分析', icon: 'DataAnalysis' },
    children: [
      {
        path: 'traffic',
        name: 'TrafficStatistics',
        component: () => import('@/views/statistics/traffic.vue'),
        meta: { title: '流量统计' }
      }
    ]
  },
  {
    path: '/logs',
    component: Layout,
    children: [
      {
        path: '',
        name: 'Logs',
        component: () => import('@/views/logs/index.vue'),
        meta: { title: '系统日志', icon: 'Document' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
