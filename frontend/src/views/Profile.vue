<template>
  <div class="container py-4">
    <h2 class="fw-bold mb-4 pb-2 border-bottom border-dark">My Profile Settings</h2>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-dark" role="status"></div>
    </div>
    
    <div v-else-if="user" class="card border-dark shadow-sm p-4 mx-auto" style="max-width: 650px;">
      <div class="card-body p-0">
        <!-- Account settings -->
        <div class="mb-4 pb-3 border-bottom border-secondary" style="border-bottom-style: dashed !important;">
          <h5 class="fw-bold text-dark mb-3">Basic Account Details</h5>
          
          <div class="row g-3 mb-3">
            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Full Name *</label>
              <input v-model="form.name" type="text" class="form-control border-dark" placeholder="Your name" required />
            </div>
            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Email *</label>
              <input v-model="form.email" type="email" class="form-control border-dark" placeholder="Your email" required />
            </div>
          </div>

          <div class="row g-3 mb-3">
            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Phone</label>
              <input v-model="form.phone" type="text" class="form-control border-dark" placeholder="+91 XXXXXXXXXX" />
            </div>
            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Password (blank to keep current)</label>
              <input v-model="form.password" type="password" class="form-control border-dark" placeholder="New password" />
            </div>
          </div>

          <div class="mb-2">
            <label class="form-label fw-bold text-dark">Bio</label>
            <textarea v-model="form.bio" rows="2" class="form-control border-dark" placeholder="Write something about yourself..."></textarea>
          </div>
        </div>

        <!-- Trekker-specific details (role = user) -->
        <div class="mb-4" v-if="user.role === 'user'">
          <h5 class="fw-bold text-dark mb-3">Trekker Profile Attributes</h5>
          
          <div class="row g-3 mb-3">
            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Experience Level</label>
              <select v-model="form.experience_level" class="form-select border-dark">
                <option>Beginner</option>
                <option>Intermediate</option>
                <option>Expert</option>
              </select>
            </div>
            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Fitness Level</label>
              <select v-model="form.fitness_level" class="form-select border-dark">
                <option>Low</option>
                <option>Medium</option>
                <option>High</option>
              </select>
            </div>
          </div>

          <div class="row g-3 mb-3">
            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Emergency Contact Name</label>
              <input v-model="form.emergency_contact" type="text" class="form-control border-dark" placeholder="Contact name" />
            </div>
            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Emergency Phone</label>
              <input v-model="form.emergency_phone" type="text" class="form-control border-dark" placeholder="+91 XXXXXXXXXX" />
            </div>
          </div>

          <div class="mb-2">
            <label class="form-label fw-bold text-dark">Medical Notes</label>
            <textarea v-model="form.medical_notes" rows="2" class="form-control border-dark" placeholder="Asthma, allergies, heart conditions, etc."></textarea>
          </div>
        </div>

        <!-- Guide-specific details (role = staff) -->
        <div class="mb-4" v-if="user.role === 'staff'">
          <h5 class="fw-bold text-dark mb-3">Guide Credentials</h5>
          
          <div class="row g-3 mb-3">
            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Specialization</label>
              <input v-model="form.specialization" type="text" class="form-control border-dark" placeholder="e.g. Winter Hikes" />
            </div>
            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Years of Experience</label>
              <input v-model.number="form.years_experience" type="number" min="0" class="form-control border-dark" />
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label fw-bold text-dark">Languages spoken</label>
            <input v-model="form.languages" type="text" class="form-control border-dark" placeholder="English, Hindi" />
          </div>

          <div class="mb-2">
            <label class="form-label fw-bold text-dark">Certifications</label>
            <textarea v-model="form.certifications" rows="2" class="form-control border-dark" placeholder="e.g. NIM Grades, Wilderness First Aid"></textarea>
          </div>
        </div>

        <button @click="save" :disabled="saving" class="btn btn-dark fw-bold w-100 mt-2">
          {{ saving ? 'Saving Changes...' : 'Save Settings' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Profile',
  data() {
    return {
      user: null,
      loading: true,
      saving: false,
      form: {
        name: '',
        email: '',
        password: '',
        phone: '',
        bio: '',
        experience_level: 'Beginner',
        fitness_level: 'Medium',
        preferred_difficulty: '',
        emergency_contact: '',
        emergency_phone: '',
        medical_notes: '',
        specialization: '',
        certifications: '',
        years_experience: 0,
        languages: 'Hindi, English'
      }
    };
  },
  mounted() {
    this.load();
  },
  methods: {
    async load() {
      this.loading = true;
      try {
        const d = await this.$api.get('/auth/profile');
        this.user = d;
        this.form = {
          name: d.name,
          email: d.email,
          password: '',
          phone: d.phone,
          bio: d.bio,
          experience_level: d.trekker_info ? d.trekker_info.experience_level || 'Beginner' : 'Beginner',
          fitness_level: d.trekker_info ? d.trekker_info.fitness_level || 'Medium' : 'Medium',
          preferred_difficulty: d.trekker_info ? d.trekker_info.preferred_difficulty || '' : '',
          emergency_contact: d.trekker_info ? d.trekker_info.emergency_contact || '' : '',
          emergency_phone: d.trekker_info ? d.trekker_info.emergency_phone || '' : '',
          medical_notes: d.trekker_info ? d.trekker_info.medical_notes || '' : '',
          specialization: d.staff_info ? d.staff_info.specialization || '' : '',
          certifications: d.staff_info ? d.staff_info.certifications || '' : '',
          years_experience: d.staff_info ? d.staff_info.years_experience || 0 : 0,
          languages: d.staff_info ? d.staff_info.languages || 'Hindi, English' : 'Hindi, English'
        };
      } catch (e) {
        this.$root.toast(e.message, 'error');
      } finally {
        this.loading = false;
      }
    },
    async save() {
      if (!this.form.name || !this.form.email) {
        this.$root.toast('Name and email are required.', 'warning');
        return;
      }
      this.saving = true;
      try {
        const payload = { ...this.form };
        if (!payload.password) delete payload.password; // Don't send empty password
        const res = await this.$api.put('/auth/profile', payload);
        this.$root.setUser(res.user);
        this.$root.toast('Profile updated successfully!');
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
