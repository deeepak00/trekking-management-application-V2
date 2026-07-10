<template>
  <div class="container py-4">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-dark" role="status">
        <span class="visually-hidden">Loading Dashboard...</span>
      </div>
    </div>
    
    <div v-else-if="stats">
      <!-- Title area -->
      <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center mb-4 pb-2 border-bottom border-dark">
        <div class="mb-3 mb-md-0">
          <h2 class="fw-bold mb-1">Admin Dashboard</h2>
          <p class="text-muted small mb-0">Real-time platform overview</p>
        </div>
        <div class="d-flex gap-2">
          <router-link :to="{ path: '/admin/treks', query: { action: 'new' } }" class="btn btn-outline-dark fw-bold">+ New Trek</router-link>
          <router-link :to="{ path: '/admin/staff', query: { action: 'new' } }" class="btn btn-outline-dark fw-bold">+ Add Staff</router-link>
        </div>
      </div>

      <!-- Global Search -->
      <div class="card border-dark shadow-sm mb-4">
        <div class="card-body p-4">
          <h4 class="fw-bold mb-3">Global Search</h4>
          <div class="d-flex gap-2 w-100">
            <input 
              v-model="searchQ" 
              type="text" 
              class="form-control border-dark"
              placeholder="Search treks, users, staff..." 
              style="flex: 1;"
            />
            <button v-if="searchQ" @click="clearSearch" class="btn btn-outline-dark py-1 px-3">Clear</button>
          </div>
          
          <!-- Search Results Dropdown -->
          <div v-if="searchRes" class="mt-3 pt-3 border-top border-secondary" style="border-top-style: dashed !important;">
            <div v-if="!hasResults" class="text-muted text-center py-2">No results for "{{ searchQ }}"</div>
            <div v-else>
              <div class="fw-bold mb-2">{{ totalResults }} results for "{{ searchQ }}"</div>
              
              <!-- Treks -->
              <div v-if="searchRes.treks.length" class="mb-3">
                <div class="fw-bold text-muted mb-1" style="font-size: 0.9rem;">TREKS</div>
                <div v-for="t in searchRes.treks" :key="'t'+t.id" class="d-flex justify-content-between align-items-center p-2 mb-2 border border-dark rounded bg-light">
                  <span>{{ t.name }} ({{ t.location }})</span>
                  <div class="d-flex gap-2 align-items-center">
                    <span class="badge bg-dark">{{ t.difficulty }}</span>
                    <span class="badge bg-secondary text-dark border border-dark">{{ t.status }}</span>
                    <router-link to="/admin/treks" class="text-dark fw-bold text-decoration-underline ms-2" style="font-size: 0.95rem;">Edit</router-link>
                  </div>
                </div>
              </div>

              <!-- Users -->
              <div v-if="searchRes.users.length" class="mb-3">
                <div class="fw-bold text-muted mb-1" style="font-size: 0.9rem;">TREKKERS</div>
                <div v-for="u in searchRes.users" :key="'u'+u.id" class="d-flex justify-content-between align-items-center p-2 mb-2 border border-dark rounded bg-light">
                  <span>{{ u.name }} (@{{ u.username }} · {{ u.email }})</span>
                  <div class="d-flex gap-2 align-items-center">
                    <span class="badge bg-secondary text-dark border border-dark">{{ u.status }}</span>
                    <router-link to="/admin/users" class="text-dark fw-bold text-decoration-underline ms-2" style="font-size: 0.95rem;">View</router-link>
                  </div>
                </div>
              </div>

              <!-- Staff -->
              <div v-if="searchRes.staff.length" class="mb-3">
                <div class="fw-bold text-muted mb-1" style="font-size: 0.9rem;">STAFF</div>
                <div v-for="s in searchRes.staff" :key="'s'+s.id" class="d-flex justify-content-between align-items-center p-2 mb-2 border border-dark rounded bg-light">
                  <span>{{ s.name }} ({{ s.staff_info ? s.staff_info.specialization : 'Guide' }})</span>
                  <div class="d-flex gap-2 align-items-center">
                    <span class="badge bg-secondary text-dark border border-dark">{{ s.status }}</span>
                    <router-link to="/admin/staff" class="text-dark fw-bold text-decoration-underline ms-2" style="font-size: 0.95rem;">Edit</router-link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Stats Cards Grid -->
      <div class="row mb-4 g-3">
        <div 
          v-for="s in [
            { val: stats.total_treks, label: 'Total Treks' },
            { val: stats.total_users, label: 'Trekkers' },
            { val: stats.total_staff, label: 'Staff' },
            { val: stats.total_bookings, label: 'Bookings' },
            { val: stats.active_bookings, label: 'Active' },
            { val: '₹' + Math.round((stats.total_revenue || 0) / 1000) + 'K', label: 'Revenue' }
          ]" 
          :key="s.label"
          class="col-6 col-md-4 col-lg-2"
        >
          <div class="card border-dark text-center py-3 shadow-sm">
            <div class="text-muted small fw-bold">{{ s.label }}</div>
            <h2 class="fw-bold text-dark mt-1 mb-0">{{ s.val }}</h2>
          </div>
        </div>
      </div>

      <!-- Charts Grid -->
      <div class="row mb-4 g-4">
        <div class="col-md-6">
          <div class="card border-dark shadow-sm p-3 h-100">
            <h4 class="fw-bold mb-3">Trek Status Distribution</h4>
            <div style="height: 220px; position: relative;">
              <canvas id="statusChart"></canvas>
            </div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card border-dark shadow-sm p-3 h-100">
            <h4 class="fw-bold mb-3">Bookings by Difficulty</h4>
            <div style="height: 220px; position: relative;">
              <canvas id="diffChart"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- Monthly Booking Chart -->
      <div class="card border-dark shadow-sm mb-4">
        <div class="card-body p-3">
          <h4 class="fw-bold mb-3">Monthly Bookings & Revenue</h4>
          <div style="height: 240px; position: relative;">
            <canvas id="monthlyChart"></canvas>
          </div>
        </div>
      </div>

      <!-- Most Booked Treks -->
      <div class="card border-dark shadow-sm p-4">
        <h4 class="fw-bold mb-3">Most Booked Treks</h4>
        <div v-if="!stats.popular_treks.length" class="text-muted small">No booking data yet.</div>
        <div v-else class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead>
              <tr style="border-bottom: 2px solid #000;">
                <th class="fw-bold">Trek Name</th>
                <th class="fw-bold">Location</th>
                <th class="fw-bold">Guide</th>
                <th class="fw-bold">Difficulty</th>
                <th class="fw-bold">Bookings</th>
                <th class="fw-bold">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in stats.popular_treks" :key="item.trek.id">
                <td class="fw-bold">{{ item.trek.name }}</td>
                <td>{{ item.trek.location }}</td>
                <td>{{ item.trek.staff_name || 'TBD' }}</td>
                <td><span class="badge bg-dark">{{ item.trek.difficulty }}</span></td>
                <td><span class="badge bg-secondary text-dark border border-dark">{{ item.bookings }}</span></td>
                <td><span class="badge bg-secondary text-dark border border-dark">{{ item.trek.status }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Chart from 'chart.js/auto';

export default {
  name: 'AdminDashboard',
  data() {
    return {
      stats: null,
      loading: true,
      searchQ: '',
      searchRes: null,
      searching: false,
      _sT: null,
      chartInstances: [],
    };
  },
  mounted() {
    this.init();
  },
  beforeDestroy() {
    clearTimeout(this._sT);
    this.destroyCharts();
  },
  watch: {
    searchQ(v) {
      clearTimeout(this._sT);
      if (!v || v.length < 2) {
        this.searchRes = null;
        return;
      }
      this.searching = true;
      this._sT = setTimeout(async () => {
        try {
          this.searchRes = await this.$api.get('/admin/search?q=' + encodeURIComponent(v));
        } catch (e) {
          this.$root.toast(e.message, 'error');
        } finally {
          this.searching = false;
        }
      }, 400);
    },
  },
  computed: {
    hasResults() {
      return (
        this.searchRes &&
        (this.searchRes.treks.length ||
          this.searchRes.users.length ||
          this.searchRes.staff.length)
      );
    },
    totalResults() {
      if (!this.searchRes) return 0;
      return this.searchRes.treks.length + this.searchRes.users.length + this.searchRes.staff.length;
    },
  },
  methods: {
    async init() {
      this.loading = true;
      try {
        const [dashRes, statsRes] = await Promise.all([
          this.$api.get('/admin/dashboard'),
          this.$api.get('/admin/stats')
        ]);
        this.stats = dashRes;
        this.loading = false;
        this.$nextTick(() => {
          this.renderCharts(dashRes, statsRes);
        });
      } catch (e) {
        this.loading = false;
        this.$root.toast(e.message, 'error');
      }
    },
    clearSearch() {
      this.searchQ = '';
      this.searchRes = null;
    },
    destroyCharts() {
      this.chartInstances.forEach(c => c.destroy());
      this.chartInstances = [];
    },
    renderCharts(dash, st) {
      this.destroyCharts();
      
      const pieCtx = document.getElementById('statusChart');
      if (pieCtx && dash.trek_stats) {
        const labels = Object.keys(dash.trek_stats).filter(k => dash.trek_stats[k] > 0);
        const vals = labels.map(k => dash.trek_stats[k]);
        
        const c = new Chart(pieCtx, {
          type: 'doughnut',
          data: {
            labels: labels,
            datasets: [{
              data: vals,
              backgroundColor: ['#1c1917', '#44403c', '#78716c', '#a8a29e', '#d6d3d1', '#e7e5e4'],
              borderWidth: 1,
              borderColor: '#ffffff'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false
          }
        });
        this.chartInstances.push(c);
      }

      const diffCtx = document.getElementById('diffChart');
      if (diffCtx && st.difficulty_stats && st.difficulty_stats.length) {
        const c = new Chart(diffCtx, {
          type: 'pie',
          data: {
            labels: st.difficulty_stats.map(d => d.difficulty),
            datasets: [{
              data: st.difficulty_stats.map(d => d.bookings),
              backgroundColor: ['#1c1917', '#78716c', '#d6d3d1'],
              borderWidth: 1,
              borderColor: '#ffffff'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false
          }
        });
        this.chartInstances.push(c);
      }

      const barCtx = document.getElementById('monthlyChart');
      if (barCtx && st.monthly_stats && st.monthly_stats.length) {
        const c = new Chart(barCtx, {
          type: 'bar',
          data: {
            labels: st.monthly_stats.map(m => m.month),
            datasets: [
              {
                label: 'Bookings',
                data: st.monthly_stats.map(m => m.count),
                backgroundColor: '#1c1917',
                borderWidth: 1,
                borderColor: '#ffffff',
                yAxisID: 'y'
              },
              {
                label: 'Revenue (₹)',
                data: st.monthly_stats.map(m => m.revenue),
                backgroundColor: '#e7e5e4',
                borderWidth: 1,
                borderColor: '#78716c',
                yAxisID: 'y1'
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: { beginAtZero: true, position: 'left' },
              y1: { beginAtZero: true, position: 'right', grid: { drawOnChartArea: false } }
            }
          }
        });
        this.chartInstances.push(c);
      }
    }
  }
};
</script>
