<template>
  <router-view v-slot="{ Component, route }">
    <transition name="page" mode="out-in">
      <component :is="Component" :key="route.meta.transitionKey ?? route.path" />
    </transition>
  </router-view>
  <ToastHost />
</template>

<script setup lang="ts">
import ToastHost from '@/components/ToastHost.vue'
</script>
