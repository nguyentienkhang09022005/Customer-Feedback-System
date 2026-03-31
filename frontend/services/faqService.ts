/**
 * FAQ Service - API calls for FAQ endpoints
 * 
 * Uses the unified /api/v1/faqs/public endpoint which returns
 * paginated lists with content included.
 * 
 * @see docs/specs/2026-03-31-faq-frontend-integration-guide.md
 */

import type {
  FAQPublicItem,
  FAQPublicListResponse,
  FAQListParams,
  APIResponse,
  MAX_FAQ_LIMIT,
} from '../types/faq';
import { DEFAULT_FAQ_PARAMS } from '../types/faq';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Build query string from params object
 */
function buildQueryString(params: FAQListParams): string {
  const searchParams = new URLSearchParams();
  
  if (params.article_id) {
    searchParams.append('article_id', params.article_id);
  }
  if (params.category_id) {
    searchParams.append('category_id', params.category_id);
  }
  if (params.page !== undefined) {
    searchParams.append('page', String(params.page));
  }
  if (params.limit !== undefined) {
    // Enforce max limit
    const limit = Math.min(params.limit, 100);
    searchParams.append('limit', String(limit));
  }
  if (params.search) {
    searchParams.append('search', params.search);
  }
  
  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
}

/**
 * Fetch with error handling
 */
async function fetchWithErrorHandling<T>(url: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const result: APIResponse<T> = await response.json();
  
  if (!result.status) {
    throw new Error(result.message || 'API request failed');
  }
  
  return result.data;
}

/**
 * FAQService - Methods for fetching FAQ data
 */
export const faqService = {
  /**
   * Fetch paginated list of FAQs
   * 
   * @param params - Query parameters (page, limit, category_id, search)
   * @returns Promise with paginated FAQ list and metadata
   * 
   * @example
   * // Fetch first page with 20 items
   * const { items, meta } = await faqService.getFAQs({ page: 1, limit: 20 });
   * 
   * @example
   * // Filter by category
   * const { items, meta } = await faqService.getFAQs({ category_id: 'cat-123' });
   * 
   * @example
   * // Search FAQs
   * const { items, meta } = await faqService.getFAQs({ search: 'password' });
   */
  async getFAQs(params: FAQListParams = {}): Promise<FAQPublicListResponse> {
    const mergedParams: FAQListParams = {
      ...DEFAULT_FAQ_PARAMS,
      ...params,
    };
    
    const queryString = buildQueryString(mergedParams);
    return fetchWithErrorHandling<FAQPublicListResponse>(`/api/v1/faqs/public${queryString}`);
  },
  
  /**
   * Fetch a single FAQ by ID
   * 
   * Note: This uses the same endpoint with article_id param.
   * Content is returned directly (no nested structure needed).
   * 
   * @param articleId - The FAQ article UUID
   * @returns Promise with single FAQ item
   * 
   * @example
   * const faq = await faqService.getFAQById('550e8400-e29b-41d4-a716-446655440000');
   * console.log(faq.title, faq.content);
   */
  async getFAQById(articleId: string): Promise<FAQPublicItem> {
    const queryString = buildQueryString({ article_id: articleId });
    return fetchWithErrorHandling<FAQPublicItem>(`/api/v1/faqs/public${queryString}`);
  },
  
  /**
   * Fetch FAQs filtered by category
   * 
   * @param categoryId - The category UUID
   * @param page - Page number (default: 1)
   * @param limit - Items per page (default: 20, max: 100)
   * @returns Promise with paginated FAQ list
   */
  async getFAQsByCategory(
    categoryId: string,
    page: number = DEFAULT_FAQ_PARAMS.page,
    limit: number = DEFAULT_FAQ_PARAMS.limit
  ): Promise<FAQPublicListResponse> {
    return this.getFAQs({ category_id: categoryId, page, limit });
  },
  
  /**
   * Search FAQs by keyword
   * 
   * @param searchTerm - Search term to match against title and content
   * @param page - Page number (default: 1)
   * @param limit - Items per page (default: 20, max: 100)
   * @returns Promise with paginated search results
   */
  async searchFAQs(
    searchTerm: string,
    page: number = DEFAULT_FAQ_PARAMS.page,
    limit: number = DEFAULT_FAQ_PARAMS.limit
  ): Promise<FAQPublicListResponse> {
    return this.getFAQs({ search: searchTerm, page, limit });
  },
};

export default faqService;
