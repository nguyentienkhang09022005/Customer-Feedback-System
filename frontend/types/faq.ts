/**
 * FAQ TypeScript Type Definitions
 * 
 * These types correspond to the unified FAQ API endpoint:
 * GET /api/v1/faqs/public
 * 
 * @see docs/specs/2026-03-31-faq-frontend-integration-guide.md
 */

/**
 * Author information embedded in FAQ items
 */
export interface FAQAuthor {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
}

/**
 * Category information embedded in FAQ items
 */
export interface FAQCategory {
  id_category: string | null;
  name: string | null;
}

/**
 * Individual FAQ item returned in list and detail responses
 * Note: Content is now included in list responses (unlike the old API)
 */
export interface FAQPublicItem {
  id_article: string;
  title: string;
  content: string;
  view_count: number;
  is_published: boolean;
  created_at: string;
  updated_at: string;
  id_category: string | null;
  id_author: string;
  author: FAQAuthor | null;
  category: FAQCategory | null;
}

/**
 * Pagination metadata for list responses
 */
export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

/**
 * Paginated list response structure
 */
export interface FAQPublicListResponse {
  items: FAQPublicItem[];
  meta: PaginationMeta;
}

/**
 * Generic API response wrapper
 */
export interface APIResponse<T> {
  status: boolean;
  code: number;
  message: string;
  data: T;
}

/**
 * Query parameters for FAQ list endpoint
 */
export interface FAQListParams {
  article_id?: string;
  category_id?: string;
  page?: number;
  limit?: number;
  search?: string;
}

/**
 * Default pagination settings
 */
export const DEFAULT_FAQ_PARAMS: Required<Omit<FAQListParams, 'article_id' | 'category_id' | 'search'>> = {
  page: 1,
  limit: 20,
};

/**
 * Maximum allowed items per page
 */
export const MAX_FAQ_LIMIT = 100;
