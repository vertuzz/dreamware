import api from '../api';
import type { Tool } from '../types';

export const toolService = {
    getTools: async (): Promise<Tool[]> => {
        const response = await api.get('/tools/');
        return response.data;
    }
};
