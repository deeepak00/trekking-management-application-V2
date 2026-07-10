<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4 pb-2 border-bottom border-dark flex-wrap gap-3">
      <h2 class="fw-bold mb-0">Manage Trekkers</h2>
    </div>

    <!-- Filter Bar -->
    <div class="card border-dark shadow-sm mb-4">
      <div class="card-body p-3">
        <div class="row g-3">
          <div class="col-md-8">
            <input 
              v-model="search" 
              type="text" 
              class="form-control border-dark"
              placeholder="Search trekkers by name, username, email..." 
              @input="debounceSearch"
            />
          </div>
          <div class="col-md-4">
            <select v-model="filterStatus" class="form-select border-dark">
              <option value="">All Accounts</option>
              <option value="active">Active Only</option>
              <option value="inactive">Inactive Only</option>
              <option value="blacklisted">Blacklisted Only</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-dark" role="status"></div>
    </div>
    <div v-else>
      <div v-if="!users.length" class="card border-dark text-center p-5">
        <p class="text-muted mb-0">No trekkers found matching filters.</p>
      </div>
      
      <div v-else class="card border-dark shadow-sm p-4">
        <div class="table-responsive" style="max-height: 350px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 4px;">
          <table class="table table-hover table-sm align-middle mb-0" style="table-layout: fixed; width: 100%; font-size: 0.9rem;">
            <colgroup>
              <col style="width: 20%;">
              <col style="width: 15%;">
              <col style="width: 25%;">
              <col style="width: 15%;">
              <col style="width: 10%;">
              <col style="width: 10%;">
              <col style="width: 15%;">
            </colgroup>
            <thead>
              <tr style="border-bottom: 2px solid #000;">
                <th class="fw-bold">Name</th>
                <th class="fw-bold">Username</th>
                <th class="fw-bold">Email</th>
                <th class="fw-bold">Phone</th>
                <th class="fw-bold">Bookings</th>
                <th class="fw-bold">Blacklisted</th>
                <th class="fw-bold">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in users" :key="u.id">
                <td class="fw-bold text-break">{{ u.name }}</td>
                <td class="text-break">@{{ u.username }}</td>
                <td class="text-break">{{ u.email }}</td>
                <td class="text-break">{{ u.phone || '—' }}</td>
                <td>{{ u.booking_count }}</td>
                <td>
                  <span class="badge bg-dark text-white">
                    {{ u.status === 'blacklisted' ? 'Yes' : 'No' }}
                  </span>
                </td>
                <td>
                  <div class="d-flex gap-1 flex-wrap">
                    <button @click="blacklist(u)" class="btn btn-outline-dark btn-sm fw-bold">
                      {{ u.status === 'blacklisted' ? 'Unblacklist' : 'Blacklist' }}
                    </button>
                    <button @click="del(u)" class="btn btn-outline-danger btn-sm fw-bold">Delete</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ManageUsers',
  data() {
    return {
      users: [],
      loading: true,
      search: '',
      filterStatus: '',
      _searchTimer: null
    };
  },
  mounted() {
    this.load();
  },
  beforeDestroy() {
    clearTimeout(this._searchTimer);
  },
  watch: {
    filterStatus() {
      this.load();
    }
  },
  methods: {
    async load() {
      this.loading = true;
      try {
        let url = '/admin/users?role=user';
        if (this.search) url += '&q=' + encodeURIComponent(this.search);
        if (this.filterStatus) url += '&status=' + this.filterStatus;
        this.users = await this.$api.get(url);
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.loading = false;
      }
    },
    debounceSearch() {
      clearTimeout(this._searchTimer);
      this._searchTimer = setTimeout(() => {
        this.load();
      }, 450);
    },
    async toggle(u) {
      try {
        await this.$api.put('/admin/users/' + u.id + '/status', { is_active: !u.is_active });
        this.$root.toast('User active status updated');
        await this.load();
      } catch (e) {
        this.$root.toast(e.message, 'error');
      }
    },
    async blacklist(u) {
      const isBlack = u.status === 'blacklisted';
      const act = isBlack ? 'Unblacklist' : 'Blacklist';
      if (!confirm(`${act} user "${u.name}"?`)) return;
      try {
        const nextStatus = isBlack ? 'active' : 'blacklisted';
        await this.$api.put('/admin/users/' + u.id + '/status', { status: nextStatus });
        this.$root.toast('User blacklist status updated');
        await this.load();
      } catch (e) {
        this.$root.toast(e.message, 'error');
      }
    },
    async del(u) {
      if (!confirm(`Permanently delete user "${u.name}"? This cannot be undone.`)) return;
      try {
        await this.$api.delete('/admin/users/' + u.id);
        this.$root.toast('User deleted');
        await this.load();
      } catch (e) {
        this.$root.toast(e.message, 'error');
      }
    }
  }
};
</script>
