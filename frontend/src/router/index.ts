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
  // Public "check authenticity" page reached via the QR code / link printed
  // on every contract page - looks the contract up by its verification
  // code, no login required.
  {
    path: '/contracts/:code',
    name: 'contract-public-verify',
    component: () => import('@/modules/online_contracts/pages/ContractVerifyPage.vue'),
    meta: { public: true, title: 'Shartnomani tekshirish' }
  },
  // Staff-prefilled signing link (contract_sign_views.py) - no account/
  // login at all, the sign_token in the URL is the sole access key, so
  // this uses `public: true` (not `studentOnly`, which unconditionally
  // requires authStore.isAuthenticated) same as contract-public-verify
  // above. Top-level and slug-free like /contracts/:code, since the token
  // alone resolves the tenant server-side.
  {
    path: '/sign/:token',
    name: 'contract-sign-link',
    component: () => import('@/modules/online_contracts/pages/ContractSignLinkPage.vue'),
    meta: { public: true, title: 'Shartnomani imzolash' }
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
  } else if (to.meta.headManagerOnly && !authStore.isHeadManager) {
    next({ name: 'students' })
  } else if (to.meta.managerOnly && !authStore.isManager) {
    next({ name: 'students' })
  } else {
    next()
  }
})

export default router
