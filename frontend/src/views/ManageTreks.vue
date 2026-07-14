<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4 pb-2 border-bottom border-dark flex-wrap gap-3">
      <h2 class="fw-bold mb-0">Manage Treks</h2>
      <button @click="openNew" class="btn btn-dark fw-bold">Create Trek</button>
    </div>

    <!-- Search / Filter bar -->
    <div class="card border-dark shadow-sm mb-4">
      <div class="card-body p-3">
        <input 
          v-model="search" 
          type="text" 
          class="form-control border-dark"
          placeholder="Filter treks by name or location..." 
          @input="debounceSearch"
        />
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-dark" role="status"></div>
    </div>
    <div v-else>
      <div v-if="!treks.length" class="card border-dark text-center p-5">
        <p class="text-muted mb-0">No treks found.</p>
      </div>
      
      <div v-else class="card border-dark shadow-sm p-4">
        <div class="table-responsive" style="max-height: 350px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 4px;">
          <table class="table table-hover table-sm align-middle mb-0" style="table-layout: fixed; width: 100%; font-size: 0.9rem;">
            <colgroup>
              <col style="width: 20%;">
              <col style="width: 20%;">
              <col style="width: 10%;">
              <col style="width: 12%;">
              <col style="width: 10%;">
              <col style="width: 15%;">
              <col style="width: 10%;">
              <col style="width: 13%;">
            </colgroup>
            <thead>
              <tr style="border-bottom: 2px solid #000;">
                <th class="fw-bold">Name</th>
                <th class="fw-bold">Location</th>
                <th class="fw-bold">Difficulty</th>
                <th class="fw-bold">Slots (Booked/Total)</th>
                <th class="fw-bold">Price</th>
                <th class="fw-bold">Staff/Guide</th>
                <th class="fw-bold">Status</th>
                <th class="fw-bold">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in treks" :key="t.id">
                <td class="fw-bold text-break">{{ t.name }}</td>
                <td class="text-break">{{ t.location }}</td>
                <td><span class="badge bg-dark">{{ t.difficulty }}</span></td>
                <td>{{ t.booked_count }} / {{ t.total_slots }}</td>
                <td>₹{{ t.price }}</td>
                <td class="text-break">{{ t.staff_name }}</td>
                <td><span class="badge bg-secondary text-dark border border-dark">{{ t.status }}</span></td>
                <td>
                  <div class="d-flex gap-1">
                    <button @click="openEdit(t)" class="btn btn-outline-dark btn-sm fw-bold" :disabled="t.booked_count > 0 || t.status === 'Started' || t.status === 'Completed'">Edit</button>
                    <button @click="del(t)" class="btn btn-outline-danger btn-sm fw-bold" :disabled="t.booked_count > 0 || t.status === 'Started' || t.status === 'Completed'">Delete</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Simple Custom Modal Overlay for Add/Edit -->
    <div class="modal d-block" tabindex="-1" style="background-color: rgba(0,0,0,0.5);" v-if="showModal">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content border-dark">
          <div class="modal-header border-bottom border-dark bg-light">
            <h5 class="modal-title fw-bold">{{ isEditing ? 'Edit Trek' : 'New Trek' }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body p-4" style="max-height: 70vh; overflow-y: auto;">
            <div class="row g-3">
              <div class="col-md-6">
                <label class="form-label fw-bold text-dark">Trek Name *</label>
                <input v-model="form.name" type="text" class="form-control border-dark" placeholder="e.g. Valley of Flowers" />
              </div>

              <div class="col-md-6">
                <label class="form-label fw-bold text-dark">Location *</label>
                <input v-model="form.location" type="text" class="form-control border-dark" placeholder="e.g. Uttarakhand, India" />
              </div>

              <div class="col-md-4">
                <label class="form-label fw-bold text-dark">Difficulty *</label>
                <select v-model="form.difficulty" class="form-select border-dark">
                  <option>Easy</option>
                  <option>Moderate</option>
                  <option>Hard</option>
                </select>
              </div>
              <div class="col-md-4">
                <label class="form-label fw-bold text-dark">Duration (days) *</label>
                <input v-model.number="form.duration" type="number" min="1" class="form-control border-dark" />
              </div>
              <div class="col-md-4">
                <label class="form-label fw-bold text-dark">Total Slots *</label>
                <input v-model.number="form.total_slots" type="number" min="1" class="form-control border-dark" />
              </div>

              <div class="col-md-6">
                <label class="form-label fw-bold text-dark">Price (INR) *</label>
                <input v-model.number="form.price" type="number" min="0" class="form-control border-dark" />
              </div>
              <div class="col-md-6">
                <label class="form-label fw-bold text-dark">Altitude (meters)</label>
                <input v-model.number="form.altitude" type="number" class="form-control border-dark" />
              </div>

              <div class="col-md-6">
                <label class="form-label fw-bold text-dark">Start Date</label>
                <input v-model="form.start_date" type="date" class="form-control border-dark" />
              </div>
              <div class="col-md-6">
                <label class="form-label fw-bold text-dark">End Date</label>
                <input v-model="form.end_date" type="date" class="form-control border-dark" />
              </div>

              <div class="col-md-6">
                <label class="form-label fw-bold text-dark">Assign Guide</label>
                <select v-model="form.staff_id" class="form-select border-dark">
                  <option :value="null">Unassigned</option>
                  <option v-for="s in staff" :key="s.id" :value="s.id">{{ s.name }} ({{ s.staff_info ? s.staff_info.specialization : 'Guide' }})</option>
                </select>
              </div>
              <div class="col-md-6">
                <label class="form-label fw-bold text-dark">Trek Status</label>
                <select v-model="form.status" class="form-select border-dark">
                  <option v-for="st in allowedStatuses" :key="st" :value="st">{{ st }}</option>
                </select>
              </div>


              <div class="col-12">
                <label class="form-label fw-bold text-dark">Meeting Point</label>
                <input v-model="form.meeting_point" type="text" class="form-control border-dark" placeholder="e.g. Sankri Village" />
              </div>

              <div class="col-12">
                <label class="form-label fw-bold text-dark">Description</label>
                <textarea v-model="form.description" rows="2" class="form-control border-dark" placeholder="Write description..."></textarea>
              </div>

              <div class="col-12">
                <label class="form-label fw-bold text-dark">Highlights (pipe separated)</label>
                <input v-model="form.highlights" type="text" class="form-control border-dark" placeholder="Peak views|Snow camping" />
              </div>

              <div class="col-12">
                <label class="form-label fw-bold text-dark">Included (pipe separated)</label>
                <input v-model="form.included" type="text" class="form-control border-dark" placeholder="Tents|Meals|Guide" />
              </div>

              <div class="col-12">
                <label class="form-label fw-bold text-dark">Not Included (pipe separated)</label>
                <input v-model="form.not_included" type="text" class="form-control border-dark" placeholder="Personal clothing|Transport" />
              </div>

              <div class="col-12">
                <label class="form-label fw-bold text-dark">Equipment Needed</label>
                <input v-model="form.equipment_needed" type="text" class="form-control border-dark" placeholder="Boots, poles, thermal layer" />
              </div>
            </div>
            
            <div class="d-flex justify-content-end gap-2 mt-4">
              <button @click="closeModal" :disabled="saving" class="btn btn-outline-danger btn-sm fw-bold">Cancel</button>
              <button @click="save" :disabled="saving" class="btn btn-dark btn-sm fw-bold">
                {{ saving ? 'Saving...' : 'Save Trek' }}
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
  name: 'ManageTreks',
  data() {
    return {
      treks: [],
      staff: [],
      loading: true,
      saving: false,
      search: '',
      showModal: false,
      isEditing: false,
      editingId: null,
      form: this.getEmptyForm(),
      _searchTimer: null
    };
  },
  mounted() {
    this.loadTreks();
    this.loadStaff();
    if (this.$route.query.action === 'new') {
      this.openNew();
    }
  },
  beforeDestroy() {
    clearTimeout(this._searchTimer);
  },
  computed: {
    allowedStatuses() {
      if (!this.form.staff_id) {
        return ['Pending'];
      }
      if (!this.isEditing) {
        return ['Pending', 'Approved'];
      }
      const curr = this.form.status;
      if (curr === 'Pending' || curr === 'Approved') {
        return ['Pending', 'Approved'];
      }
      if (curr === 'Open' || curr === 'Closed' || curr === 'Completed') {
        return ['Open', 'Closed', 'Completed'];
      }
      return [curr];
    }
  },
  watch: {
    'form.start_date'(val) {
      if (val && this.form.duration > 0) {
        const start = new Date(val);
        const end = new Date(start);
        end.setDate(end.getDate() + parseInt(this.form.duration));
        const formatted = end.toISOString().split('T')[0];
        if (this.form.end_date !== formatted) {
          this.form.end_date = formatted;
        }
      }
    },
    'form.duration'(val) {
      if (this.form.start_date && val > 0) {
        const start = new Date(this.form.start_date);
        const end = new Date(start);
        end.setDate(end.getDate() + parseInt(val));
        const formatted = end.toISOString().split('T')[0];
        if (this.form.end_date !== formatted) {
          this.form.end_date = formatted;
        }
      }
    },
    'form.end_date'(val) {
      if (this.form.start_date && val) {
        const start = new Date(this.form.start_date);
        const end = new Date(val);
        const diffTime = end - start;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        if (diffDays > 0 && this.form.duration !== diffDays) {
          this.form.duration = diffDays;
        }
      }
    },
    'form.staff_id'(newVal) {
      if (!newVal) {
        this.form.status = 'Pending';
      } else {
        if (this.form.status === 'Pending') {
          // Keep as Pending
        } else if (this.form.status !== 'Approved') {
          this.form.status = 'Pending';
        }
      }
    }
  },
  methods: {
    getEmptyForm() {
      return {
        name: '',
        location: '',
        difficulty: 'Moderate',
        duration: 5,
        total_slots: 15,
        staff_id: null,
        status: 'Pending',
        start_date: '',
        end_date: '',
        description: '',
        highlights: '',
        included: '',
        not_included: '',
        altitude: null,
        price: 0,
        meeting_point: '',
        equipment_needed: ''
      };
    },
    async loadTreks() {
      this.loading = true;
      try {
        const query = this.search ? '?q=' + encodeURIComponent(this.search) : '';
        this.treks = await this.$api.get('/admin/treks' + query);
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.loading = false;
      }
    },
    async loadStaff() {
      try {
        this.staff = await this.$api.get('/admin/staff');
      } catch (e) {}
    },
    debounceSearch() {
      clearTimeout(this._searchTimer);
      this._searchTimer = setTimeout(() => {
        this.loadTreks();
      }, 450);
    },
    openNew() {
      this.isEditing = false;
      this.editingId = null;
      this.form = this.getEmptyForm();
      this.showModal = true;
    },
    openEdit(t) {
      this.isEditing = true;
      this.editingId = t.id;
      this.form = {
        name: t.name,
        location: t.location,
        difficulty: t.difficulty,
        duration: t.duration,
        total_slots: t.total_slots,
        staff_id: t.staff_id,
        status: t.status,
        start_date: t.start_date || '',
        end_date: t.end_date || '',
        description: t.description || '',
        highlights: t.highlights || '',
        included: t.included || '',
        not_included: t.not_included || '',
        altitude: t.altitude,
        price: t.price,
        meeting_point: t.meeting_point || '',
        equipment_needed: t.equipment_needed || ''
      };
      this.showModal = true;
    },
    closeModal() {
      this.showModal = false;
      this.form = this.getEmptyForm();
    },
    async save() {
      if (!this.form.name || !this.form.location || !this.form.duration || !this.form.total_slots) {
        this.$root.toast('Please fill all required fields.', 'warning');
        return;
      }
      this.saving = true;
      try {
        if (this.isEditing) {
          await this.$api.put('/admin/treks/' + this.editingId, this.form);
          this.$root.toast('Trek updated!');
        } else {
          await this.$api.post('/admin/treks', this.form);
          this.$root.toast('Trek created!');
        }
        this.closeModal();
        await this.loadTreks();
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.saving = false;
      }
    },
    async del(t) {
      if (!confirm(`Delete trek "${t.name}" permanently?`)) return;
      try {
        await this.$api.delete('/admin/treks/' + t.id);
        this.$root.toast('Deleted');
        await this.loadTreks();
      } catch (e) {
        this.$root.toast(e.message, 'error');
      }
    }
  }
};
</script>
