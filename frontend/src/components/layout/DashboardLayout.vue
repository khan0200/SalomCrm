<script setup lang="ts">
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'
import NotificationToast from '@/components/common/NotificationToast.vue'
</script>

<template>
  <div class="flex h-screen w-screen overflow-hidden bg-zinc-50 dark:bg-zinc-950 font-sans text-zinc-900 dark:text-zinc-100">
    <AppSidebar />
    <div class="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
      <AppHeader />
      <main class="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-7">
        <router-view />
      </main>
    </div>
    <NotificationToast />
  </div>
</template>
