<script setup lang="ts">
withDefaults(defineProps<{ size?: number; alt?: string }>(), {
  size: 40,
  alt: 'Advertly logo',
})

const logoUrl = `${import.meta.env.BASE_URL}advertly-logo.png`
</script>

<template>
  <img
    :src="logoUrl"
    :alt="alt"
    :width="size"
    :height="size"
    class="shrink-0 object-contain"
    decoding="async"
    draggable="false"
  />
</template>
