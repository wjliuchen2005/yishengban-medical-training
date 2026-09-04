<template>
  <router-view />
  <PageGuide v-if="!route.meta.immersiveAvatar" />
</template>

<script setup>
import { useRoute } from 'vue-router'
import PageGuide from '@/components/PageGuide.vue'

const route = useRoute()
</script>

<style lang="scss">
#app {
  min-height: 100vh;
}
</style>
