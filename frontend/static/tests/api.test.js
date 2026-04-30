/**
 * Unit tests for API Service Module
 * Tests API request handling, error handling, and response parsing
 */

describe('ApiService', () => {
  let apiService;
  let fetchSpy;

  beforeEach(() => {
    // Mock fetch before importing ApiService
    global.fetch = jest.fn();
    fetchSpy = global.fetch;

    // Import or reinitialize ApiService for each test
    apiService = new ApiService('/api');
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('constructor', () => {
    test('should initialize with default baseUrl', () => {
      const service = new ApiService();
      expect(service.baseUrl).toBe('');
    });

    test('should initialize with custom baseUrl', () => {
      const service = new ApiService('/api/v1');
      expect(service.baseUrl).toBe('/api/v1');
    });

    test('should set default timeout', () => {
      expect(apiService.timeout).toBe(30000);
    });

    test('should set default headers', () => {
      expect(apiService.defaultHeaders).toHaveProperty('Content-Type', 'application/json');
    });
  });

  describe('GET requests', () => {
    test('should make GET request', async () => {
      const mockResponse = { status: 'ok' };
      fetchSpy.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockResponse
      });

      const result = await apiService.get('/status');

      expect(fetchSpy).toHaveBeenCalledWith(
        '/api/status',
        expect.objectContaining({ method: 'GET' })
      );
      expect(result).toEqual(mockResponse);
    });

    test('should handle GET request without JSON response', async () => {
      const mockText = 'text response';
      fetchSpy.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'text/plain' }),
        text: async () => mockText
      });

      const result = await apiService.get('/text');

      expect(result).toBe(mockText);
    });
  });

  describe('POST requests', () => {
    test('should make POST request with body', async () => {
      const mockResponse = { id: 1, created: true };
      const postData = { name: 'test' };

      fetchSpy.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockResponse
      });

      const result = await apiService.post('/items', postData);

      expect(fetchSpy).toHaveBeenCalledWith(
        '/api/items',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(postData)
        })
      );
      expect(result).toEqual(mockResponse);
    });

    test('should serialize object body to JSON', async () => {
      const body = { test: 'data', number: 42 };
      fetchSpy.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({})
      });

      await apiService.post('/endpoint', body);

      const callArgs = fetchSpy.mock.calls[0][1];
      expect(callArgs.body).toBe(JSON.stringify(body));
    });
  });

  describe('error handling', () => {
    test('should throw ApiError on HTTP error', async () => {
      fetchSpy.mockResolvedValueOnce({
        ok: false,
        status: 404,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ error: 'Not found' })
      });

      await expect(apiService.get('/notfound')).rejects.toThrow('Not found');
    });

    test('should throw ApiError on network error', async () => {
      fetchSpy.mockRejectedValueOnce(new Error('Network error'));

      await expect(apiService.get('/endpoint')).rejects.toThrow('Network error');
    });

    test('should handle timeout', async () => {
      const abortController = jest.spyOn(global, 'AbortController', 'get');
      const mockAbort = { abort: jest.fn() };
      abortController.mockReturnValue(mockAbort);

      jest.useFakeTimers();
      const promise = apiService.get('/slow', { timeout: 1000 });
      jest.advanceTimersByTime(1000);

      jest.useRealTimers();

      // Verify abort was called
      expect(mockAbort.abort).toHaveBeenCalled();

      abortController.mockRestore();
    });

    test('should throw ApiError on invalid JSON response', async () => {
      fetchSpy.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => {
          throw new SyntaxError('Invalid JSON');
        }
      });

      await expect(apiService.get('/endpoint')).rejects.toThrow('Invalid response format');
    });
  });

  describe('header handling', () => {
    test('should merge custom headers with defaults', async () => {
      fetchSpy.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({})
      });

      const customHeaders = { 'Authorization': 'Bearer token123' };
      await apiService.get('/endpoint', { headers: customHeaders });

      const callArgs = fetchSpy.mock.calls[0][1];
      expect(callArgs.headers).toHaveProperty('Content-Type', 'application/json');
      expect(callArgs.headers).toHaveProperty('Authorization', 'Bearer token123');
    });
  });

  describe('content type detection', () => {
    test('should parse JSON response', async () => {
      const jsonData = { key: 'value' };
      fetchSpy.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => jsonData
      });

      const result = await apiService.get('/endpoint');

      expect(result).toEqual(jsonData);
    });

    test('should parse text response', async () => {
      const textData = 'plain text response';
      fetchSpy.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'text/plain' }),
        text: async () => textData
      });

      const result = await apiService.get('/endpoint');

      expect(result).toBe(textData);
    });
  });
});
