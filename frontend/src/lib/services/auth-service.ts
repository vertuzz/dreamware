import api from '../api';
import type { User } from '../types';

export const authService = {
    login: async (credentials: any) => {
        // FastAPI OAuth2PasswordRequestForm expects FormData
        const formData = new FormData();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);

        const response = await api.post('/auth/login', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });

        if (response.data.access_token) {
            localStorage.setItem('token', response.data.access_token);
        }
        return response.data;
    },

    signup: async (userData: any) => {
        const response = await api.post('/auth/register', userData);
        return response.data;
    },

    getMe: async (): Promise<User> => {
        const response = await api.get('/auth/me');
        return response.data;
    },

    googleLogin: async (code: string) => {
        const response = await api.post('/auth/google', { code });
        if (response.data.access_token) {
            localStorage.setItem('token', response.data.access_token);
        }
        return response.data;
    },

    githubLogin: async (code: string) => {
        const response = await api.post('/auth/github', { code });
        if (response.data.access_token) {
            localStorage.setItem('token', response.data.access_token);
        }
        return response.data;
    },

    logout: () => {
        localStorage.removeItem('token');
    },
};
