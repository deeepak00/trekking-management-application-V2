<template>
  <div class="container d-flex justify-content-center align-items-center" style="padding-top: 100px;">
    <!-- Clean Bootstrap border-dark card layout -->
    <div class="card border-dark shadow-sm" style="max-width: 420px; width: 100%;">
      <div class="card-body p-4">
        
        <!-- Header with solid border-bottom -->
        <h2 class="card-title text-center text-dark border-bottom border-dark pb-2 mb-4 fw-bold">
          Login Form
        </h2>
        
        <!-- Success Alert Box for Registration -->
        <div v-if="showSuccess" class="alert alert-success text-center text-success border-success py-2 mb-3 fw-bold">
          Account created successfully! Please login.
        </div>

        <!-- Secondary Alert Box for Error Handling -->
        <div v-if="error" class="alert alert-secondary text-center text-danger border-dark py-2 mb-3 fw-bold">
          {{ error }}
        </div>

        <!-- Login Form -->
        <form @submit.prevent="handleLogin">
          <!-- Username Input -->
          <div class="mb-3">
            <label class="form-label fw-bold text-dark">Username</label>
            <input
              v-model="form.email"
              type="text"
              class="form-control border-dark"
              placeholder="Enter Username"
              required
            />
          </div>

          <!-- Password Input -->
          <div class="mb-4">
            <label class="form-label fw-bold text-dark">Password</label>
            <input
              v-model="form.password"
              type="password"
              class="form-control border-dark"
              placeholder="Enter Password"
              required
            />
          </div>

          <!-- Submit Button (btn-dark for solid black styling) -->
          <div class="text-center">
            <button type="submit" class="btn btn-dark w-100 fw-bold border-dark" :disabled="loading">
              {{ loading ? 'Loading...' : 'Login' }}
            </button>
          </div>
        </form>

        <!-- Navigation Footer -->
        <div class="text-center mt-4 pt-3 border-top" style="border-top: 1px dashed #6c757d !important; font-size: 14px;">
          Do not have an account? 
          <router-link to="/register" class="text-dark fw-bold text-decoration-underline">Register</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'LoginView',
  data() {
    return {
      form: {
        email: '',
        password: ''
      },
      loading: false,
      error: '',
      showSuccess: false
    }
  },
  mounted() {
    if (this.$route.query.registered === 'success') {
      this.showSuccess = true
      setTimeout(() => {
        this.showSuccess = false
        // Remove the query parameter so refreshing doesn't show it again
        this.$router.replace({ query: {} }).catch(() => {})
      }, 3000)
    }
  },
  methods: {
    async handleLogin() {
      this.loading = true
      this.error = ''
      try {
        const resp = await axios.post('http://127.0.0.1:5000/api/auth/login', {
          username: this.form.email,
          password: this.form.password
        })
        
        const token = resp.data.token || resp.data.access_token
        const user = resp.data.user
        
        localStorage.setItem('token', token)
        localStorage.setItem('tma_token', token)
        localStorage.setItem('role', user.role)
        localStorage.setItem('email', user.email)
        localStorage.setItem('tma_user', JSON.stringify(user))
        
        this.$root.setUser(user)
        this.$root.toast('Welcome back, ' + user.name.split(' ')[0] + '!')
        
        const role = user.role
        if (role === 'admin') {
          this.$router.push('/admin/dashboard')
        } else if (role === 'staff') {
          this.$router.push('/staff/dashboard')
        } else {
          this.$router.push('/dashboard')
        }
      } catch (e) {
        this.error = e.response?.data?.error || 'Wrong credentials'
        this.form.password = ''
        clearTimeout(this._errTimer)
        this._errTimer = setTimeout(() => {
          this.error = ''
        }, 3000)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
