// Authentication utility functions

/**
 * Store authentication token in localStorage
 */
function storeAuthToken(accessToken, tokenType = 'bearer') {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('token_type', tokenType);
}

/**
 * Get authentication token from localStorage
 */
function getAuthToken() {
    const accessToken = localStorage.getItem('access_token');
    const tokenType = localStorage.getItem('token_type');
    
    if (!accessToken) {
        return null;
    }
    
    return {
        accessToken,
        tokenType
    };
}

/**
 * Clear authentication token from localStorage
 */
function clearAuthToken() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return getAuthToken() !== null;
}

/**
 * Get authorization header for API requests
 */
function getAuthHeader() {
    const token = getAuthToken();
    if (!token) {
        return {};
    }
    
    // Capitalize token type (e.g., "bearer" -> "Bearer")
    const tokenType = token.tokenType.charAt(0).toUpperCase() + token.tokenType.slice(1);
    
    return {
        'Authorization': `${tokenType} ${token.accessToken}`
    };
}

/**
 * Make authenticated API request
 */
async function authenticatedFetch(url, options = {}) {
    const authHeader = getAuthHeader();
    
    const response = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            ...authHeader
        }
    });
    
    // If unauthorized, clear token and redirect to login
    if (response.status === 401) {
        clearAuthToken();
        window.location.href = '/auth/login';
        throw new Error('Unauthorized');
    }
    
    return response;
}

/**
 * Redirect to dashboard if already authenticated
 */
function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        window.location.href = '/dashboard/';
    }
}

/**
 * Require authentication - redirect to login if not authenticated
 */
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/auth/login';
    }
}

/**
 * Logout user
 */
function logout() {
    clearAuthToken();
    window.location.href = '/auth/login';
}

// Made with Bob
