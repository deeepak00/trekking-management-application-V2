<template>
  <div class="container py-4">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-dark" role="status">
        <span class="visually-hidden">Loading dashboard...</span>
      </div>
    </div>
    
    <div v-else-if="dash">
      <!-- Welcome Banner (Bootstrap Card) -->
      <div class="card border-dark shadow-sm mb-4">
        <div class="card-body p-4">
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-3">
            <div>
              <h2 class="fw-bold mb-1">{{ greeting }}, {{ dash.user.name.split(' ')[0] }}!</h2>
              <p class="text-muted small mb-0">
                <span v-if="dash.user.trekker_info">
                  {{ dash.user.trekker_info.experience_level }} Trekker &middot; 
                  {{ dash.user.trekker_info.fitness_level }} Fitness Level
                </span>
                <span v-else>Welcome to TMA</span>
              </p>
            </div>
            <div class="d-flex gap-2 flex-wrap">
              <router-link to="/treks" class="btn btn-dark fw-bold">Explore Treks</router-link>
              <router-link to="/wishlist" class="btn btn-outline-dark fw-bold">Wishlist ({{ dash.wishlist_count }})</router-link>
              <button @click="exportCSV" :disabled="exporting" class="btn btn-outline-dark fw-bold">
                {{ exporting ? 'Exporting...' : 'Export Bookings' }}
              </button>
            </div>
          </div>

          <!-- Stats Grid -->
          <div class="row row-cols-2 row-cols-md-4 g-3 mt-3">
            <div 
              v-for="s in [
                { val: dash.total_bookings, label: 'Total Booked' },
                { val: dash.active_bookings, label: 'Active' },
                { val: dash.completed_bookings || 0, label: 'Completed' },
                { val: '₹' + dash.total_spent, label: 'Total Spent' }
              ]" 
              :key="s.label"
              class="col"
            >
              <div class="card border-dark h-100 text-center py-2 px-3">
                <div class="text-muted small fw-bold">{{ s.label }}</div>
                <h3 class="fw-bold text-dark mt-1 mb-0">{{ s.val }}</h3>
              </div>
            </div>
          </div>
        </div>
      </div>


      <!-- My Active Registrations -->
      <div v-if="(dash.active_boking_list && dash.active_boking_list.length) || (dash.active_bookings_list && dash.active_bookings_list.length)" class="mb-4">
        <h4 class="fw-bold mb-3">My Active Registrations</h4>
        <div class="row g-3">
          <div 
            v-for="b in (dash.active_boking_list || dash.active_bookings_list)" 
            :key="'ab'+b.id" 
            class="col-md-4"
          >
            <div class="card border-dark h-100 shadow-sm d-flex flex-column justify-content-between">
              <div class="card-body p-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <span class="fw-bold text-dark">{{ b.trek_name }}</span>
                  <span class="badge bg-dark">{{ b.status }}</span>
                </div>
                <div class="text-muted small mb-1">Location: {{ b.trek_location }}</div>
                <div class="text-muted small mb-1">Dates: {{ b.start_date || 'TBD' }} &rarr; {{ b.end_date || 'TBD' }}</div>
                <div class="text-muted small mb-2">Transaction ID: {{ b.transaction_id || '—' }}</div>

                <!-- Guide contact info -->
                <div v-if="b.staff_name && b.staff_name !== 'Unassigned'" class="small mt-2 p-2 border border-dark rounded bg-light">
                  <div class="fw-bold">Guide: {{ b.staff_name }}</div>
                  <div v-if="b.staff_phone" class="text-muted">Phone: {{ b.staff_phone }}</div>
                  <div v-if="b.staff_email" class="text-muted">Email: {{ b.staff_email }}</div>
                </div>
                <div v-else class="small text-muted mt-2">Guide: Unassigned</div>
              </div>
              <div class="card-footer bg-white border-top border-dark d-flex justify-content-between align-items-center p-3">
                <span class="fw-bold text-dark fs-5">₹{{ b.amount }}</span>
                <button @click="cancel(b.id)" class="btn btn-outline-danger btn-sm fw-bold">Cancel</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent History -->
      <div class="mb-4">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h4 class="fw-bold mb-0">Recent Booking History</h4>
          <router-link to="/bookings" class="text-dark fw-bold text-decoration-underline">View complete history &rarr;</router-link>
        </div>
        
        <div v-if="!dash.recent_bookings.length" class="card border-dark p-4 text-center text-muted">
          No booking history recorded.
        </div>
        
        <div class="row g-3" v-else>
          <div 
            v-for="b in dash.recent_bookings" 
            :key="b.id" 
            class="col-md-4"
          >
            <div class="card border-dark h-100 shadow-sm d-flex flex-column justify-content-between">
              <div class="card-body p-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <span class="fw-bold text-dark">{{ b.trek_name }}</span>
                  <span class="badge bg-secondary text-dark border border-dark">{{ b.status }}</span>
                </div>
                <div class="text-muted small mb-1">Location: {{ b.trek_location }}</div>
                <div class="text-muted small mb-2">Dates: {{ b.start_date || 'TBD' }} &rarr; {{ b.end_date || 'TBD' }}</div>

                <!-- Guide info -->
                <div v-if="b.staff_name && b.staff_name !== 'Unassigned'" class="small p-2 border border-dark rounded bg-light">
                  <div class="fw-bold">Guide: {{ b.staff_name }}</div>
                  <div v-if="b.staff_phone" class="text-muted">Phone: {{ b.staff_phone }}</div>
                  <div v-if="b.staff_email" class="text-muted">Email: {{ b.staff_email }}</div>
                </div>
              </div>
              <div class="card-footer bg-white border-top border-dark d-flex justify-content-between align-items-center p-3">
                <span class="fw-bold text-dark fs-5">₹{{ b.amount }}</span>
                <div class="d-flex gap-1">
                  <button v-if="b.status === 'Booked'" @click="cancel(b.id)" class="btn btn-outline-danger btn-sm fw-bold">Cancel</button>
                  <router-link v-else-if="b.status === 'Completed' && !b.reviewed" to="/bookings" class="btn btn-outline-warning btn-sm fw-bold">Review</router-link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'UserDashboard',
  data() {
    return {
      dash: null,
      loading: true,
      exporting: false,
      taskId: null,
      taskPoll: null
    };
  },
  created() {
    this.boundRefresh = () => {
      this.load();
    };
  },
  mounted() {
    this.load();
    this.$root.$on('refresh-notifications', this.boundRefresh);
  },
  beforeDestroy() {
    if (this.taskPoll) clearInterval(this.taskPoll);
    this.$root.$off('refresh-notifications', this.boundRefresh);
  },
  computed: {
    greeting() {
      const h = new Date().getHours();
      return h < 12 ? 'Good Morning' : h < 17 ? 'Good Afternoon' : 'Good Evening';
    }
  },
  methods: {
    async load() {
      this.loading = true;
      try {
        this.dash = await this.$api.get('/dashboard');
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.loading = false;
      }
    },
    async cancel(id) {
      if (!confirm('Are you sure you want to cancel this booking? A refund will be automatically simulated.')) return;
      try {
        await this.$api.put('/bookings/' + id + '/cancel', {});
        this.$root.toast('Booking cancelled successfully.');
        this.$root.$emit('refresh-notifications');
        await this.load();
      } catch (e) {
        this.$root.toast(e.message, 'error');
      }
    },
    async exportCSV() {
      this.exporting = true;
      try {
        const res = await this.$api.post('/export-bookings', {});
        if (res.task_id) {
          this.taskId = res.task_id;
          this.$root.toast('CSV compile started in background! You will receive email/notifs once complete. 📊');
          this.pollTask(res.task_id);
        } else {
          const r = await fetch('/api/export-bookings', {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + localStorage.getItem('tma_token') }
          });
          const blob = await r.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `bookings_export.csv`;
          a.click();
          URL.revokeObjectURL(url);
          this.$root.toast('CSV downloaded!');
        }
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.exporting = false;
      }
    },
    pollTask(tid) {
      let tries = 0;
      if (this.taskPoll) clearInterval(this.taskPoll);
      this.taskPoll = setInterval(async () => {
        tries++;
        try {
          const r = await this.$api.get('/export-bookings/status/' + tid);
          if (r.status === 'SUCCESS') {
            clearInterval(this.taskPoll);
            this.$root.toast('CSV export compile completed! Check email. ✅');
            this.$root.$emit('refresh-notifications');
            await this.load();
          } else if (r.status === 'FAILURE') {
            clearInterval(this.taskPoll);
            this.$root.toast('CSV compile failed on worker.', 'error');
          }
        } catch (e) {}
        if (tries > 25) clearInterval(this.taskPoll);
      }, 3000);
    }
  }
};
</script>
