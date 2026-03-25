(function () {
  function showSessionToast(message) {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.position = 'fixed';
    toast.style.right = '20px';
    toast.style.bottom = '20px';
    toast.style.zIndex = '4000';
    toast.style.background = '#ECFDF5';
    toast.style.color = '#065F46';
    toast.style.border = '1px solid #6EE7B7';
    toast.style.borderRadius = '8px';
    toast.style.padding = '10px 12px';
    toast.style.fontSize = '0.86rem';
    toast.style.boxShadow = '0 8px 20px rgba(0,0,0,0.12)';
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 150ms ease';
    document.body.appendChild(toast);
    requestAnimationFrame(() => {
      toast.style.opacity = '1';
    });
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 200);
    }, 1600);
  }

  async function refreshAuthToken() {
    try {
      const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/api/auth/refresh/`, {
        method: 'POST',
        credentials: 'include',
      });
      if (response.ok) {
        showSessionToast('Session renewed.');
      }
      return response.ok;
    } catch {
      return false;
    }
  }

  window.authApiFetch = async function authApiFetch(url, options = {}) {
    const requestOptions = {
      credentials: 'include',
      ...options,
    };

    let response = await fetch(url, requestOptions);
    if (response.status !== 401) return response;

    const refreshed = await refreshAuthToken();
    if (!refreshed) {
      sessionStorage.removeItem('user');
      if (!window.location.pathname.endsWith('/login.html')) {
        window.location.href = 'login.html';
      }
      throw new Error('AUTH_EXPIRED');
    }

    response = await fetch(url, requestOptions);
    if (response.status === 401) {
      sessionStorage.removeItem('user');
      if (!window.location.pathname.endsWith('/login.html')) {
        window.location.href = 'login.html';
      }
      throw new Error('AUTH_EXPIRED');
    }

    return response;
  };
})();
