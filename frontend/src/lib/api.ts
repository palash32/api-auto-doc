export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

// Helper to get auth token
function getAuthToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
}

export interface Repository {
    id: string;
    name: string;
    full_name: string;
    url: string;
    status: string;
    api_count: number;
    last_scanned: string | null;
    health_score: number;
}

export interface EndpointSummary {
    id: string;
    path: string;
    method: string;
    summary: string;
    tags: string[];
    auth_required: boolean;
}

export interface EndpointDetail {
    id: string;
    path: string;
    method: string;
    summary: string;
    description: string;
    parameters: Record<string, unknown>[];
    request_body?: Record<string, unknown>;
    responses: Record<string, unknown>[];
    auth_required: boolean;
    auth_type?: string;
    file_path: string;
    tags: string[];
}

export interface PaginatedEndpoints {
    total: number;
    page: number;
    per_page: number;
    endpoints: EndpointSummary[];
}

export interface DashboardStats {
    totalRepositories: number;
    totalEndpoints: number;
    avgHealthScore: number;
    lastScanTime: string | null;
    scanningCount: number;
}

export interface ActivityItem {
    id: string;
    type: 'scan_started' | 'scan_completed' | 'scan_failed' | 'repo_added' | 'repo_deleted' | 'docs_generated';
    title: string;
    description?: string;
    repositoryId?: string;
    metadata?: Record<string, any>;
    createdAt: string;
}

export const api = {
    // Repository endpoints
    async getRepositories(): Promise<Repository[]> {
        try {
            const token = getAuthToken();
            const res = await fetch(`${API_BASE_URL}/api/repositories/`, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            if (!res.ok) throw new Error('Failed to fetch repositories');
            return res.json();
        } catch (error) {
            console.error('Error fetching repositories:', error);
            return [];
        }
    },

    async addRepository(url: string): Promise<any> {
        try {
            const token = getAuthToken();
            const res = await fetch(`${API_BASE_URL}/api/repositories/?url=${encodeURIComponent(url)}`, {
                method: 'POST',
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });

            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.detail || 'Failed to add repository');
            }
            return res.json();
        } catch (error) {
            console.error('Error adding repository:', error);
            throw error;
        }
    },

    // Endpoint documentation endpoints
    async getRepositoryEndpoints(
        repoId: string,
        params?: {
            page?: number;
            per_page?: number;
            method?: string;
            tag?: string;
            search?: string;
        }
    ): Promise<PaginatedEndpoints> {
        try {
            const token = getAuthToken();
            const queryParams = new URLSearchParams();

            if (params?.page) queryParams.set('page', params.page.toString());
            if (params?.per_page) queryParams.set('per_page', params.per_page.toString());
            if (params?.method) queryParams.set('method', params.method);
            if (params?.tag) queryParams.set('tag', params.tag);
            if (params?.search) queryParams.set('search', params.search);

            const url = `${API_BASE_URL}/api/repositories/${repoId}/endpoints?${queryParams}`;
            const res = await fetch(url, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });

            if (!res.ok) throw new Error('Failed to fetch endpoints');
            return res.json();
        } catch (error) {
            console.error('Error fetching endpoints:', error);
            return { total: 0, page: 1, per_page: 50, endpoints: [] };
        }
    },

    async getEndpointDetail(endpointId: string): Promise<EndpointDetail | null> {
        try {
            const token = getAuthToken();
            const res = await fetch(`${API_BASE_URL}/api/endpoints/${endpointId}`, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });

            if (!res.ok) throw new Error('Failed to fetch endpoint details');
            return res.json();
        } catch (error) {
            console.error('Error fetching endpoint details:', error);
            return null;
        }
    },

    async updateEndpoint(
        endpointId: string,
        data: {
            summary?: string;
            description?: string;
            tags?: string[];
        }
    ): Promise<EndpointDetail | null> {
        try {
            const token = getAuthToken();
            const res = await fetch(`${API_BASE_URL}/api/endpoints/${endpointId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify(data)
            });

            if (!res.ok) throw new Error('Failed to update endpoint');
            return res.json();
        } catch (error) {
            console.error('Error updating endpoint:', error);
            return null;
        }
    },

    async generateDocs(endpointId: string): Promise<any> {
        try {
            const token = getAuthToken();
            const res = await fetch(`${API_BASE_URL}/api/endpoints/${endpointId}/generate`, {
                method: 'POST',
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });

            if (!res.ok) throw new Error('Failed to generate docs');
            return res.json();
        } catch (error) {
            console.error('Error generating docs:', error);
            throw error;
        }
    },

    // Dashboard endpoints
    async getDashboardStats(): Promise<DashboardStats> {
        try {
            const token = getAuthToken();
            const res = await fetch(`${API_BASE_URL}/api/dashboard/stats`, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            if (!res.ok) throw new Error('Failed to fetch dashboard stats');
            return res.json();
        } catch (error) {
            console.error('Error fetching dashboard stats:', error);
            return {
                totalRepositories: 0,
                totalEndpoints: 0,
                avgHealthScore: 0,
                lastScanTime: null,
                scanningCount: 0
            };
        }
    },

    async getDashboardActivity(limit: number = 10): Promise<ActivityItem[]> {
        try {
            const token = getAuthToken();
            const res = await fetch(`${API_BASE_URL}/api/dashboard/activity?limit=${limit}`, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            if (!res.ok) throw new Error('Failed to fetch activity');
            return res.json();
        } catch (error) {
            console.error('Error fetching activity:', error);
            return [];
        }
    }
};
