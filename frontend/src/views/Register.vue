<template>
  <div class="container d-flex justify-content-center align-items-center" style="padding: 50px 0;">
    <!-- Clean Bootstrap border-dark card layout (widened to 800px) -->
    <div class="card border-dark shadow-sm" style="max-width: 800px; width: 100%;">
      <div class="card-body p-4">
        
        <!-- Header with solid border-bottom -->
        <h2 class="card-title text-center text-dark border-bottom border-dark pb-2 mb-4 fw-bold">
          Registration Form
        </h2>
        
        <!-- Basic Information Section -->
        <div class="mb-4 pb-3 border-bottom border-secondary" style="border-bottom-style: dashed !important;">
          <h5 class="fw-bold text-dark mb-3">Basic Information</h5>
          
          <!-- Full Name -->
          <div class="mb-3">
            <label class="form-label fw-bold text-dark">Full Name *</label>
            <input 
              v-model="form.name" 
              type="text" 
              class="form-control border-dark" 
              placeholder="Your full name" 
              required
            />
          </div>

          <!-- Username and Email (Row layout) -->
          <div class="row mb-3">
            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Username *</label>
              <input 
                v-model="form.username" 
                type="text" 
                class="form-control border-dark" 
                placeholder="Min 3 characters" 
                required
              />
              <div class="mt-1">
                <span class="text-muted small" v-if="checkingU">checking...</span>
                <span class="badge bg-secondary text-white small" v-else-if="usernameAvail === true">Available</span>
                <span class="badge bg-dark text-white small" v-else-if="usernameAvail === false">Taken</span>
              </div>
            </div>

            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Email *</label>
              <input 
                v-model="form.email" 
                type="email" 
                class="form-control border-dark" 
                placeholder="your@email.com" 
                required
              />
              <div class="mt-1">
                <span class="text-muted small" v-if="checkingE">checking...</span>
                <span class="badge bg-secondary text-white small" v-else-if="emailAvail === true">Available</span>
                <span class="badge bg-dark text-white small" v-else-if="emailAvail === false">Registered</span>
              </div>
            </div>
          </div>

          <!-- Phone Number -->
          <div class="mb-3">
            <label class="form-label fw-bold text-dark">Phone Number</label>
            <input 
              v-model="form.phone" 
              type="tel" 
              class="form-control border-dark" 
              placeholder="+91 XXXXXXXXXX" 
            />
          </div>

          <!-- Password and Confirm Password (Row layout) -->
          <div class="row">
            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Password *</label>
              <input 
                v-model="form.password" 
                type="password" 
                class="form-control border-dark" 
                placeholder="Create password" 
                required
              />
              <div v-if="form.password" class="text-muted small mt-1">
                Strength: <span class="fw-bold text-dark">{{ pwdLabel }}</span>
              </div>
            </div>

            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Confirm Password *</label>
              <input 
                v-model="form.confirm" 
                type="password" 
                class="form-control border-dark" 
                placeholder="Repeat password" 
                required
              />
              <div class="mt-1" v-if="form.confirm && !pwdMatch">
                <span class="badge bg-dark text-white small">Passwords do not match</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Trekker Profile Section -->
        <div class="mb-4">
          <h5 class="fw-bold text-dark mb-3">Trekker Profile</h5>

          <!-- Experience and Fitness Level (Row layout) -->
          <div class="row mb-3">
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

          <!-- Emergency Contact and Emergency Phone (Row layout) -->
          <div class="row">
            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Emergency Contact Name</label>
              <input 
                v-model="form.emergency_contact" 
                type="text" 
                class="form-control border-dark" 
                placeholder="Contact name" 
              />
            </div>

            <div class="col-md-6">
              <label class="form-label fw-bold text-dark">Emergency Phone</label>
              <input 
                v-model="form.emergency_phone" 
                type="tel" 
                class="form-control border-dark" 
                placeholder="+91 XXXXXXXXXX" 
              />
            </div>
          </div>
        </div>

        <!-- Submit Button -->
        <div class="text-center mt-4">
          <button 
            @click="register" 
            :disabled="loading || !formValid" 
            class="btn btn-dark w-100 fw-bold border-dark"
          >
            <span v-if="loading">Creating Account...</span>
            <span v-else>Create Account</span>
          </button>
        </div>

        <!-- Navigation Footer -->
        <div class="text-center mt-4 pt-3 border-top" style="border-top: 1px dashed #6c757d !important; font-size: 14px;">
          Already have an account? 
          <router-link to="/login" class="text-dark fw-bold text-decoration-underline">Sign In</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Register',
  data() {
    return {
      form: {
        username: '',
        email: '',
        password: '',
        confirm: '',
        name: '',
        phone: '',
        experience_level: 'Beginner',
        fitness_level: 'Medium',
        emergency_contact: '',
        emergency_phone: ''
      },
      loading: false,
      usernameAvail: null,
      emailAvail: null,
      checkingU: false,
      checkingE: false,
      _uT: null,
      _eT: null,
    };
  },
  beforeDestroy() {
    clearTimeout(this._uT);
    clearTimeout(this._eT);
  },
  watch: {
    'form.username'(v) {
      this.usernameAvail = null;
      this.checkingU = false;
      clearTimeout(this._uT);
      if (!v || v.trim().length < 3) return;
      this.checkingU = true;
      this._uT = setTimeout(async () => {
        try {
          const r = await axios.get('http://127.0.0.1:5000/api/auth/check?field=username&value=' + encodeURIComponent(v.trim()));
          if (this.form.username === v) this.usernameAvail = r.data.available;
        } catch (e) {
        } finally {
          this.checkingU = false;
        }
      }, 500);
    },
    'form.email'(v) {
      this.emailAvail = null;
      this.checkingE = false;
      clearTimeout(this._eT);
      if (!v || !v.includes('@')) return;
      this.checkingE = true;
      this._eT = setTimeout(async () => {
        try {
          const r = await axios.get('http://127.0.0.1:5000/api/auth/check?field=email&value=' + encodeURIComponent(v.trim()));
          if (this.form.email === v) this.emailAvail = r.data.available;
        } catch (e) {
        } finally {
          this.checkingE = false;
        }
      }, 500);
    },
  },
  computed: {
    pwdStr() {
      const p = this.form.password;
      let s = 0;
      if (p.length >= 6) s++;
      if (p.length >= 10) s++;
      if (/[A-Z]/.test(p)) s++;
      if (/[0-9]/.test(p)) s++;
      if (/[^A-Za-z0-9]/.test(p)) s++;
      return s;
    },
    pwdLabel() {
      return ['', 'Very Weak', 'Weak', 'Fair', 'Strong', 'Very Strong'][this.pwdStr] || '';
    },
    pwdMatch() {
      if (!this.form.confirm) return null;
      return this.form.password === this.form.confirm;
    },
    formValid() {
      return (
        this.form.name.trim() &&
        this.form.username.length >= 3 &&
        this.usernameAvail === true &&
        this.form.email.includes('@') &&
        this.emailAvail === true &&
        this.pwdStr >= 2 &&
        this.pwdMatch === true
      );
    },
  },
  methods: {
    async register() {
      if (!this.formValid) return;
      this.loading = true;
      try {
        await axios.post('http://127.0.0.1:5000/api/auth/register', {
          username: this.form.username,
          email: this.form.email,
          password: this.form.password,
          name: this.form.name,
          phone: this.form.phone,
          experience_level: this.form.experience_level,
          fitness_level: this.form.fitness_level,
          emergency_contact: this.form.emergency_contact,
          emergency_phone: this.form.emergency_phone,
        });
        // Redirect to Login passing success status query parameter
        this.$router.push({ path: '/login', query: { registered: 'success' } });
      } catch (e) {
        const errorMsg = e.response?.data?.error || e.message || 'Registration failed';
        this.$root.toast(errorMsg, 'error');
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
