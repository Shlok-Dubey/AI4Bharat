/**
 * Authentication utility functions
 */

/**
 * Get JWT token from localStorage
 */
export const getToken = () => {
    return localStorage.getItem('token')
}

/**
 * Get user data from localStorage
 */
export const getUser = () => {
    const userData = localStorage.getItem('user')
    return userData ? JSON.parse(userData) : null
}

/**
 * Check if user is authenticated
 */
export const isAuthenticated = () => {
    return !!getToken()
}

/**
 * Clear authentication data
 */
export const clearAuth = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
}

/**
 * Set authentication data
 */
export const setAuth = (token, user) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
}

/**
 * Get axios config with auth header
 */
export const getAuthConfig = () => {
    const token = getToken()
    return {
        headers: {
            Authorization: `Bearer ${token}`
        }
    }
}

