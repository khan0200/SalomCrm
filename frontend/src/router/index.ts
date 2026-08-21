import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import LoginPage from '@/modules/auth/LoginPage.vue'
import StudentsPage from '@/modules/students/StudentsPage.vue'
import PaymentsPage from '@/modules/payments/PaymentsPage.vue'
import StatusPage from '@/modules/status/StatusPage.vue'
import TenantsPage from '@/modules/tenants/TenantsPage.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
    meta: { public: true }
  },
  {
    path: '/',
    component: DashboardLayout,
    redirect: '/students',
    children: [
      {
        path: 'students',
        name: 'students',
        component: StudentsPage,
        meta: { title: 'Students' }
      },
      {
        path: 'students/:id/extract',
        name: 'student-extract',
        component: () => import('@/modules/students/pages/StudentExtractPage.vue'),
        meta: { title: 'Fill By Document' }
      },
      {
        path: 'payments',
        name: 'payments',
        component: PaymentsPage,
        meta: { title: 'Payments' }
      },
      {
        path: 'status',
        name: 'status',
        component: StatusPage,
        meta: { title: 'Status Board' }
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('@/modules/settings/SettingsPage.vue'),
        meta: { title: 'Settings' }
      },
      {
        path: 'tenants',
        name: 'tenants',
        component: TenantsPage,
        meta: { title: 'Tenants Management', superAdminOnly: true }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/students'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (!to.meta.public && !authStore.isAuthenticated) {
    next({ name: 'login' })
  } else if (to.name === 'login' && authStore.isAuthenticated) {
    next({ name: 'students' })
  } else if (to.meta.superAdminOnly && !authStore.isSuperAdmin) {
    next({ name: 'students' })
  } else {
    next()
  }
})

export default router
