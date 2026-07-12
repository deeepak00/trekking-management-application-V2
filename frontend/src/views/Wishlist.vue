<template>
  <div class="container py-4">
    <h2 class="fw-bold mb-4 pb-2 border-bottom border-dark">My Trek Wishlist</h2>
    
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-dark" role="status"></div>
    </div>
    
    <div v-else>
      <div v-if="!items.length" class="card border-dark text-center p-5">
        <p class="text-muted mb-3">Your wishlist is empty.</p>
        <router-link to="/treks" class="btn btn-dark fw-bold mx-auto">Explore Treks</router-link>
      </div>

      <div class="row g-3" v-else>
        <div 
          v-for="item in items" 
          :key="item.wishlist_id" 
          class="col-md-6 col-lg-4"
        >
          <div class="card border-dark h-100 shadow-sm d-flex flex-column justify-content-between">
            <div class="card-body p-3">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="badge bg-dark">{{ item.trek.difficulty }}</span>
                <span class="badge bg-secondary text-dark border border-dark">₹{{ item.trek.price }}</span>
              </div>

              <h5 class="fw-bold mb-1">{{ item.trek.name }}</h5>
              <div class="text-muted small mb-1">Location: {{ item.trek.location }}</div>
              <div class="text-muted small">Duration: {{ item.trek.duration }} Days</div>
            </div>

            <div class="card-footer bg-white border-top border-dark d-flex gap-2 p-3">
              <button 
                @click="openBook(item.trek)" 
                class="btn btn-dark btn-sm w-100 fw-bold"
                :disabled="item.trek.available_slots === 0"
              >
                {{ item.trek.available_slots === 0 ? 'Full' : 'Book Now' }}
              </button>
              <button @click="remove(item.trek.id)" class="btn btn-outline-danger btn-sm fw-bold">Remove</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Booking details Modal Overlay -->
    <div class="modal d-block" tabindex="-1" style="background-color: rgba(0,0,0,0.5);" v-if="sel">
      <div class="modal-dialog modal-dialog-centered" style="max-width: 450px;">
        <div class="modal-content border-dark">
          <div class="modal-header border-bottom border-dark bg-light">
            <h5 class="modal-title fw-bold">Complete Booking</h5>
            <button type="button" class="btn-close" @click="sel = null"></button>
          </div>
          <div class="modal-body p-4">
            <div class="mb-3 p-3 border border-dark rounded bg-light">
              <div class="fw-bold">{{ sel.name }}</div>
              <div class="small text-muted">{{ sel.location }} &middot; {{ sel.duration }} Days</div>
              <div class="small text-muted">Starting: {{ sel.start_date || 'TBD' }}</div>
            </div>

            <label class="form-label fw-bold mb-2">Payment Method</label>
            <div class="d-flex flex-wrap gap-2 mb-3">
              <button 
                v-for="m in ['UPI', 'Credit Card', 'Debit Card', 'Net Banking']" 
                :key="m"
                @click="payMethod = m"
                class="btn btn-sm"
                :class="payMethod === m ? 'btn-dark' : 'btn-outline-dark'"
              >
                {{ m }}
              </button>
            </div>

            <div class="mb-3">
              <label class="form-label fw-bold mb-2">Medical/Special Notes</label>
              <textarea v-model="notes" rows="2" class="form-control border-dark" placeholder="e.g. Dietary needs, medical details"></textarea>
            </div>

            <div class="p-2 border border-dark rounded bg-light mb-3">
              <div class="d-flex justify-content-between small"><span>Subtotal</span><span>₹{{ sel.price }}</span></div>
              <div class="d-flex justify-content-between small text-muted"><span>Fees & Tax</span><span>₹0.00</span></div>
              <div class="border-top border-dark my-2"></div>
              <div class="d-flex justify-content-between fw-bold"><span>Total Price</span><span>₹{{ sel.price }}</span></div>
            </div>
            
            <div class="d-flex justify-content-end gap-2">
              <button @click="sel = null" :disabled="booking" class="btn btn-outline-danger btn-sm fw-bold">Cancel</button>
              <button @click="book" class="btn btn-dark btn-sm fw-bold" :disabled="booking">
                {{ booking ? 'Processing...' : 'Pay ₹' + sel.price }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Wishlist',
  data() {
    return {
      items: [],
      loading: true,
      sel: null,
      payMethod: 'UPI',
      notes: '',
      booking: false
    };
  },
  mounted() {
    this.load();
  },
  methods: {
    async load() {
      this.loading = true;
      try {
        this.items = await this.$api.get('/wishlist');
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.loading = false;
      }
    },
    async remove(tid) {
      try {
        await this.$api.delete('/wishlist/' + tid);
        this.$root.toast('Removed from wishlist');
        await this.load();
      } catch (e) {
        this.$root.toast(e.message, 'error');
      }
    },
    openBook(trek) {
      this.sel = trek;
      this.payMethod = 'UPI';
      this.notes = '';
    },
    async book() {
      this.booking = true;
      try {
        const d = await this.$api.post('/bookings', {
          trek_id: this.sel.id,
          payment_method: this.payMethod,
          notes: this.notes
        });
        this.$root.toast('Trek booked! TXN ID: ' + d.transaction_id);
        
        // Auto-remove from wishlist since booked
        try {
          await this.$api.delete('/wishlist/' + this.sel.id);
        } catch (e) {}

        this.$root.$emit('refresh-notifications');
        this.sel = null;
        this.$router.push('/dashboard');
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.booking = false;
      }
    }
  }
};
</script>
