import api from '../api';
import type { Tag } from '../types';

export const tagService = {
    getTags: async (): Promise<Tag[]> => {
        const response = await api.get('/tags/');
        return response.data;
    }
};
