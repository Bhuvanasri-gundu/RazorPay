const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || `API Error: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchMetrics() {
  return fetchAPI<any>('/api/dashboard/metrics');
}

export async function fetchAnalytics() {
  return fetchAPI<any>('/api/dashboard/analytics');
}

export async function fetchCases(params?: Record<string, any>) {
  let url = '/api/cases';
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
  }
  return fetchAPI<any>(url);
}

export async function fetchCase(id: string) {
  return fetchAPI<any>(`/api/cases/${id}`);
}

export async function analyzeCase(id: string) {
  return fetchAPI<any>(`/api/cases/${id}/analyze`, { method: 'POST' });
}

export async function executeCase(id: string) {
  return fetchAPI<any>(`/api/cases/${id}/execute`, { method: 'POST' });
}

export async function approveCase(id: string) {
  return fetchAPI<any>(`/api/cases/${id}/approve`, { method: 'POST' });
}

export async function runDemoScenario(scenario: number) {
  return fetchAPI<any>('/api/demo/run-scenario', {
    method: 'POST',
    body: JSON.stringify({ scenario }),
  });
}

export async function runCustomScenario(data: any) {
  return fetchAPI<any>('/api/demo/run-custom-scenario', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function runBatchSimulation() {
  return fetchAPI<any>('/api/simulation/run-batch', { method: 'POST' });
}

export async function createPaymentLink(data: any) {
  return fetchAPI<any>('/api/payments/create-link', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function verifyPayment(data: any) {
  return fetchAPI<any>('/api/payments/verify', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function seedDatabase() {
  return fetchAPI<any>('/api/seed', { method: 'POST' });
}

export async function healthCheck() {
  return fetchAPI<any>('/api/health');
}
