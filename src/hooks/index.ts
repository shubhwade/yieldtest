/**
 * Custom React Hooks for API operations
 * Provides reusable data fetching patterns
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { fetchAPI } from './api';

interface UseFetchState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Hook for fetching data from API endpoints
 */
export function useFetch<T = unknown>(
  endpoint: string,
  options?: RequestInit
): UseFetchState<T> & { refetch: () => Promise<void> } {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAPI<T>(endpoint, options);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [endpoint, options]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

/**
 * Hook for polling API at intervals
 */
export function usePollAPI<T = unknown>(
  endpoint: string,
  interval: number = 30000,
  options?: RequestInit
): UseFetchState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const poll = async () => {
      try {
        const result = await fetchAPI<T>(endpoint, options);
        setData(result);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setLoading(false);
      }
    };

    poll();
    const timer = setInterval(poll, interval);
    return () => clearInterval(timer);
  }, [endpoint, interval, options]);

  return { data, loading, error };
}

/**
 * Hook for debounced API calls (e.g., search)
 */
export function useDebouncedAPI<T = unknown>(
  fn: (query: string) => Promise<T>,
  delay: number = 300
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(
    (query: string) => {
      const timer = setTimeout(async () => {
        if (!query) {
          setData(null);
          return;
        }
        setLoading(true);
        try {
          const result = await fn(query);
          setData(result);
          setError(null);
        } catch (err) {
          setError(err instanceof Error ? err : new Error('Unknown error'));
        } finally {
          setLoading(false);
        }
      }, delay);

      return () => clearTimeout(timer);
    },
    [fn, delay]
  );

  return { data, loading, error, execute };
}

/**
 * Hook for mutation operations (POST, PUT, DELETE)
 */
export function useMutation<T = unknown, P = unknown>(
  fn: (payload: P) => Promise<T>
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mutate = useCallback(
    async (payload: P) => {
      setLoading(true);
      setError(null);
      try {
        const result = await fn(payload);
        setData(result);
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Unknown error');
        setError(error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [fn]
  );

  return { data, loading, error, mutate };
}
