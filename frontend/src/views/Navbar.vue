<template>
  <nav class="navbar navbar-expand-lg navbar-light bg-white border-bottom border-dark px-3 py-2">
    <div class="container-fluid d-flex justify-content-between align-items-center">
      <!-- Logo -->
      <router-link to="/" class="navbar-brand fw-bold text-dark fs-4">
        TMA
      </router-link>
      
      <div class="d-flex align-items-center gap-3">
        <!-- Navigation Links -->
        <div class="navbar-nav d-flex flex-row gap-3" v-if="user">
          <router-link 
            v-for="l in links" 
            :key="l.to" 
            :to="l.to" 
            class="nav-link text-dark fw-semibold"
            active-class="border-bottom border-dark"
          >
            {{ l.label }}
          </router-link>
        </div>

        <div class="d-flex align-items-center gap-3" v-if="user">
          <!-- Notification Dropdown -->
          <div v-if="user.role === 'user'" class="position-relative">
            <button @click="toggleNotifs" class="btn btn-outline-dark btn-sm fw-bold">
              Alerts <span v-if="unread > 0" class="badge bg-danger ms-1">{{ unread }}</span>
            </button>
            
            <div v-if="open" class="position-absolute bg-white border border-dark rounded p-3 shadow" style="right: 0; top: 120%; width: 320px; z-index: 1000;">
              <div class="d-flex justify-content-between align-items-center mb-2 pb-1 border-bottom border-dark">
                <span class="fw-bold">Alerts</span>
                <div class="d-flex gap-2">
                  <button @click="markAll" class="btn btn-dark btn-xs py-0 px-1" style="font-size: 0.75rem;">Mark Read</button>
                  <button @click="open = false" class="btn btn-outline-dark btn-xs py-0 px-1" style="font-size: 0.75rem;">Close</button>
                </div>
              </div>
              <div v-if="!notifs.length" class="text-muted text-center py-2" style="font-size: 0.9rem;">No alerts</div>
              <div 
                v-for="n in notifs" 
                :key="n.id" 
                class="p-2 mb-2 border border-secondary rounded" 
                :style="{ backgroundColor: n.is_read ? '#ffffff' : '#fffbeb' }"
                style="font-size: 0.85rem;"
              >
                <div class="fw-bold text-dark">{{ n.title }}</div>
                <div class="text-muted">{{ n.message }}</div>
              </div>
            </div>
          </div>

          <!-- Role Badge -->
          <span class="badge bg-dark text-white uppercase">{{ user.role }}</span>
          
          <!-- Profile Link -->
          <router-link to="/profile" class="nav-link text-dark fw-bold">
            Profile ({{ user.name.split(' ')[0] }})
          </router-link>
          
          <!-- Logout Button -->
          <button @click="$root.logout()" class="btn btn-dark btn-sm fw-bold">
            Logout
          </button>
        </div>
        
        <!-- Guest Links -->
        <div class="navbar-nav d-flex flex-row gap-3" v-else>
          <router-link to="/login" class="nav-link text-dark fw-semibold">Login</router-link>
          <router-link to="/register" class="nav-link text-dark fw-semibold">Register</router-link>
        </div>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'Navbar',
  data() {
    return {
      unread: 0,
      notifs: [],
      open: false,
      _timer: null,
    };
  },
  computed: {
    user() {
      return this.$root.currentUser;
    },
    links() {
      if (!this.user) return [];
      if (this.user.role === 'admin') {
        return [
          { to: '/admin/dashboard', label: 'Dashboard' },
          { to: '/admin/treks',     label: 'Treks' },
          { to: '/admin/staff',     label: 'Staff' },
          { to: '/admin/users',     label: 'Users' },
          { to: '/admin/bookings',  label: 'Bookings' },
        ];
      }
      if (this.user.role === 'staff') {
        return [
          { to: '/staff/dashboard', label: 'Dashboard' },
        ];
      }
      return [
        { to: '/treks',    label: 'Browse Treks' },
        { to: '/dashboard',label: 'Dashboard' },
        { to: '/bookings', label: 'My Bookings' },
        { to: '/wishlist', label: 'Wishlist' },
      ];
    }
  },
  mounted() {
    this.boundRefresh = this.onRefreshNotifications.bind(this);
    this.$root.$on('refresh-notifications', this.boundRefresh);

    if (this.user && this.user.role === 'user') {
      this.fetchNotifs();
      this._timer = setInterval(() => {
        this.fetchNotifs();
      }, 30000);
    }
  },
  beforeDestroy() {
    if (this._timer) clearInterval(this._timer);
    this.$root.$off('refresh-notifications', this.boundRefresh);
  },
  methods: {
    onRefreshNotifications() {
      if (this.user && this.user.role === 'user') {
        this.fetchNotifs();
      }
    },
    async fetchNotifs() {
      try {
        const d = await this.$api.get('/notifications?_t=' + Date.now());
        this.unread = d.unread;
        this.notifs = d.notifications.slice(0, 6);
      } catch (e) {}
    },
    toggleNotifs() {
      this.open = !this.open;
      if (this.open) this.fetchNotifs();
    },
    async markAll() {
      try {
        await this.$api.put('/notifications/read-all', {});
        this.unread = 0;
        this.notifs.forEach(n => { n.is_read = true; });
      } catch (e) {}
    }
  }
};
</script>
