import api from '../api';
import type { User, Notification, UserLink, UserUpdate } from '../types';

export const userService = {
    getUser: async (id: string | number): Promise<User> => {
        const response = await api.get(`/users/${id}`);
        return response.data;
    },

    updateUser: async (userId: number, data: UserUpdate): Promise<User> => {
        const response = await api.patch(`/users/${userId}`, data);
        return response.data;
    },

    createUserLink: async (userId: number, link: { label: string; url: string }): Promise<UserLink> => {
        const response = await api.post(`/users/${userId}/links`, link);
        return response.data;
    },

    deleteUserLink: async (userId: number, linkId: number): Promise<void> => {
        await api.delete(`/users/${userId}/links/${linkId}`);
    },

    followUser: async (userId: number): Promise<{ message: string }> => {
        const response = await api.post(`/users/${userId}/follow`);
        return response.data;
    },

    unfollowUser: async (userId: number): Promise<{ message: string }> => {
        const response = await api.delete(`/users/${userId}/follow`);
        return response.data;
    },

    checkFollowStatus: async (userId: number): Promise<{ is_following: boolean }> => {
        const response = await api.get(`/users/${userId}/follow/status`);
        return response.data;
    },

    getNotifications: async (): Promise<Notification[]> => {
        const response = await api.get('/notifications/');
        return response.data;
    },

    markNotificationRead: async (id: number): Promise<Notification> => {
        const response = await api.patch(`/notifications/${id}/read`);
        return response.data;
    },

    markAllNotificationsRead: async (): Promise<{ message: string }> => {
        const response = await api.patch('/notifications/read-all');
        return response.data;
    },

    regenerateApiKey: async (): Promise<User> => {
        const response = await api.post('/auth/api-key/regenerate');
        return response.data;
    },
};
