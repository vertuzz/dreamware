import api from '../api';
import type { Dream, DreamCreate, Comment, CommentCreate, Tag, Tool, OwnershipClaim } from '../types';

export interface DreamQueryParams {
    skip?: number;
    limit?: number;
    tool_id?: number | number[];
    tag_id?: number | number[];
    tool?: string;
    tag?: string;
    search?: string;
    status?: 'Concept' | 'WIP' | 'Live';
    creator_id?: number;
    liked_by_user_id?: number;
    sort_by?: 'trending' | 'newest' | 'top_rated' | 'likes';
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    pages: number;
}

export const dreamService = {
    getDreams: async (params?: DreamQueryParams): Promise<Dream[]> => {
        const response = await api.get('/dreams/', { params });
        return response.data;
    },

    getDream: async (id: number | string): Promise<Dream> => {
        const response = await api.get(`/dreams/${id}`);
        return response.data;
    },

    createDream: async (dream: DreamCreate): Promise<Dream> => {
        const response = await api.post('/dreams/', dream);
        return response.data;
    },

    updateDream: async (id: number, dream: Partial<DreamCreate>): Promise<Dream> => {
        const response = await api.patch(`/dreams/${id}`, dream);
        return response.data;
    },

    forkDream: async (id: number): Promise<Dream> => {
        const response = await api.post(`/dreams/${id}/fork`);
        return response.data;
    },

    deleteDream: async (id: number): Promise<void> => {
        await api.delete(`/dreams/${id}`);
    },

    // Like endpoints
    likeDream: async (id: number): Promise<void> => {
        await api.post(`/dreams/${id}/like`);
    },

    unlikeDream: async (id: number): Promise<void> => {
        await api.delete(`/dreams/${id}/like`);
    },

    // Comment endpoints
    getComments: async (dreamId: number): Promise<Comment[]> => {
        const response = await api.get(`/dreams/${dreamId}/comments`);
        return response.data;
    },

    createComment: async (dreamId: number, comment: CommentCreate): Promise<Comment> => {
        const response = await api.post(`/dreams/${dreamId}/comments`, comment);
        return response.data;
    },

    likeComment: async (commentId: number): Promise<void> => {
        await api.post(`/comments/${commentId}/like`);
    },

    unlikeComment: async (commentId: number): Promise<void> => {
        await api.delete(`/comments/${commentId}/like`);
    },

    getTags: async (): Promise<Tag[]> => {
        const response = await api.get('/tags/');
        return response.data;
    },

    getTools: async (): Promise<Tool[]> => {
        const response = await api.get('/tools/');
        return response.data;
    },

    // Ownership Claim endpoints
    claimOwnership: async (dreamId: number, message?: string): Promise<OwnershipClaim> => {
        const response = await api.post(`/dreams/${dreamId}/claim-ownership`, { message });
        return response.data;
    },

    getDreamClaims: async (dreamId: number): Promise<OwnershipClaim[]> => {
        const response = await api.get(`/dreams/${dreamId}/ownership-claims`);
        return response.data;
    },

    getPendingClaims: async (): Promise<OwnershipClaim[]> => {
        const response = await api.get('/ownership-claims');
        return response.data;
    },

    resolveClaim: async (claimId: number, status: 'approved' | 'rejected'): Promise<OwnershipClaim> => {
        const response = await api.put(`/ownership-claims/${claimId}/resolve`, null, { params: { status } });
        return response.data;
    },
};
