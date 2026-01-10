/**
 * MediCare - Doctor Appointment System
 * Main JavaScript Application - CONNECTED TO DJANGO
 */

// ==========================================
// Configuration
// ==========================================
const API_BASE_URL = 'http://localhost:8000/api';

// ==========================================
// State Management
// ==========================================
let currentUser = null;
let blockedUsers = new Set();

// ==========================================
// Utility Functions
// ==========================================
function $(selector) {
  return document.querySelector(selector);
}

function $$(selector) {
  return document.querySelectorAll(selector);
}

function formatDate(dateStr) {
  const options = { year: 'numeric', month: 'short', day: 'numeric' };
  return new Date(dateStr).toLocaleDateString('en-US', options);
}

function getInitials(name) {
  return name.split(' ').map(n => n[0]).join('').toUpperCase();
}

// ==========================================
// API Helper Functions (REAL Django API)
// ==========================================
const API = {
  // GET /api/users/doctors/
  getDoctors: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/doctors/`);
      if (!response.ok) throw new Error('Failed to fetch doctors');
      return await response.json();
    } catch (error) {
      console.error('Error fetching doctors:', error);
      showToast('Error', 'Could not load doctors. Using demo data.', 'error');
      // Fallback to demo data
      return [
        {
          id: 1,
          name: 'Dr. Sarah Johnson',
          email: 'sarah.johnson@medicare.com',
          specialization: 'Cardiologist',
          experience: 12,
          rating: 4.9,
          consultation_fee: 150,
          bio: 'Board-certified cardiologist with expertise in preventive cardiology.'
        }
      ];
    }
  },
  
  // GET /api/users/{id}/
  getDoctor: async (id) => {
    const response = await fetch(`${API_BASE_URL}/users/${id}/`);
    return await response.json();
  },
  
  // POST /api/auth/login/
  login: async (username, password) => {
    const response = await fetch(`${API_BASE_URL}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }
    
    const data = await response.json();
    // Store tokens
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    
    // Get user profile
    const userResponse = await fetch(`${API_BASE_URL}/users/profile/`, {
      headers: {
        'Authorization': `Bearer ${data.access}`
      }
    });
    
    if (userResponse.ok) {
      const userData = await userResponse.json();
      localStorage.setItem('user', JSON.stringify(userData));
      return userData;
    }
    
    return data;
  },
  
  // GET /api/appointments/
  getAppointments: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_BASE_URL}/appointments/`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) throw new Error('Failed to fetch appointments');
    return await response.json();
  },
  
  // GET /api/appointments/?patient_id=xxx
  getPatientAppointments: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_BASE_URL}/appointments/`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) throw new Error('Failed to fetch appointments');
    const allAppointments = await response.json();
    
    // Filter client-side (or backend can filter)
    const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
    return allAppointments.filter(apt => apt.patient === currentUser.id);
  },
  
  // POST /api/appointments/
  createAppointment: async (data) => {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_BASE_URL}/appointments/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create appointment');
    }
    
    return await response.json();
  },
  
  // POST /api/appointments/{id}/update_status/
  updateAppointmentStatus: async (id, status) => {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_BASE_URL}/appointments/${id}/update_status/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ status })
    });
    
    if (!response.ok) throw new Error('Failed to update appointment');
    return await response.json();
  },
  
  // POST /api/appointments/{id}/cancel/
  cancelAppointment: async (id) => {
    return API.updateAppointmentStatus(id, 'cancelled');
  }
};

// ==========================================
// Authentication Functions (UPDATED)
// ==========================================
async function login(email, password, role) {
  try {
    // Use Django login API
    const user = await API.login(email, password);
    
    // Store user info
    currentUser = {
      id: user.id,
      name: user.first_name + ' ' + user.last_name,
      email: user.email,
      role: user.role,
      specialization: user.specialization || '',
      consultation_fee: user.consultation_fee || 0,
      rating: user.rating || 0
    };
    
    localStorage.setItem('user', JSON.stringify(currentUser));
    showToast('Success', 'Login successful!', 'success');
    
    // Redirect based on role
    setTimeout(() => {
      if (user.role === 'patient') {
        window.location.href = 'doctors.html';
      } else if (user.role === 'doctor') {
        window.location.href = 'doctor-dashboard.html';
      } else if (user.role === 'admin') {
        window.location.href = 'admin-dashboard.html';
      }
    }, 1000);
    
    return true;
  } catch (error) {
    console.error('Login error:', error);
    showToast('Login Failed', error.message || 'Invalid credentials', 'error');
    return false;
  }
}

function logout() {
  // Clear all stored data
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  currentUser = null;
  
  // Redirect to login
  window.location.href = 'login.html';
}

function checkAuth() {
  const token = localStorage.getItem('access_token');
  const storedUser = localStorage.getItem('user');
  
  if (token && storedUser) {
    currentUser = JSON.parse(storedUser);
    return true;
  }
  
  return false;
}

function requireAuth(allowedRoles = []) {
  if (!checkAuth()) {
    window.location.href = 'login.html';
    return false;
  }
  
  if (allowedRoles.length > 0 && !allowedRoles.includes(currentUser.role)) {
    window.location.href = 'index.html';
    return false;
  }
  
  return true;
}

// ==========================================
// Toast Notifications (Keep as is)
// ==========================================
function showToast(title, message, type = 'success') {
  let container = $('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-title">${title}</div>
    <div class="toast-message">${message}</div>
  `;
  
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ==========================================
// UI Component Renderers (UPDATED)
// ==========================================
function renderHeader() {
  const header = $('#main-header');
  if (!header) return;
  
  const isLoggedIn = checkAuth();
  
  let navLinks = '';
  let userSection = '';
  
  if (isLoggedIn && currentUser) {
    switch (currentUser.role) {
      case 'patient':
        navLinks = `
          <a href="doctors.html" class="nav-link">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
            Find Doctors
          </a>
          <a href="patient-appointments.html" class="nav-link">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            My Appointments
          </a>
        `;
        break;
      case 'doctor':
        navLinks = `
          <a href="doctor-dashboard.html" class="nav-link">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
            Dashboard
          </a>
          <a href="doctor-schedule.html" class="nav-link">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            My Schedule
          </a>
        `;
        break;
      case 'admin':
        navLinks = `
          <a href="admin-dashboard.html" class="nav-link">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
            Dashboard
          </a>
          <a href="admin-users.html" class="nav-link">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            Users
          </a>
          <a href="admin-appointments.html" class="nav-link">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            Appointments
          </a>
        `;
        break;
    }
    
    userSection = `
      <div class="user-info">
        <div class="user-avatar">${getInitials(currentUser.name)}</div>
        <div class="user-details">
          <span class="user-name">${currentUser.name}</span>
          <span class="user-role">${currentUser.role}</span>
        </div>
      </div>
      <button class="btn btn-outline btn-sm" onclick="logout()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
        Logout
      </button>
    `;
  } else {
    userSection = `
      <a href="login.html" class="btn btn-ghost">Login</a>
      <a href="register.html" class="btn btn-primary">Get Started</a>
    `;
  }
  
  header.innerHTML = `
    <div class="container">
      <div class="header-inner">
        <a href="index.html" class="logo">
          <div class="logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
          </div>
          <span class="logo-text">MediCare</span>
        </a>
        
        <nav class="nav">${navLinks}</nav>
        
        <div class="header-actions">${userSection}</div>
      </div>
    </div>
  `;
}

async function renderDoctorCard(doctor) {
  // Generate time slots (you can replace with real API later)
  const timeSlots = generateTimeSlots();
  const availableSlots = timeSlots.filter(s => s.available);
  const uniqueDates = [...new Set(availableSlots.map(s => s.date))].slice(0, 5);
  
  return `
    <div class="card doctor-card" data-doctor-id="${doctor.id}">
      <div class="doctor-header">
        <div class="avatar avatar-lg">
          <div class="avatar-placeholder">${getInitials(doctor.name)}</div>
        </div>
        <div class="doctor-info">
          <h3 class="doctor-name">${doctor.name}</h3>
          <span class="badge badge-secondary">${doctor.specialization}</span>
          <div class="doctor-meta">
            <span class="doctor-rating">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
              ${doctor.rating || 4.5}
            </span>
            <span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              ${doctor.experience || 5} yrs
            </span>
          </div>
        </div>
      </div>
      <div class="card-content">
        <p class="doctor-bio">${doctor.bio || 'Experienced medical professional'}</p>
        <div class="doctor-fee">
          <span class="fee-amount">$${doctor.consultation_fee || 100}<small>/visit</small></span>
          <span class="slots-available">${availableSlots.length} slots available</span>
        </div>
        <button class="btn btn-outline w-full" onclick="toggleSlots('${doctor.id}')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          View Available Slots
        </button>
        <div class="slots-container hidden" id="slots-${doctor.id}">
          <div class="date-pills">
            ${uniqueDates.map((date, i) => `
              <button class="date-pill ${i === 0 ? 'active' : ''}" data-date="${date}" onclick="selectDate('${doctor.id}', '${date}')">
                ${formatDate(date)}
              </button>
            `).join('')}
          </div>
          <div class="time-slots" id="time-slots-${doctor.id}">
            ${renderTimeSlots(doctor.id, uniqueDates[0], availableSlots)}
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderTimeSlots(doctorId, selectedDate, slots) {
  const dateSlots = slots.filter(s => s.date === selectedDate && s.available);
  
  if (dateSlots.length === 0) {
    return '<p class="text-center text-muted">No slots available for this date</p>';
  }
  
  return dateSlots.map(slot => `
    <button class="time-slot" onclick="openBookingModal(${doctorId}, '${slot.date}', '${slot.time}')">
      ${slot.time}
    </button>
  `).join('');
}

// Helper function for time slots (temporary)
function generateTimeSlots() {
  const times = ['09:00 AM', '10:00 AM', '11:00 AM', '02:00 PM', '03:00 PM', '04:00 PM'];
  const slots = [];
  
  for (let day = 1; day <= 5; day++) {
    const date = new Date();
    date.setDate(date.getDate() + day);
    const dateStr = date.toISOString().split('T')[0];
    
    times.forEach(time => {
      slots.push({
        date: dateStr,
        time: time,
        available: Math.random() > 0.3,
      });
    });
  }
  
  return slots;
}

// ==========================================
// Page Initialization
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  renderHeader();
  initTabs();
  
  // Load doctors on doctors.html page
  if (window.location.pathname.includes('doctors.html')) {
    loadDoctors();
  }
});

// Load doctors function
async function loadDoctors() {
  const doctorsContainer = $('#doctors-container');
  if (!doctorsContainer) return;
  
  try {
    const doctors = await API.getDoctors();
    doctorsContainer.innerHTML = '';
    
    for (const doctor of doctors) {
      const cardHtml = await renderDoctorCard(doctor);
      doctorsContainer.innerHTML += cardHtml;
    }
  } catch (error) {
    console.error('Error loading doctors:', error);
    doctorsContainer.innerHTML = '<p class="text-center text-muted">Failed to load doctors. Please try again.</p>';
  }
}

// Rest of your functions (toggleSlots, selectDate, etc.) remain similar
// Just update them to use the real API calls