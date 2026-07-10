import Vue from 'vue';
import VueRouter from 'vue-router';

// Lazy load components for cleaner modularity
import Login from '@/views/LoginView.vue';
import Register from '@/views/Register.vue';
import AdminDashboard from '@/views/AdminDashboard.vue';
import ManageTreks from '@/views/ManageTreks.vue';
import ManageStaff from '@/views/ManageStaff.vue';
import ManageUsers from '@/views/ManageUsers.vue';
import AdminBookings from '@/views/AdminBookings.vue';
import StaffDashboard from '@/views/StaffDashboard.vue';
import TrekList from '@/views/TrekList.vue';
import UserDashboard from '@/views/UserDashboard.vue';
import BookingHistory from '@/views/BookingHistory.vue';
import Wishlist from '@/views/Wishlist.vue';
import Profile from '@/views/Profile.vue';

Vue.use(VueRouter);

const router = new VueRouter({
  mode: 'hash',
  routes: [
    { path: '/',                redirect: '/login' },
    { path: '/login',           component: Login,          meta: { guest: true } },
    { path: '/register',        component: Register,       meta: { guest: true } },
    { path: '/admin/dashboard', component: AdminDashboard, meta: { role: 'admin' } },
    { path: '/admin/treks',     component: ManageTreks,    meta: { role: 'admin' } },
    { path: '/admin/staff',     component: ManageStaff,    meta: { role: 'admin' } },
    { path: '/admin/users',     component: ManageUsers,    meta: { role: 'admin' } },
    { path: '/admin/bookings',  component: AdminBookings,  meta: { role: 'admin' } },
    { path: '/staff/dashboard', component: StaffDashboard, meta: { role: 'staff' } },
    { path: '/treks',           component: TrekList },
    { path: '/dashboard',       component: UserDashboard,  meta: { role: 'user' } },
    { path: '/bookings',        component: BookingHistory, meta: { role: 'user' } },
    { path: '/wishlist',        component: Wishlist,       meta: { role: 'user' } },
    { path: '/profile',         component: Profile,        meta: { auth: true } },
  ],
  scrollBehavior: () => ({ x: 0, y: 0 }),
});

router.beforeEach((to, from, next) => {
  const u = JSON.parse(localStorage.getItem('tma_user') || 'null');
  
  // If user is logged in and tries to access guest pages (login/register)
  if (to.meta.guest && u) {
    if (u.role === 'admin') return next('/admin/dashboard');
    if (u.role === 'staff') return next('/staff/dashboard');
    return next('/dashboard');
  }
  
  // If route requires auth/role and user is not logged in
  if ((to.meta.auth || to.meta.role) && !u) {
    return next('/login');
  }
  
  // If user role doesn't match the route role, redirect to their proper dashboard
  if (to.meta.role && u && u.role !== to.meta.role) {
    if (u.role === 'admin') return next('/admin/dashboard');
    if (u.role === 'staff') return next('/staff/dashboard');
    return next('/dashboard');
  }
  
  next();
});

export default router;
