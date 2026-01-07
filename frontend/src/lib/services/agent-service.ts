import api from '~/lib/api';

export interface AgentStatus {
    configured: boolean;
    model: string | null;
    api_base: string | null;
    headless: boolean;
}

export interface AgentRunResponse {
    success: boolean;
    result: string | null;
    error: string | null;
    app_ids: number[];
}

export const agentService = {
    async getStatus(): Promise<AgentStatus> {
        const response = await api.get('/agent/status');
        return response.data;
    },

    async runAgent(prompt: string): Promise<AgentRunResponse> {
        const response = await api.post('/agent/run', { prompt });
        return response.data;
    }
};
