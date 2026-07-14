<template>
  <div class="container py-4">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-dark" role="status"></div>
    </div>
    
    <div v-else-if="dash">
      <!-- Guide Profile Banner (Bootstrap Card) -->
      <div class="card border-dark shadow-sm mb-4">
        <div class="card-body p-4">
          <h2 class="fw-bold mb-1">Welcome, {{ dash.staff.name }}!</h2>
          <p class="text-muted small mb-0">
            <span v-if="dash.staff.staff_info">
              {{ dash.staff.staff_info.specialization || 'Trek Guide' }} &middot; 
              {{ dash.staff.staff_info.years_experience || 0 }} Yrs Experience &middot; 
              {{ dash.staff.staff_info.languages || 'Hindi, English' }}
            </span>
            <span v-else>Trek Guide Member</span>
          </p>

          <!-- Stats Grid -->
          <div class="row row-cols-2 row-cols-md-5 g-3 mt-3">
            <div 
              v-for="s in [
                { val: dash.total_assigned, label: 'Assigned' },
                { val: dash.open_treks, label: 'Open' },
                { val: dash.started_treks, label: 'Started' },
                { val: dash.completed_treks, label: 'Completed' },
                { val: totalParts, label: 'Trekkers' }
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

      <!-- My Assigned Treks List -->
      <h3 class="fw-bold mb-3">My Assigned Treks</h3>
      <div v-if="!dash.assigned_treks.length" class="card border-dark text-center p-5">
        <p class="text-muted mb-0">No treks assigned yet.</p>
      </div>
      
      <div class="row g-3" v-else>
        <div 
          v-for="trek in dash.assigned_treks" 
          :key="trek.id" 
          class="col-md-6 col-lg-4"
        >
          <div class="card border-dark h-100 shadow-sm d-flex flex-column justify-content-between">
            <div class="card-body p-3">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="fw-bold text-dark fs-5">{{ trek.name }}</span>
                <span class="badge bg-dark">{{ trek.status }}</span>
              </div>
              <div class="text-muted small mb-1">Location: {{ trek.location }}</div>
              <div class="text-muted small mb-2">Dates: {{ trek.start_date || 'TBD' }} &rarr; {{ trek.end_date || 'TBD' }}</div>
              
              <div class="d-flex gap-2 mb-2">
                <span class="badge bg-secondary text-dark border border-dark">{{ trek.difficulty }}</span>
                <span class="badge bg-secondary text-dark border border-dark">{{ trek.duration }} Days</span>
                <span class="badge bg-secondary text-dark border border-dark">₹{{ trek.price }}</span>
              </div>

              <div class="fw-bold mb-0" style="font-size: 0.95rem;">
                Trekkers Registered: <span class="text-dark">{{ trek.participant_count }} / {{ trek.total_slots }}</span>
              </div>
            </div>

            <div class="card-footer bg-white border-top border-dark p-3">
              <button @click="view(trek)" class="btn btn-dark btn-sm w-100 fw-bold">Manage Trek</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Manage Trek Modal Overlay -->
    <div class="modal d-block" tabindex="-1" style="background-color: rgba(0,0,0,0.5);" v-if="showModal && sel">
      <div class="modal-dialog modal-xl modal-dialog-centered">
        <div class="modal-content border-dark">
          <div class="modal-header border-bottom border-dark bg-light">
            <div>
              <h4 class="modal-title fw-bold">{{ sel.name }}</h4>
              <div class="text-muted small">Location: {{ sel.location }}</div>
            </div>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body p-4" style="max-height: 70vh; overflow-y: auto;">
            <div class="row g-4">
              <!-- Update Form (Left side) -->
              <div class="col-md-4 border-end border-dark pb-3 pb-md-0" style="border-right-style: dashed !important;">
                <h5 class="fw-bold text-dark mb-3">Update Status</h5>
                
                <div class="mb-3">
                  <label class="form-label fw-bold text-dark">Available Slots</label>
                  <input 
                    v-model.number="ef.available_slots" 
                    type="number" 
                    min="0" 
                    class="form-control border-dark"
                  />
                  <span class="text-muted small">Total Capacity: {{ sel.total_slots }}</span>
                </div>

                <div class="mb-3">
                  <label class="form-label fw-bold text-dark">Trek Status</label>
                  <select v-model="ef.status" class="form-select border-dark">
                    <option>Open</option>
                    <option>Started</option>
                    <option>Completed</option>
                  </select>
                </div>

                <div v-if="ef.status === 'Started'" class="alert alert-warning p-2 mb-3 small fw-bold">
                  Marking "Started" will send push notification updates to all booked participants.
                </div>

                <div v-if="ef.status === 'Completed'" class="alert alert-danger p-2 mb-3 small fw-bold">
                  Completing the trek will automatically archive all active bookings and credit experience values to user accounts.
                </div>

                <button @click="update" :disabled="saving" class="btn btn-dark w-100 fw-bold">
                  {{ saving ? 'Saving Changes...' : 'Save Settings' }}
                </button>
              </div>

              <!-- Participants list (Right side) -->
              <div class="col-md-8">
                <h5 class="fw-bold text-dark mb-3">Trekkers Registered ({{ parts.length }})</h5>
                <div v-if="loadingP" class="text-muted text-center py-3">Loading participant lists...</div>
                <div v-else-if="!parts.length" class="text-muted text-center py-3">No participants checked in yet.</div>
                <div v-else class="table-responsive">
                  <table class="table table-hover align-middle mb-0" style="font-size: 0.95rem;">
                    <thead>
                      <tr style="border-bottom: 2px solid #000;">
                        <th class="fw-bold">Trekker Name</th>
                        <th class="fw-bold">Level / Fitness</th>
                        <th class="fw-bold">Emergency Contact</th>
                        <th class="fw-bold">Medical Notes</th>
                        <th class="fw-bold">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="p in parts" :key="p.id">
                        <td class="fw-bold">
                          {{ p.user_name }}
                          <div class="text-muted small fw-normal">{{ p.user_email }}</div>
                        </td>
                        <td>
                          <div class="fw-bold">{{ p.experience_level || 'Beginner' }}</div>
                          <div class="text-muted small">{{ p.fitness_level || 'Medium' }} Fitness</div>
                        </td>
                        <td>
                          <div>{{ p.emergency_contact || '—' }}</div>
                          <div class="text-muted small">{{ p.emergency_phone || '' }}</div>
                        </td>
                        <td>
                          <span v-if="p.medical_notes" class="text-danger fw-bold" :title="p.medical_notes">
                            Medical Note
                          </span>
                          <span v-else class="text-muted">—</span>
                        </td>
                        <td>
                          <span class="badge bg-secondary text-dark border border-dark">{{ p.status }}</span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
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
export default {
  name: 'StaffDashboard',
  data() {
    return {
      dash: null,
      loading: true,
      sel: null,
      parts: [],
      loadingP: false,
      saving: false,
      showModal: false,
      ef: {
        available_slots: 0,
        status: ''
      }
    };
  },
  mounted() {
    this.load();
  },
  computed: {
    totalParts() {
      return this.dash ? this.dash.assigned_treks.reduce((s, t) => s + t.participant_count, 0) : 0;
    }
  },
  methods: {
    async load() {
      this.loading = true;
      try {
        this.dash = await this.$api.get('/staff/dashboard');
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.loading = false;
      }
    },
    async view(trek) {
      this.sel = trek;
      this.ef = {
        available_slots: trek.available_slots,
        status: trek.status
      };
      this.parts = [];
      this.loadingP = true;
      this.showModal = true;
      try {
        const d = await this.$api.get('/staff/treks/' + trek.id + '/participants');
        this.parts = d.participants;
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.loadingP = false;
      }
    },
    closeModal() {
      this.showModal = false;
      this.sel = null;
    },
    async update() {
      this.saving = true;
      try {
        await this.$api.put('/staff/treks/' + this.sel.id, this.ef);
        this.$root.toast('Trek updated successfully!');
        this.closeModal();
        await this.load();
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.saving = false;
      }
    }
  }
};
</script>
