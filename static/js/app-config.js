(function () {
  const localOverride = localStorage.getItem('api_base_url') || '';
  const isLocalHost = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost';
  const defaultBase = isLocalHost ? 'http://127.0.0.1:8000' : window.location.origin;

  const apiBaseUrl = (localOverride || defaultBase).replace(/\/+$/, '');

  window.APP_CONFIG = Object.freeze({
    API_BASE_URL: apiBaseUrl
  });
})();
