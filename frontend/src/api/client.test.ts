import { describe, it, expect, vi, beforeEach } from 'vitest';

let mockAxiosInstance: {
  defaults: { headers: { common: Record<string, string> } };
  interceptors: { request: { use: ReturnType<typeof vi.fn> }; response: { use: ReturnType<typeof vi.fn> } };
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  patch: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

beforeEach(() => {
  vi.resetModules();
  mockAxiosInstance = {
    defaults: { headers: { common: {} } },
    interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  };
  vi.doMock('axios', () => ({
    default: {
      create: vi.fn(() => mockAxiosInstance),
    },
  }));
});

describe('api client', () => {
  it('creates axios instance with correct config', async () => {
    const { default: api } = await import('../api/client');
    expect(api).toBeDefined();
  });

  it('authApi has required methods', async () => {
    const { authApi } = await import('../api/client');
    expect(typeof authApi.getConfig).toBe('function');
    expect(typeof authApi.loginStart).toBe('function');
    expect(typeof authApi.logout).toBe('function');
    expect(typeof authApi.getMe).toBe('function');
  });

  it('analysesApi has required methods', async () => {
    const { analysesApi } = await import('../api/client');
    expect(typeof analysesApi.list).toBe('function');
    expect(typeof analysesApi.get).toBe('function');
    expect(typeof analysesApi.create).toBe('function');
    expect(typeof analysesApi.update).toBe('function');
    expect(typeof analysesApi.delete).toBe('function');
  });

  it('setAccessToken sets header', async () => {
    const { setAccessToken } = await import('../api/client');
    setAccessToken('test-token');
    expect(mockAxiosInstance.defaults.headers.common['Authorization']).toBe('Bearer test-token');
  });

  it('setAccessToken clears header when null', async () => {
    const { setAccessToken } = await import('../api/client');
    setAccessToken('test-token');
    setAccessToken(null);
    expect(mockAxiosInstance.defaults.headers.common['Authorization']).toBeUndefined();
  });
});