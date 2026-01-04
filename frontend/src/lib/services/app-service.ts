import api from '../api';
import type { App, AppCreate, Comment, CommentCreate, Tag, Tool, OwnershipClaim, DeadAppReport, DeadAppReportCreate, DeadAppReportResolve } from '../types';

export interface AppQueryParams {
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
    include_dead?: boolean;
    sort_by?: 'trending' | 'newest' | 'top_rated' | 'likes';
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    pages: number;
}

// Simple in-memory cache for static data (tags, tools)
const staticCache: {
    tags: { data: Tag[] | null; promise: Promise<Tag[]> | null };
    tools: { data: Tool[] | null; promise: Promise<Tool[]> | null };
} = {
    tags: { data: null, promise: null },
    tools: { data: null, promise: null },
};

export const appService = {
    getApps: async (params?: AppQueryParams): Promise<App[]> => {
        const response = await api.get('/apps/', { params });
        return Array.isArray(response.data) ? response.data : [];
    },

    getApp: async (id: number | string): Promise<App> => {
        const response = await api.get(`/apps/${id}`);
        return response.data;
    },

    createApp: async (app: AppCreate): Promise<App> => {
        const response = await api.post('/apps/', app);
        return response.data;
    },

    updateApp: async (id: number, app: Partial<AppCreate>): Promise<App> => {
        const response = await api.patch(`/apps/${id}`, app);
        return response.data;
    },

    forkApp: async (id: number): Promise<App> => {
        const response = await api.post(`/apps/${id}/fork`);
        return response.data;
    },

    deleteApp: async (id: number): Promise<void> => {
        await api.delete(`/apps/${id}`);
    },

    // Like endpoints
    likeApp: async (id: number): Promise<void> => {
        await api.post(`/apps/${id}/like`);
    },

    unlikeApp: async (id: number): Promise<void> => {
        await api.delete(`/apps/${id}/like`);
    },

    // Comment endpoints
    getComments: async (appId: number): Promise<Comment[]> => {
        const response = await api.get(`/apps/${appId}/comments`);
        return response.data;
    },

    createComment: async (appId: number, comment: CommentCreate): Promise<Comment> => {
        const response = await api.post(`/apps/${appId}/comments`, comment);
        return response.data;
    },

    likeComment: async (commentId: number): Promise<void> => {
        await api.post(`/comments/${commentId}/like`);
    },

    unlikeComment: async (commentId: number): Promise<void> => {
        await api.delete(`/comments/${commentId}/like`);
    },

    getTags: async (): Promise<Tag[]> => {
        // Return cached data if available
        if (staticCache.tags.data) {
            return staticCache.tags.data;
        }
        // Return existing promise if request is in flight (deduplication)
        if (staticCache.tags.promise) {
            return staticCache.tags.promise;
        }
        // Make request and cache both the promise and result
        staticCache.tags.promise = api.get('/tags/').then(response => {
            staticCache.tags.data = Array.isArray(response.data) ? response.data : [];
            staticCache.tags.promise = null;
            return staticCache.tags.data;
        }).catch(err => {
            staticCache.tags.promise = null;
            throw err;
        });
        return staticCache.tags.promise;
    },

    getTools: async (): Promise<Tool[]> => {
        // Return cached data if available
        if (staticCache.tools.data) {
            return staticCache.tools.data;
        }
        // Return existing promise if request is in flight (deduplication)
        if (staticCache.tools.promise) {
            return staticCache.tools.promise;
        }
        // Make request and cache both the promise and result
        staticCache.tools.promise = api.get('/tools/').then(response => {
            staticCache.tools.data = Array.isArray(response.data) ? response.data : [];
            staticCache.tools.promise = null;
            return staticCache.tools.data;
        }).catch(err => {
            staticCache.tools.promise = null;
            throw err;
        });
        return staticCache.tools.promise;
    },

    // Ownership Claim endpoints
    claimOwnership: async (appId: number, message?: string): Promise<OwnershipClaim> => {
        const response = await api.post(`/apps/${appId}/claim-ownership`, { message });
        return response.data;
    },

    getAppClaims: async (appId: number): Promise<OwnershipClaim[]> => {
        const response = await api.get(`/apps/${appId}/ownership-claims`);
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

    // Dead App Report endpoints
    reportDeadApp: async (appId: number, data?: DeadAppReportCreate): Promise<DeadAppReport> => {
        const response = await api.post(`/apps/${appId}/report-dead`, data || {});
        return response.data;
    },

    getPendingDeadReports: async (): Promise<DeadAppReport[]> => {
        const response = await api.get('/apps/dead-reports/pending');
        return response.data;
    },

    resolveDeadReport: async (reportId: number, data: DeadAppReportResolve): Promise<DeadAppReport> => {
        const response = await api.put(`/apps/dead-reports/${reportId}/resolve`, data);
        return response.data;
    },
};
