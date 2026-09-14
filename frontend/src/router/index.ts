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
        path: 'contracts',
        name: 'contracts',
        component: () => import('@/modules/contracts/ContractsPage.vue'),
        meta: { title: 'Contracts' }
      },
      {
        path: 'payments',
        name: 'payments',
        component: PaymentsPage,
        meta: { title: 'Payments', managerOnly: true }
      },
      {
        path: 'status',
        name: 'status',
        component: StatusPage,
        meta: { title: 'Status Board' }
      },
      {
        path: 'documents',
        name: 'documents',
        component: () => import('@/modules/documents/DocumentsPage.vue'),
        meta: { title: 'Documents' }
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('@/modules/settings/SettingsPage.vue'),
        meta: { title: 'Settings', managerOnly: true }
      },
      {
        path: 'visacheck',
        name: 'visacheck',
        component: () => import('@/modules/visacheck/VisaCheckPage.vue'),
        meta: { title: 'Visa Check' }
      },
      {
        path: 'app-form',
        name: 'app-form',
        component: () => import('@/modules/app_form/AppFormPage.vue'),
        meta: { title: 'App Form', headManagerOnly: true }
      },
      // Kept so older links and bookmarks land on the matching tab.
      {
        path: 'excel-fill',
        redirect: { name: 'app-form', query: { tab: 'excel' } }
      },
      {
        path: 'word-fill',
        redirect: { name: 'app-form', query: { tab: 'word' } }
      },
      {
        path: 'tenants',
        name: 'tenants',
        component: TenantsPage,
        meta: { title: 'Tenants Management', superAdminOnly: true }
      },
      {
        path: 'staff',
        name: 'staff',
        component: () => import('@/modules/staff/StaffPage.vue'),
        meta: { title: 'Staff Management', headManagerOnly: true }
      }
    ]
  },
  // ── Online Contracts System (Multi-tenant) ─────────────────────────────────
  {
    path: '/contracts/online/:tenantname',
    name: 'online-landing',
    component: () => import('@/modules/online_contracts/pages/OnlineLandingPage.vue'),
    meta: { public: true, title: 'Onlayn Shartnomalar' }
  },
  {
    path: '/contracts/online/:tenantname/sign-up',
    name: 'online-sign-up',
    component: () => import('@/modules/online_contracts/pages/OnlineSignUpPage.vue'),
    meta: { public: true, title: "Ro'yxatdan o'tish" }
  },
  {
    path: '/contracts/online/:tenantname/sign-in',
    name: 'online-sign-in',
    component: () => import('@/modules/online_contracts/pages/OnlineSignInPage.vue'),
    meta: { public: true, title: 'Kirish' }
  },
  {
    path: '/contracts/online/:tenantname/profile',
    name: 'online-profile',
    component: () => import('@/modules/online_contracts/pages/OnlineProfilePage.vue'),
    meta: { studentOnly: true, title: 'Mening Shartnomalarim' }
  },
  {
    path: '/contracts/online/:tenantname/contracts/sign',
    name: 'online-contract-sign',
    component: () => import('@/modules/online_contracts/pages/OnlineContractSignPage.vue'),
    meta: { studentOnly: true, title: 'Shartnomani Imzolash' }
  },
  {
    path: '/contracts/online/:tenantname/contracts/:contractId/sign',
    name: 'online-contract-sign-direct',
    component: () => import('@/modules/online_contracts/pages/OnlineContractSignPage.vue'),
    meta: { studentOnly: true, title: 'Shartnomani Imzolash' }
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

  // Student portal guard
  if (to.meta.studentOnly) {
    if (!authStore.isAuthenticated) {
      next({
        name: 'online-sign-in',
        params: { tenantname: to.params.tenantname || 'unibridge' },
        query: { redirect: to.fullPath }
      })
      return
    }
    next()
    return
  }

  // Prevent student accounts from accessing internal CRM dashboards
  if (authStore.isAuthenticated && authStore.user?.role === 'STUDENT' && !to.path.startsWith('/contracts/online/')) {
    const tenantSlug = authStore.user.tenant?.slug || 'unibridge'
    next({ name: 'online-profile', params: { tenantname: tenantSlug } })
    return
  }

  if (!to.meta.public && !authStore.isAuthenticated) {
    next({ name: 'login' })
  } else if (to.name === 'login' && authStore.isAuthenticated) {
    next({ name: 'students' })
  } else if (to.meta.superAdminOnly && !authStore.isSuperAdmin) {
    next({ name: 'students' })
  } else if (to.meta.headManagerOnly && !authStore.isHeadManager) {
    next({ name: 'students' })
  } else if (to.meta.managerOnly && !authStore.isManager) {
    next({ name: 'students' })
  } else {
    next()
  }
})

export default router
