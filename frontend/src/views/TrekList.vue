<template>
  <div class="container py-4">
    
    <!-- Hero Banner area -->
    <div class="card border-dark shadow-sm text-center mb-4">
      <div class="card-body p-4 bg-light">
        <h2 class="fw-bold mb-2">Discover Your Next Adventure</h2>
        <p class="text-muted small mb-3">Hand-curated treks across the Himalayas and beyond</p>
        
        <!-- Search controls -->
        <div class="d-flex justify-content-center gap-2 flex-wrap">
          <input 
            v-model="filters.q" 
            type="text" 
            class="form-control border-dark"
            placeholder="Search treks, locations..." 
            style="max-width: 300px; width: 100%;"
            @input="debounceSearch"
          />
          <select v-model="filters.sort" class="form-select border-dark" style="max-width: 180px; width: 100%;" @change="fetch">
            <option value="date">Sort: Date</option>
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
            <option value="rating">Top Rated</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Main Content Area: Sidebar Filter + Cards Grid -->
    <div class="row g-4">
      
      <!-- Sidebar Filters (Left) -->
      <div class="col-md-3">
        <div class="card border-dark shadow-sm mb-3">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom border-dark">
              <span class="fw-bold">Filters</span>
              <button v-if="hasFilters" @click="resetFilters" class="btn btn-outline-dark btn-sm py-0 px-2">Reset</button>
            </div>

            <!-- Difficulty selection -->
            <div class="mb-4">
              <div class="fw-bold small mb-2">DIFFICULTY</div>
              <div v-for="d in ['Easy', 'Moderate', 'Hard']" :key="d" class="form-check mb-1">
                <input type="radio" :id="'diff-'+d" :value="d" v-model="filters.difficulty" class="form-check-input border-dark" @change="fetch" />
                <label :for="'diff-'+d" class="form-check-label small">{{ d }} ({{ counts[d] || 0 }})</label>
              </div>
              <div class="form-check">
                <input type="radio" id="diff-all" value="" v-model="filters.difficulty" class="form-check-input border-dark" @change="fetch" />
                <label for="diff-all" class="form-check-label text-muted small">All Difficulties</label>
              </div>
            </div>

            <!-- Location selection -->
            <div class="mb-4">
              <div class="fw-bold small mb-2">LOCATION</div>
              <select v-model="filters.location" class="form-select border-dark" @change="fetch">
                <option value="">All Locations</option>
                <option v-for="l in locations" :key="l" :value="l">{{ l }}</option>
              </select>
            </div>

            <!-- Price Range -->
            <div class="mb-4">
              <div class="fw-bold small mb-2">PRICE RANGE (₹)</div>
              <div class="d-flex gap-2">
                <input v-model.number="filters.min_price" type="number" placeholder="Min" class="form-control border-dark form-control-sm" @input="debounceSearch" />
                <input v-model.number="filters.max_price" type="number" placeholder="Max" class="form-control border-dark form-control-sm" @input="debounceSearch" />
              </div>
            </div>

            <!-- Duration Range -->
            <div class="mb-2">
              <div class="fw-bold small mb-2">DURATION (DAYS)</div>
              <div class="d-flex gap-2">
                <input v-model.number="filters.min_duration" type="number" placeholder="Min" class="form-control border-dark form-control-sm" @input="debounceSearch" />
                <input v-model.number="filters.max_duration" type="number" placeholder="Max" class="form-control border-dark form-control-sm" @input="debounceSearch" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Treks Grid (Right) -->
      <div class="col-md-9">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <span class="text-muted fw-bold"><span class="text-dark">{{ treks.length }}</span> treks found</span>
          <span v-if="loading" class="spinner-border spinner-border-sm text-dark" role="status"></span>
        </div>

        <div v-if="loading && !treks.length" class="text-center p-5">
          <div class="spinner-border text-dark" role="status"></div>
        </div>
        
        <div v-else>
          <div v-if="!treks.length" class="card border-dark text-center p-5">
            <h4 class="fw-bold mb-3">No treks match your criteria</h4>
            <button @click="resetFilters" class="btn btn-dark btn-sm mx-auto">Clear All Filters</button>
          </div>
          
          <div 
            class="row g-3" 
            v-else
            :style="loading ? 'opacity: 0.6; transition: opacity 0.2s;' : 'transition: opacity 0.2s;'"
          >
            <div 
              v-for="trek in treks" 
              :key="trek.id" 
              class="col-md-6 col-lg-4"
            >
              <div class="card border-dark h-100 shadow-sm d-flex flex-column justify-content-between">
                <div class="card-body p-3">
                  <div class="d-flex justify-content-between align-items-center mb-2">
                    <div class="d-flex gap-1 align-items-center flex-wrap">
                      <span class="badge bg-dark">{{ trek.difficulty }}</span>
                      <span v-if="isRecommended(trek)" class="badge bg-dark text-white fw-bold" style="font-size: 0.75rem;">Recommended</span>
                    </div>
                    <button @click.stop="toggleWish(trek)" class="btn btn-link p-0 text-decoration-none fs-5">
                      {{ isWish(trek.id) ? '❤️' : '🤍' }}
                    </button>
                  </div>

                  <h5 class="fw-bold mb-1">{{ trek.name }}</h5>
                  <div class="text-muted small mb-1">Location: {{ trek.location }}</div>
                  <div class="small mb-1">
                    Guide: <span class="fw-bold">{{ trek.staff_name }}</span>
                    <span v-if="trek.staff_specialization" class="text-muted"> &middot; {{ trek.staff_specialization }}</span>
                  </div>
                  
                  <div class="text-muted small mb-2">
                    Dates: {{ trek.start_date || 'TBD' }} &middot; {{ trek.duration }} Days &middot; {{ trek.altitude || '—' }}m Alt
                  </div>

                  <div class="mb-2" style="font-size: 0.95rem;">
                    Rating: <span class="fw-bold">{{ trek.avg_rating > 0 ? trek.avg_rating + ' ★' : 'No reviews' }}</span>
                    <span class="text-muted"> ({{ trek.review_count || 0 }})</span>
                  </div>

                  <p class="text-muted small mb-0" style="display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 2.6rem;">
                    {{ trek.description || 'Enjoy this fantastic trek.' }}
                  </p>
                </div>

                <div class="card-footer bg-white border-top border-dark p-3">
                  <div class="d-flex justify-content-between align-items-center mb-2" style="font-size: 0.9rem;">
                    <span class="text-muted">Slots Left:</span>
                    <span :class="trek.available_slots === 0 ? 'text-danger fw-bold' : 'fw-bold'">{{ trek.available_slots === 0 ? 'FULL' : trek.available_slots + ' left' }}</span>
                  </div>

                  <div class="d-flex justify-content-between align-items-center">
                    <div>
                      <span class="fw-bold text-dark fs-5">₹{{ trek.price }}</span>
                      <span class="text-muted small">/person</span>
                    </div>
                    <div class="d-flex gap-1">
                      <button @click="openDetail(trek)" class="btn btn-outline-dark btn-sm fw-bold">Details</button>
                      <button 
                        @click="openBook(trek)" 
                        class="btn btn-dark btn-sm fw-bold"
                        :disabled="trek.available_slots === 0"
                      >
                        Book
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- Trek Detail Modal Overlay -->
    <div class="modal d-block" tabindex="-1" style="background-color: rgba(0,0,0,0.5);" v-if="detailTrek">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content border-dark">
          <div class="modal-header border-bottom border-dark bg-light">
            <div>
              <h4 class="modal-title fw-bold">{{ detailTrek.name }}</h4>
              <div class="text-muted small">Location: {{ detailTrek.location }}</div>
            </div>
            <button type="button" class="btn-close" @click="detailTrek = null"></button>
          </div>
          <div class="modal-body p-4" style="max-height: 70vh; overflow-y: auto;">
            <div class="row g-3">
              <!-- Details (Left) -->
              <div class="col-md-8">
                <div class="row g-2 mb-3 text-center">
                  <div class="col">
                    <div class="border border-dark rounded p-2">
                      <div class="fw-bold">{{ detailTrek.duration }}d</div>
                      <div class="text-muted small">Duration</div>
                    </div>
                  </div>
                  <div class="col">
                    <div class="border border-dark rounded p-2">
                      <div class="fw-bold">{{ detailTrek.altitude ? detailTrek.altitude + 'm' : '—' }}</div>
                      <div class="text-muted small">Max Alt</div>
                    </div>
                  </div>
                  <div class="col">
                    <div class="border border-dark rounded p-2">
                      <div class="fw-bold">{{ detailTrek.available_slots }}/{{ detailTrek.total_slots }}</div>
                      <div class="text-muted small">Slots Left</div>
                    </div>
                  </div>
                </div>

                <h5 class="fw-bold mb-2">Description</h5>
                <p class="small text-muted mb-3">{{ detailTrek.description }}</p>

                <div v-if="detailTrek.highlights" class="mb-3">
                  <h5 class="fw-bold mb-2">Highlights</h5>
                  <div class="d-flex flex-wrap gap-2">
                    <span v-for="h in detailTrek.highlights.split('|')" :key="h" class="badge bg-secondary text-dark border border-dark">{{ h }}</span>
                  </div>
                </div>

                <div class="row g-3 mb-3">
                  <div v-if="detailTrek.included" class="col-sm-6">
                    <div class="fw-bold small text-dark mb-1">What's Included:</div>
                    <ul class="small ps-3 mb-0">
                      <li v-for="item in detailTrek.included.split('|')" :key="item">{{ item }}</li>
                    </ul>
                  </div>
                  <div v-if="detailTrek.not_included" class="col-sm-6">
                    <div class="fw-bold small text-dark mb-1">Not Included:</div>
                    <ul class="small ps-3 mb-0">
                      <li v-for="item in detailTrek.not_included.split('|')" :key="item">{{ item }}</li>
                    </ul>
                  </div>
                </div>

                <div v-if="detailTrek.equipment_needed" class="mb-3">
                  <div class="fw-bold small">Equipment Needed:</div>
                  <p class="small text-muted mt-1">{{ detailTrek.equipment_needed }}</p>
                </div>

                <!-- Reviews list -->
                <h5 class="fw-bold mb-2">Reviews ({{ detailRevs.length }})</h5>
                <div v-if="!detailRevs.length" class="text-muted small mb-2">No reviews recorded yet.</div>
                <div 
                  v-for="r in detailRevs" 
                  :key="r.id" 
                  class="p-2 mb-2 border border-dark rounded bg-light"
                >
                  <div class="d-flex justify-content-between align-items-center small fw-bold">
                    <span>{{ r.user_name }}</span>
                    <span class="text-dark">{{ r.rating }} ★</span>
                  </div>
                  <p class="small text-muted mt-1 mb-0">{{ r.comment }}</p>
                </div>
              </div>

              <!-- Booking panel (Right) -->
              <div class="col-md-4">
                <div class="border border-dark rounded p-3 bg-light">
                  <div class="text-center mb-3">
                    <span class="fw-bold text-dark fs-4">₹{{ detailTrek.price }}</span>
                    <span class="text-muted small"> /person</span>
                  </div>
                  
                  <div class="small mb-3">
                    <div class="d-flex justify-content-between mb-1"><span>Difficulty:</span><span class="fw-bold">{{ detailTrek.difficulty }}</span></div>
                    <div class="d-flex justify-between mb-1"><span>Ages Allowed:</span><span class="fw-bold">{{ detailTrek.min_age }}–{{ detailTrek.max_age }} yrs</span></div>
                    <div class="d-flex justify-between"><span>Meeting:</span><span class="fw-bold">{{ detailTrek.meeting_point || 'TBD' }}</span></div>
                  </div>

                  <div class="p-2 border border-dark rounded bg-white mb-3">
                    <div class="fw-bold small">Your Guide Info:</div>
                    <div class="small fw-bold mt-1">{{ detailTrek.staff_name }}</div>
                    <div v-if="detailTrek.staff_specialization" class="small text-muted">{{ detailTrek.staff_specialization }} specialization</div>
                  </div>

                  <button @click="openBook(detailTrek)" class="btn btn-dark w-100 fw-bold" :disabled="detailTrek.available_slots === 0">
                    {{ detailTrek.available_slots === 0 ? 'No Slots Left' : 'Book Trek' }}
                  </button>
                </div>
              </div>
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
import axios from 'axios';

export default {
  name: 'TrekList',
  data() {
    return {
      treks: [],
      wishIds: [],
      allLocations: [],
      loading: true,
      booking: false,
      sel: null,
      detailTrek: null,
      detailRevs: [],
      payMethod: 'UPI',
      notes: '',
      filters: {
        q: '',
        difficulty: '',
        location: '',
        min_duration: '',
        max_duration: '',
        min_price: '',
        max_price: '',
        sort: 'date'
      },
      _t: null
    };
  },
  mounted() {
    this.fetch();
    if (this.$root.currentUser && this.$root.currentUser.role === 'user') {
      this.fetchWish();
    }
  },
  beforeDestroy() {
    clearTimeout(this._t);
  },
  computed: {
    locations() {
      return this.allLocations;
    },
    counts() {
      let e = 0, m = 0, h = 0;
      this.treks.forEach(t => {
        if (t.difficulty === 'Easy') e++;
        else if (t.difficulty === 'Moderate') m++;
        else h++;
      });
      return { Easy: e, Moderate: m, Hard: h };
    },
    hasFilters() {
      const f = this.filters;
      return !!(f.q || f.difficulty || f.location || f.min_duration || f.max_duration || f.min_price || f.max_price);
    }
  },
  methods: {
    debounceSearch() {
      clearTimeout(this._t);
      this._t = setTimeout(() => {
        this.fetch();
      }, 450);
    },
    async fetch() {
      this.loading = true;
      try {
        const p = new URLSearchParams();
        const f = this.filters;
        if (f.q) p.append('q', f.q);
        if (f.difficulty) p.append('difficulty', f.difficulty);
        if (f.location) p.append('location', f.location);
        if (f.min_duration) p.append('min_duration', f.min_duration);
        if (f.max_duration) p.append('max_duration', f.max_duration);
        if (f.min_price) p.append('min_price', f.min_price);
        if (f.max_price) p.append('max_price', f.max_price);
        if (f.sort) p.append('sort', f.sort);

        this.treks = await this.$api.get('/treks?' + p.toString());
        // Populate allLocations only once when there are no active filters
        if (!f.q && !f.difficulty && !f.location && !f.min_duration && !f.max_duration && !f.min_price && !f.max_price) {
          const seen = {};
          const list = [];
          this.treks.forEach(t => {
            const x = t.location.split(',')[0].trim();
            if (!seen[x]) {
              seen[x] = true;
              list.push(x);
            }
          });
          this.allLocations = list;
        }
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.loading = false;
      }
    },
    async fetchWish() {
      try {
        const res = await this.$api.get('/wishlist/ids');
        this.wishIds = Array.isArray(res) ? res : (res.wishlist_ids || []);
      } catch (e) {
        this.wishIds = [];
      }
    },
    resetFilters() {
      this.filters = {
        q: '',
        difficulty: '',
        location: '',
        min_duration: '',
        max_duration: '',
        min_price: '',
        max_price: '',
        sort: 'date'
      };
      this.fetch();
    },
    isWish(id) {
      return this.wishIds.indexOf(id) !== -1;
    },
    isRecommended(trek) {
      // 1. Must have slots left
      if (trek.available_slots <= 0) return false;

      // 2. Highly rated treks are always recommended
      if (trek.avg_rating >= 4.0) return true;

      // 3. Match logged-in user's preferred difficulty (personalized recommendation)
      const u = this.$root.currentUser;
      if (u && u.trekker_info && u.trekker_info.preferred_difficulty) {
        return trek.difficulty === u.trekker_info.preferred_difficulty;
      }

      // 4. Fallback default: recommend beginner-friendly treks
      return trek.difficulty === 'Easy' || trek.difficulty === 'Moderate';
    },
    async toggleWish(trek) {
      const u = this.$root.currentUser;
      if (!u) {
        this.$router.push('/login');
        return;
      }
      if (u.role !== 'user') {
        this.$root.toast('Only trekkers can use the wishlist', 'warning');
        return;
      }
      try {
        if (this.isWish(trek.id)) {
          await this.$api.delete('/wishlist/' + trek.id);
          this.wishIds = this.wishIds.filter(i => i !== trek.id);
          this.$root.toast('Removed from wishlist');
        } else {
          await this.$api.post('/wishlist/' + trek.id, {});
          this.wishIds.push(trek.id);
          this.$root.toast('Added to wishlist');
        }
      } catch (e) {
        this.$root.toast(e.message, 'error');
      }
    },
    async openDetail(trek) {
      this.detailTrek = trek;
      this.detailRevs = [];
      try {
        this.detailRevs = await this.$api.get('/treks/' + trek.id + '/reviews');
      } catch (e) {}
    },
    openBook(trek) {
      const u = this.$root.currentUser;
      if (!u) {
        this.$router.push('/login');
        return;
      }
      if (u.role !== 'user') {
        this.$root.toast('Only trekkers can register bookings', 'warning');
        return;
      }
      this.sel = trek;
      this.payMethod = 'UPI';
      this.notes = '';
      this.detailTrek = null;
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
        this.$root.$emit('refresh-notifications');
        this.sel = null;
        await this.fetch();
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
