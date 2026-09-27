<script setup lang="ts">
import { agents } from '@/types/agent'
</script>

<template>
  <div>
    <div class="text-center mb-12">
      <h1 class="text-4xl font-bold text-white mb-4">Advertly</h1>
      <p class="text-slate-400 text-lg max-w-2xl mx-auto">
        Turn raw marketing copy into ready-to-publish advertorial landing pages, with structured sections and contextual images generated for you.
      </p>
    </div>

    <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      <router-link
        v-for="agent in agents"
        :key="agent.id"
        :to="agent.route"
        class="bg-slate-900 rounded-xl border border-slate-800 p-6 hover:border-slate-600 transition-colors group"
      >
        <span class="text-3xl mb-4 block">{{ agent.icon }}</span>
        <h2 class="text-xl font-semibold text-white mb-2 group-hover:text-slate-200">
          {{ agent.name }}
        </h2>
        <p class="text-slate-400 text-sm">{{ agent.description }}</p>
      </router-link>
    </div>
  </div>
</template>
