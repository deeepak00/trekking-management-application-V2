<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4 pb-2 border-bottom border-dark flex-wrap gap-3">
      <div>
        <h2 class="fw-bold mb-1">My Booking History</h2>
        <p class="text-muted small mb-0">Total amount spent: <span class="fw-bold text-dark">₹{{ totalSpent }}</span></p>
      </div>
      <button @click="exportCSV" :disabled="exporting" class="btn btn-outline-dark fw-bold">
        {{ exporting ? 'Running export...' : 'Export Bookings CSV' }}
      </button>
    </div>

    <!-- Status Tabs -->
    <div class="card border-dark shadow-sm mb-4">
      <div class="card-body p-2">
        <div class="d-flex gap-2 flex-wrap">
          <button 
            v-for="s in ['', 'Booked', 'Started', 'Completed', 'Cancelled']" 
            :key="s"
            @click="filterStatus = s"
            class="btn btn-sm"
            :class="filterStatus === s ? 'btn-dark' : 'btn-outline-dark'"
          >
            {{ s || 'All Bookings' }} ({{ count(s) }})
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-dark" role="status"></div>
    </div>
    
    <div v-else-if="!filteredBookings.length" class="card border-dark text-center p-5">
      <h5 class="text-muted mb-3">No bookings found matching filters.</h5>
      <router-link to="/treks" class="btn btn-dark fw-bold mx-auto">Explore Treks</router-link>
    </div>
    
    <div class="row g-3" v-else>
      <div 
        v-for="b in filteredBookings" 
        :key="b.id" 
        class="col-md-6 col-lg-4"
      >
        <div class="card border-dark h-100 shadow-sm d-flex flex-column justify-content-between">
          <div class="card-body p-3">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <span class="fw-bold text-dark fs-5">{{ b.trek_name }}</span>
              <span class="badge bg-dark">{{ b.trek_status === 'Started' ? 'Started' : b.status }}</span>
            </div>
            <div class="text-muted small mb-1">Location: {{ b.trek_location }}</div>
            <div class="text-muted small mb-1">Dates: {{ b.start_date || 'TBD' }} &rarr; {{ b.end_date || 'TBD' }}</div>
            <div class="text-muted small mb-1">Booked on: {{ b.booking_date ? b.booking_date.slice(0,10) : '—' }}</div>
            <div class="text-muted small mb-2">Transaction: {{ b.payment_method || '—' }} &middot; {{ b.transaction_id || '—' }}</div>

            <!-- Guide contact details -->
            <div v-if="b.staff_name && b.staff_name !== 'Unassigned'" class="small p-2 border border-dark rounded bg-light mb-2">
              <div class="fw-bold">Guide: {{ b.staff_name }}</div>
              <div v-if="b.staff_phone" class="text-muted">Phone: {{ b.staff_phone }}</div>
              <div v-if="b.staff_email" class="text-muted">Email: {{ b.staff_email }}</div>
            </div>
            <div v-else class="small text-muted mt-2 mb-2">Guide: Unassigned</div>

            <div class="d-flex gap-2 mb-0">
              <span class="badge bg-secondary text-dark border border-dark">{{ b.trek_difficulty }}</span>
              <span class="badge bg-secondary text-dark border border-dark">{{ b.payment_status }}</span>
            </div>
          </div>

          <div class="card-footer bg-white border-top border-dark d-flex justify-content-between align-items-center p-3">
            <span class="fw-bold text-dark fs-5">₹{{ b.amount }}</span>
            
            <div class="d-flex gap-1">
              <button 
                v-if="b.status === 'Booked' && b.trek_status !== 'Started'" 
                @click="cancel(b.id)" 
                class="btn btn-outline-danger btn-sm fw-bold" 
                :disabled="cancelling === b.id"
              >
                Cancel
              </button>
              
              <button 
                v-if="b.status === 'Completed' && !b.reviewed" 
                @click="openReview(b)" 
                class="btn btn-outline-warning btn-sm fw-bold"
              >
                Review
              </button>
              <span v-if="b.status === 'Completed' && b.reviewed" class="badge bg-secondary text-dark border border-dark">Reviewed</span>
              <span v-if="b.status === 'Cancelled'" class="badge bg-secondary text-dark border border-dark">Refunded</span>
              <span v-if="b.trek_status === 'Started'" class="badge bg-secondary text-dark border border-dark">In Progress</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Review Modal Overlay -->
    <div class="modal d-block" tabindex="-1" style="background-color: rgba(0,0,0,0.5);" v-if="showReviewModal">
      <div class="modal-dialog modal-dialog-centered" style="max-width: 400px;">
        <div class="modal-content border-dark">
          <div class="modal-header border-bottom border-dark bg-light">
            <h5 class="modal-title fw-bold">Rate Trek</h5>
            <button type="button" class="btn-close" @click="showReviewModal = false"></button>
          </div>
          <div class="modal-body p-4">
            <h5 class="text-center fw-bold mb-3">{{ reviewForm.trek_name }}</h5>
            
            <div class="text-center mb-3">
              <p class="text-muted small mb-2">Rate your hike (1 to 5 stars):</p>
              <div class="d-flex justify-content-center gap-1">
                <button 
                  v-for="r in [1, 2, 3, 4, 5]" 
                  :key="r" 
                  @click="reviewForm.rating = r"
                  class="btn btn-link p-0 text-decoration-none fs-4"
                >
                  {{ r <= reviewForm.rating ? '★' : '☆' }}
                </button>
              </div>
              <div class="fw-bold mt-2 text-dark fs-5">
                {{ rLabel(reviewForm.rating) }}
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label fw-bold mb-2">Your review notes</label>
              <textarea v-model="reviewForm.comment" rows="3" class="form-control border-dark" placeholder="Share your experience..."></textarea>
            </div>
            
            <div class="d-flex justify-content-end gap-2">
              <button @click="showReviewModal = false" :disabled="submitting" class="btn btn-outline-danger btn-sm fw-bold">Cancel</button>
              <button @click="submitReview" :disabled="submitting" class="btn btn-dark btn-sm fw-bold">
                {{ submitting ? 'Submitting...' : 'Submit' }}
              </button>
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
  name: 'BookingHistory',
  data() {
    return {
      allBookings: [],
      loading: true,
      cancelling: null,
      filterStatus: '',
      exporting: false,
      taskId: null,
      _poll: null,
      showReviewModal: false,
      reviewForm: {
        trek_id: null,
        trek_name: '',
        rating: 5,
        comment: ''
      },
      submitting: false
    };
  },
  mounted() {
    this.load();
  },
  beforeDestroy() {
    if (this._poll) clearInterval(this._poll);
  },
  computed: {
    filteredBookings() {
      if (!this.filterStatus) return this.allBookings;
      return this.allBookings.filter(b => {
        const effectiveStatus = (b.status === 'Booked' && b.trek_status === 'Started') ? 'Started' : b.status;
        return effectiveStatus === this.filterStatus;
      });
    },
    count() {
      return (s) => {
        if (!s) return this.allBookings.length;
        return this.allBookings.filter(b => {
          const effectiveStatus = (b.status === 'Booked' && b.trek_status === 'Started') ? 'Started' : b.status;
          return effectiveStatus === s;
        }).length;
      };
    },
    totalSpent() {
      return this.allBookings
        .filter(b => b.status !== 'Cancelled')
        .reduce((sum, b) => sum + (b.amount || 0), 0);
    }
  },
  methods: {
    async load() {
      this.loading = true;
      try {
        this.allBookings = await this.$api.get('/bookings');
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.loading = false;
      }
    },
    async cancel(id) {
      if (!confirm('Cancel booking and request simulated refund?')) return;
      this.cancelling = id;
      try {
        await this.$api.put('/bookings/' + id + '/cancel', {});
        this.$root.toast('Booking cancelled. Refund initiated.');
        this.$root.$emit('refresh-notifications');
        await this.load();
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.cancelling = null;
      }
    },
    async exportCSV() {
      this.exporting = true;
      try {
        const res = await this.$api.post('/export-bookings', {});
        if (res.task_id) {
          this.taskId = res.task_id;
          this.$root.toast('CSV compile started in background! You will receive email/notifs once complete.');
          this.pollTask(res.task_id);
        } else {
          const r = await fetch('/api/trekker/export-bookings', {
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
      if (this._poll) clearInterval(this._poll);
      this._poll = setInterval(async () => {
        tries++;
        try {
          const r = await this.$api.get('/export-bookings/status/' + tid);
          if (r.status === 'SUCCESS') {
            clearInterval(this._poll);
            this.$root.toast('CSV export compile completed! Check email.');
            this.$root.$emit('refresh-notifications');
            await this.load();
          } else if (r.status === 'FAILURE') {
            clearInterval(this._poll);
            this.$root.toast('CSV compile failed on worker.', 'error');
          }
        } catch (e) {}
        if (tries > 25) clearInterval(this._poll);
      }, 3000);
    },
    openReview(b) {
      this.reviewForm = {
        trek_id: b.trek_id,
        trek_name: b.trek_name,
        rating: 5,
        comment: ''
      };
      this.showReviewModal = true;
    },
    async submitReview() {
      this.submitting = true;
      try {
        await this.$api.post('/reviews', {
          trek_id: this.reviewForm.trek_id,
          rating: this.reviewForm.rating,
          comment: this.reviewForm.comment
        });
        this.$root.toast('Review submitted! Thank you');
        this.showReviewModal = false;
        await this.load();
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.submitting = false;
      }
    },
    rLabel(r) {
      return ['', 'Poor', 'Fair', 'Good', 'Very Good', 'Excellent!'][r] || '';
    }
  }
};
</script>
