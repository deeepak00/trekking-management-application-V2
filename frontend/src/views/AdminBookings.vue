<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4 pb-2 border-bottom border-dark flex-wrap gap-3">
      <h2 class="fw-bold mb-0">All Platform Bookings</h2>
    </div>

    <!-- Filters -->
    <div class="card border-dark shadow-sm mb-4">
      <div class="card-body p-3">
        <div class="row g-3">
          <div class="col-md-8">
            <select v-model="filterTrek" class="form-select border-dark">
              <option :value="null">All Treks</option>
              <option v-for="t in treks" :key="t.id" :value="t.id">{{ t.name }}</option>
            </select>
          </div>
          <div class="col-md-4">
            <select v-model="filterStatus" class="form-select border-dark">
              <option value="">All Statuses</option>
              <option>Booked</option>
              <option>Started</option>
              <option>Completed</option>
              <option>Cancelled</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-dark" role="status"></div>
    </div>
    <div v-else>
      <div v-if="!bookings.length" class="card border-dark text-center p-5">
        <p class="text-muted mb-0">No bookings found.</p>
      </div>
      
      <div v-else class="card border-dark shadow-sm p-4">
        <div class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead>
              <tr style="border-bottom: 2px solid #000;">
                <th class="fw-bold">Booking ID</th>
                <th class="fw-bold">Trekker</th>
                <th class="fw-bold">Trek Name</th>
                <th class="fw-bold">Booking Date</th>
                <th class="fw-bold">Amount</th>
                <th class="fw-bold">Payment Status</th>
                <th class="fw-bold">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in bookings" :key="b.id">
                <td>#{{ b.id }}</td>
                <td class="fw-bold">
                  {{ b.user_name }}
                  <div class="text-muted small fw-normal">{{ b.user_email }}</div>
                </td>
                <td>{{ b.trek_name }}</td>
                <td>{{ b.booking_date ? b.booking_date.slice(0,10) : '—' }}</td>
                <td class="fw-bold">₹{{ b.amount }}</td>
                <td>
                  <span class="badge bg-secondary text-dark border border-dark">
                    {{ b.payment_status }}
                  </span>
                </td>
                <td>
                  <span class="badge bg-dark text-white">
                    {{ b.status }}
                  </span>
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
  name: 'AdminBookings',
  data() {
    return {
      bookings: [],
      treks: [],
      filterTrek: null,
      filterStatus: '',
      loading: true
    };
  },
  mounted() {
    this.init();
  },
  watch: {
    filterTrek() { this.load(); },
    filterStatus() { this.load(); }
  },
  methods: {
    async init() {
      try {
        this.treks = await this.$api.get('/admin/treks');
      } catch (e) {}
      await this.load();
    },
    async load() {
      this.loading = true;
      try {
        let url = '/admin/bookings?';
        if (this.filterTrek) url += 'trek_id=' + this.filterTrek + '&';
        if (this.filterStatus) url += 'status=' + this.filterStatus;
        this.bookings = await this.$api.get(url);
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
