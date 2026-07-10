<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4 pb-2 border-bottom border-dark flex-wrap gap-3">
      <h2 class="fw-bold mb-0">Manage Staff Guides</h2>
      <button @click="openNew" class="btn btn-dark fw-bold">Add Staff Guide</button>
    </div>

    <!-- Filter/Search Bar -->
    <div class="card border-dark shadow-sm mb-4">
      <div class="card-body p-3">
        <input 
          v-model="search" 
          type="text" 
          class="form-control border-dark"
          placeholder="Filter staff by name, email, or username..." 
          @input="debounceSearch"
        />
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-dark" role="status"></div>
    </div>
    <div v-else>
      <div v-if="!staff.length" class="card border-dark text-center p-5">
        <p class="text-muted mb-0">No staff members found.</p>
      </div>
      
      <div v-else class="card border-dark shadow-sm p-4">
        <div class="table-responsive" style="max-height: 350px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 4px;">
          <table class="table table-hover table-sm align-middle mb-0" style="table-layout: fixed; width: 100%; font-size: 0.9rem;">
            <colgroup>
              <col style="width: 15%;">
              <col style="width: 25%;">
              <col style="width: 15%;">
              <col style="width: 12%;">
              <col style="width: 13%;">
              <col style="width: 10%;">
              <col style="width: 10%;">
            </colgroup>
            <thead>
              <tr style="border-bottom: 2px solid #000;">
                <th class="fw-bold">Name</th>
                <th class="fw-bold">Contact</th>
                <th class="fw-bold">Specialization</th>
                <th class="fw-bold">Experience</th>
                <th class="fw-bold">Languages</th>
                <th class="fw-bold">Blacklisted</th>
                <th class="fw-bold">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in staff" :key="s.id">
                <td class="fw-bold text-break">
                  {{ s.name }}
                  <div class="text-muted small fw-normal text-break">@{{ s.username }}</div>
                </td>
                <td class="text-break">
                  <div class="text-break">{{ s.email }}</div>
                  <div class="text-muted small text-break">{{ s.phone || 'No phone' }}</div>
                </td>
                <td class="text-break">{{ s.staff_info ? s.staff_info.specialization : 'N/A' }}</td>
                <td class="text-break">{{ s.staff_info ? s.staff_info.years_experience + ' years' : 'N/A' }}</td>
                <td class="text-break">{{ s.staff_info ? s.staff_info.language : 'N/A' }}</td>
                <td>
                  <span class="badge bg-dark text-white">
                    {{ s.status === 'blacklisted' ? 'Blacklisted' : 'No' }}
                  </span>
                </td>
                <td>
                  <div class="d-flex gap-1 flex-wrap">
                    <button @click="openEdit(s)" class="btn btn-outline-dark btn-sm fw-bold">Edit</button>
                    <button @click="toggleBlacklist(s)" class="btn btn-outline-dark btn-sm fw-bold">
                      {{ s.status === 'blacklisted' ? 'Unblacklist' : 'Blacklist' }}
                    </button>
                    <button @click="del(s)" class="btn btn-outline-danger btn-sm fw-bold">Delete</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Simple Custom Modal Overlay for Add/Edit Staff -->
    <div class="modal d-block" tabindex="-1" style="background-color: rgba(0,0,0,0.5);" v-if="showModal">
      <div class="modal-dialog modal-dialog-centered" style="max-width: 600px;">
        <div class="modal-content border-dark">
          <div class="modal-header border-bottom border-dark bg-light">
            <h5 class="modal-title fw-bold">{{ isEditing ? 'Edit Staff' : 'New Staff' }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body p-4">
            <div class="row g-3">
              <div class="col-12">
                <label class="form-label fw-bold text-dark">Full Name *</label>
                <input v-model="form.name" type="text" class="form-control border-dark" placeholder="e.g. Rahul Sharma" required />
              </div>

              <div class="col-md-6">
                <label class="form-label fw-bold text-dark">Username *</label>
                <input v-model="form.username" type="text" class="form-control border-dark" placeholder="username" :disabled="isEditing" required />
                <div class="mt-1" v-if="!isEditing">
                  <span class="text-muted small" v-if="checkingU">checking...</span>
                  <span class="badge bg-secondary text-white small" v-else-if="usernameAvail === true">Available</span>
                  <span class="badge bg-dark text-white small" v-else-if="usernameAvail === false">Taken</span>
                </div>
              </div>
              <div class="col-md-6">
                <label class="form-label fw-bold text-dark">Email *</label>
                <input v-model="form.email" type="email" class="form-control border-dark" placeholder="guide@tma.com" required />
                <div class="mt-1">
                  <span class="text-muted small" v-if="checkingE">checking...</span>
                  <span class="badge bg-secondary text-white small" v-else-if="emailAvail === true && (form.email !== originalEmail)">Available</span>
                  <span class="badge bg-dark text-white small" v-else-if="emailAvail === false">Registered</span>
                </div>
              </div>

              <div class="col-12">
                <label class="form-label fw-bold text-dark">Password {{ isEditing ? '(blank to keep current)' : '*' }}</label>
                <input v-model="form.password" type="password" class="form-control border-dark" placeholder="Min 6 characters" />
              </div>

              <div class="col-12">
                <label class="form-label fw-bold text-dark">Phone</label>
                <input v-model="form.phone" type="tel" class="form-control border-dark" placeholder="+91 XXXXXXXXXX" />
              </div>

              <div class="col-md-6">
                <label class="form-label fw-bold text-dark">Specialization</label>
                <input v-model="form.specialization" type="text" class="form-control border-dark" placeholder="e.g. High Altitude" />
              </div>
              <div class="col-md-6">
                <label class="form-label fw-bold text-dark">Years of Experience</label>
                <input v-model.number="form.years_experience" type="number" min="0" class="form-control border-dark" />
              </div>

              <div class="col-12">
                <label class="form-label fw-bold text-dark">Languages spoken</label>
                <input v-model="form.language" type="text" class="form-control border-dark" placeholder="Hindi, English, Nepali" />
              </div>

              <div class="col-12">
                <label class="form-label fw-bold text-dark">Certifications</label>
                <textarea v-model="form.certification" rows="2" class="form-control border-dark" placeholder="e.g. NIM Basic, First Aid"></textarea>
              </div>
            </div>
            
            <div class="d-flex justify-content-end gap-2 mt-4">
              <button @click="closeModal" :disabled="saving" class="btn btn-outline-danger btn-sm fw-bold">Cancel</button>
              <button @click="save" :disabled="!canSave" class="btn btn-dark btn-sm fw-bold">
                {{ saving ? 'Saving...' : 'Save Staff' }}
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
  name: 'ManageStaff',
  data() {
    return {
      staff: [],
      loading: true,
      saving: false,
      search: '',
      showModal: false,
      isEditing: false,
      editingId: null,
      originalEmail: '',
      form: this.getEmptyForm(),
      _searchTimer: null,
      usernameAvail: null,
      emailAvail: null,
      checkingU: false,
      checkingE: false,
      _uT: null,
      _eT: null
    };
  },
  mounted() {
    this.load();
    if (this.$route.query.action === 'new') {
      this.openNew();
    }
  },
  beforeDestroy() {
    clearTimeout(this._searchTimer);
    clearTimeout(this._uT);
    clearTimeout(this._eT);
  },
  computed: {
    canSave() {
      if (this.saving) return false;
      if (!this.form.name || !this.form.email || !this.form.username) return false;
      if (this.isEditing) {
        if (this.form.email !== this.originalEmail) {
          return this.emailAvail === true && !this.checkingE;
        }
        return true;
      }
      return (
        this.form.username.trim().length >= 3 &&
        this.usernameAvail === true &&
        this.form.email.includes('@') &&
        this.emailAvail === true &&
        !this.checkingU &&
        !this.checkingE &&
        this.form.password.length >= 6
      );
    }
  },
  watch: {
    'form.username'(v) {
      if (this.isEditing) return;
      this.usernameAvail = null;
      this.checkingU = false;
      clearTimeout(this._uT);
      if (!v || v.trim().length < 3) return;
      this.checkingU = true;
      this._uT = setTimeout(async () => {
        try {
          const r = await this.$api.get('/auth/check?field=username&value=' + encodeURIComponent(v.trim()));
          if (this.form.username === v) this.usernameAvail = r.available;
        } catch (e) {
        } finally {
          this.checkingU = false;
        }
      }, 500);
    },
    'form.email'(v) {
      if (this.isEditing && v === this.originalEmail) {
        this.emailAvail = true;
        this.checkingE = false;
        return;
      }
      this.emailAvail = null;
      this.checkingE = false;
      clearTimeout(this._eT);
      if (!v || !v.includes('@')) return;
      this.checkingE = true;
      this._eT = setTimeout(async () => {
        try {
          const r = await this.$api.get('/auth/check?field=email&value=' + encodeURIComponent(v.trim()));
          if (this.form.email === v) this.emailAvail = r.available;
        } catch (e) {
        } finally {
          this.checkingE = false;
        }
      }, 500);
    }
  },
  methods: {
    getEmptyForm() {
      return {
        username: '',
        email: '',
        password: '',
        name: '',
        phone: '',
        specialization: '',
        years_experience: 0,
        certification: '',
        language: 'Hindi, English'
      };
    },
    async load() {
      this.loading = true;
      try {
        const query = this.search ? '?q=' + encodeURIComponent(this.search) : '';
        this.staff = await this.$api.get('/admin/staff' + query);
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
    openNew() {
      this.isEditing = false;
      this.editingId = null;
      this.originalEmail = '';
      this.form = this.getEmptyForm();
      this.showModal = true;
    },
    openEdit(s) {
      this.isEditing = true;
      this.editingId = s.id;
      this.originalEmail = s.email;
      this.form = {
        username: s.username,
        email: s.email,
        password: '',
        name: s.name,
        phone: s.phone,
        specialization: s.staff_info ? s.staff_info.specialization || '' : '',
        years_experience: s.staff_info ? s.staff_info.years_experience || 0 : 0,
        certification: s.staff_info ? s.staff_info.certification || '' : '',
        language: s.staff_info ? s.staff_info.language || '' : 'Hindi, English'
      };
      this.showModal = true;
    },
    closeModal() {
      this.showModal = false;
      this.form = this.getEmptyForm();
      this.originalEmail = '';
      this.usernameAvail = null;
      this.emailAvail = null;
      this.checkingU = false;
      this.checkingE = false;
    },
    async save() {
      if (!this.form.username || !this.form.email || !this.form.name || (!this.isEditing && !this.form.password)) {
        this.$root.toast('Please fill all required fields.', 'warning');
        return;
      }
      this.saving = true;
      try {
        if (this.isEditing) {
          await this.$api.put('/admin/staff/' + this.editingId, this.form);
          this.$root.toast('Staff guide updated!');
        } else {
          await this.$api.post('/admin/staff', this.form);
          this.$root.toast('Staff guide registered successfully!');
        }
        this.closeModal();
        await this.load();
      } catch (e) {
        const errorMsg = e.response?.data?.error || e.message || 'Saving failed';
        this.$root.toast(errorMsg, 'error');
      } finally {
        this.saving = false;
      }
    },
    async toggleStatus(s) {
      try {
        await this.$api.put('/admin/users/' + s.id + '/status', { is_active: !s.is_active });
        this.$root.toast('Guide active status updated');
        await this.load();
      } catch (e) {
        this.$root.toast(e.message, 'error');
      }
    },
    async toggleBlacklist(s) {
      const isBlack = s.status === 'blacklisted';
      const act = isBlack ? 'Unblacklist' : 'Blacklist';
      if (!confirm(`${act} staff guide "${s.name}"?`)) return;
      try {
        const nextStatus = isBlack ? 'active' : 'blacklisted';
        await this.$api.put('/admin/users/' + s.id + '/status', { status: nextStatus });
        this.$root.toast('Staff blacklist status updated');
        await this.load();
      } catch (e) {
        this.$root.toast(e.message, 'error');
      }
    },
    async del(s) {
      if (!confirm(`Delete guide "${s.name}"? This assigns all their current treks to Unassigned.`)) return;
      try {
        await this.$api.delete('/admin/staff/' + s.id);
        this.$root.toast('Staff guide deleted');
        await this.load();
      } catch (e) {
        this.$root.toast(e.message, 'error');
      }
    }
  }
};
</script>
