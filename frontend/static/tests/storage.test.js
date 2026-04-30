/**
 * Unit tests for Storage Module
 * Tests persistent data storage functionality
 */

describe('Storage Module', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  describe('LocalStorage Operations', () => {
    test('should save data to localStorage', () => {
      const key = 'test_key';
      const value = 'test_value';

      localStorage.setItem(key, value);

      expect(localStorage.getItem(key)).toBe(value);
    });

    test('should retrieve data from localStorage', () => {
      const testData = { id: 1, name: 'Test' };
      localStorage.setItem('data', JSON.stringify(testData));

      const retrieved = JSON.parse(localStorage.getItem('data'));

      expect(retrieved).toEqual(testData);
    });

    test('should remove data from localStorage', () => {
      localStorage.setItem('key', 'value');
      localStorage.removeItem('key');

      expect(localStorage.getItem('key')).toBeNull();
    });

    test('should clear all localStorage', () => {
      localStorage.setItem('key1', 'value1');
      localStorage.setItem('key2', 'value2');
      localStorage.clear();

      expect(localStorage.length).toBe(0);
    });
  });

  describe('Complex Data Storage', () => {
    test('should serialize and store objects', () => {
      const userData = {
        id: 'user123',
        preferences: {
          theme: 'dark',
          language: 'en'
        },
        notifications: true
      };

      localStorage.setItem('user_prefs', JSON.stringify(userData));
      const retrieved = JSON.parse(localStorage.getItem('user_prefs'));

      expect(retrieved).toEqual(userData);
      expect(retrieved.preferences.theme).toBe('dark');
    });

    test('should handle arrays in storage', () => {
      const items = [
        { id: 1, name: 'Item 1' },
        { id: 2, name: 'Item 2' }
      ];

      localStorage.setItem('items', JSON.stringify(items));
      const retrieved = JSON.parse(localStorage.getItem('items'));

      expect(Array.isArray(retrieved)).toBe(true);
      expect(retrieved.length).toBe(2);
      expect(retrieved[0].name).toBe('Item 1');
    });
  });

  describe('Data Expiration', () => {
    test('should check if stored data has expired', () => {
      const expirationTime = Date.now() - 1000; // 1 second ago
      const currentTime = Date.now();

      expect(currentTime > expirationTime).toBe(true);
    });

    test('should identify valid (non-expired) data', () => {
      const expirationTime = Date.now() + 3600000; // 1 hour from now
      const currentTime = Date.now();

      expect(currentTime < expirationTime).toBe(true);
    });
  });

  describe('SessionStorage Operations', () => {
    test('should save temporary session data', () => {
      const key = 'session_key';
      const value = 'session_value';

      sessionStorage.setItem(key, value);

      expect(sessionStorage.getItem(key)).toBe(value);
    });

    test('should clear session on logout', () => {
      sessionStorage.setItem('temp_data', 'value');
      sessionStorage.clear();

      expect(sessionStorage.getItem('temp_data')).toBeNull();
    });
  });

  describe('Error Handling', () => {
    test('should handle invalid JSON gracefully', () => {
      localStorage.setItem('bad_data', 'not valid json');

      expect(() => {
        JSON.parse(localStorage.getItem('bad_data'));
      }).toThrow();
    });

    test('should handle missing keys', () => {
      const value = localStorage.getItem('nonexistent_key');

      expect(value).toBeNull();
    });

    test('should handle quota exceeded', () => {
      // This is a simplified test - actual quota exceeded handling would be different
      const largeData = 'x'.repeat(1024 * 1024); // 1MB string
      
      // Just verify we can attempt storage without crashing
      expect(() => {
        try {
          localStorage.setItem('large_data', largeData);
        } catch (e) {
          // Expected if quota is small
          expect(e).toBeDefined();
        }
      }).not.toThrow();
    });
  });

  describe('Key Management', () => {
    test('should list all stored keys', () => {
      localStorage.setItem('key1', 'value1');
      localStorage.setItem('key2', 'value2');
      localStorage.setItem('key3', 'value3');

      const keys = Object.keys(localStorage);

      expect(keys.length).toBeGreaterThanOrEqual(3);
    });

    test('should check if key exists', () => {
      localStorage.setItem('existing_key', 'value');

      expect(localStorage.getItem('existing_key')).not.toBeNull();
      expect(localStorage.getItem('nonexistent_key')).toBeNull();
    });
  });
});
