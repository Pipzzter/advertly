<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { agents } from '@/types/agent'

const router = useRouter()
const isDropdownOpen = ref(false)

function selectAgent(route: string) {
  isDropdownOpen.value = false
  router.push(route)
}
</script>

<template>
  <header class="bg-slate-900 border-b border-slate-700">
    <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
      <router-link to="/" class="text-xl font-bold text-white hover:text-slate-300">
        Advertly
      </router-link>

      <div class="relative">
        <button
          @click="isDropdownOpen = !isDropdownOpen"
          class="flex items-center gap-2 px-4 py-2 bg-slate-800 text-slate-200 rounded-lg hover:bg-slate-700 transition-colors"
        >
          <span>What would you like to do?</span>
          <svg
            class="w-4 h-4 transition-transform"
            :class="{ 'rotate-180': isDropdownOpen }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <div
          v-if="isDropdownOpen"
          class="absolute right-0 mt-2 w-72 bg-slate-800 rounded-lg shadow-xl border border-slate-700 py-2 z-50"
        >
          <button
            v-for="agent in agents"
            :key="agent.id"
            @click="selectAgent(agent.route)"
            class="w-full px-4 py-3 text-left hover:bg-slate-700 transition-colors"
          >
            <div class="flex items-center gap-3">
              <span class="text-xl">{{ agent.icon }}</span>
              <div>
                <div class="text-white font-medium">{{ agent.name }}</div>
                <div class="text-slate-400 text-sm">{{ agent.description }}</div>
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>
  </header>
</template>
