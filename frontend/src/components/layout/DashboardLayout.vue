<script setup lang="ts">
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'
import NotificationToast from '@/components/common/NotificationToast.vue'
</script>

<template>
  <div class="flex h-screen w-screen overflow-hidden bg-zinc-50 dark:bg-[#0b0d0e] font-sans text-zinc-900 dark:text-zinc-100">
    <AppSidebar />
    <div class="flex flex-1 flex-col overflow-hidden min-w-0">
      <AppHeader />
      <main class="flex-1 overflow-y-auto min-w-0" id="main-content">
        <div class="p-4 sm:p-5 lg:p-6 min-w-0">
          <router-view />
        </div>
      </main>
    </div>
    <NotificationToast />
  </div>
</template>
