<template>
  <div>
    <!-- Render Navbar if route is not guest-only (like login/register) -->
    <Navbar v-if="showNavbar" />
    
    <main class="container">
      <router-view></router-view>
    </main>

    <!-- Toast Notifications overlay -->
    <div class="tma-toast-container">
      <div 
        v-for="t in $root.toasts" 
        :key="t.id" 
        class="tma-toast" 
        :class="t.type"
      >
        <span v-if="t.type === 'error'">❌</span>
        <span v-else-if="t.type === 'warning'">⚠️</span>
        <span v-else>✅</span>
        <span>{{ t.message }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import Navbar from '@/views/Navbar.vue';

export default {
  name: 'App',
  components: {
    Navbar,
  },
  computed: {
    showNavbar() {
      // Don't show navbar on login/register pages
      return this.$route.path !== '/login' && this.$route.path !== '/register';
    }
  }
};
</script>
