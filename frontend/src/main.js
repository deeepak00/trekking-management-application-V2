import Vue from 'vue';
import App from './App.vue';
import router from './router';
import $api from './utils/api';
import 'bootstrap/dist/css/bootstrap.min.css';
import './style.css';

// Mount $api on the Vue prototype for global access as this.$api
Vue.prototype.$api = $api;

new Vue({
  router,
  data() {
    return {
      toasts: [],
      currentUser: JSON.parse(localStorage.getItem('tma_user') || 'null'),
    };
  },
  methods: {
    toast(msg, type = 'success') {
      const id = Date.now();
      this.toasts.push({ id, message: msg, type });
      setTimeout(() => {
        this.toasts = this.toasts.filter(t => t.id !== id);
      }, 3500);
    },
    setUser(u) {
      this.currentUser = u;
      if (u) localStorage.setItem('tma_user', JSON.stringify(u));
      else localStorage.removeItem('tma_user');
    },
    logout() {
      localStorage.removeItem('tma_token');
      localStorage.removeItem('tma_user');
      this.currentUser = null;
      this.$router.push('/login').catch(() => {});
    },
  },
  render: (h) => h(App),
}).$mount('#app');

// Register Service Worker for PWA Add to Home Screen support
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((reg) => {
        console.log('[TMA] Service Worker registered:', reg.scope);
      })
      .catch((err) => {
        console.error('[TMA] Service Worker registration failed:', err);
      });
  });
}
