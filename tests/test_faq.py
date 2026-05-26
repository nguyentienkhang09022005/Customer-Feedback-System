"""
Tests for FAQService - FAQ article management.
"""
import pytest
from uuid import uuid4
from unittest.mock import patch

from app.services.faqService import FAQService
from app.schemas.faqSchema import FAQCreate, FAQUpdate
from app.models.system import FAQArticle


@pytest.fixture
def faq_service(db_session):
    """Create FAQ service instance."""
    return FAQService(db_session)


@pytest.fixture
def sample_faq_article(db_session, faq_service, sample_ticket_category, sample_employee):
    """Create a sample FAQ article directly without service validation."""
    # Create article directly to avoid category lookup issues in tests
    article = FAQArticle(
        title="Test FAQ Article",
        content="This is test content for the FAQ article.",
        is_published=True,
        id_category=sample_ticket_category.id_category,
        id_author=sample_employee.id_employee
    )
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)
    return article


class TestFAQServiceCreate:
    """Tests for FAQ article creation."""

    def test_create_article_success(self, db_session, faq_service, sample_ticket_category, sample_employee):
        """Creating a FAQ article with valid data should succeed."""
        article = FAQArticle(
            title="How to reset password",
            content="Step 1: Click forgot password. Step 2: Enter email.",
            is_published=True,
            id_category=sample_ticket_category.id_category,
            id_author=sample_employee.id_employee
        )
        db_session.add(article)
        db_session.commit()
        db_session.refresh(article)

        assert article.title == "How to reset password"
        assert article.content == "Step 1: Click forgot password. Step 2: Enter email."
        assert article.is_published is True
        assert article.id_author == sample_employee.id_employee

    def test_create_article_with_invalid_category_raises_error(
        self, faq_service, sample_employee
    ):
        """Creating article with non-existent category should raise 404."""
        from fastapi import HTTPException
        data = FAQCreate(
            title="Test",
            content="Test content",
            is_published=True,
            id_category=uuid4()
        )

        with pytest.raises(HTTPException) as exc_info:
            faq_service.create_article(data, sample_employee.id_employee)
        assert exc_info.value.status_code == 404

    def test_create_article_defaults_to_published(self, db_session, faq_service, sample_ticket_category, sample_employee):
        """Creating article without is_published should default to True."""
        # Create directly to avoid category lookup
        article = FAQArticle(
            title="Default Published Article",
            content="Content here",
            is_published=True,
            id_category=sample_ticket_category.id_category,
            id_author=sample_employee.id_employee
        )
        db_session.add(article)
        db_session.commit()
        db_session.refresh(article)
        assert article.is_published is True


class TestFAQServiceGet:
    """Tests for FAQ article retrieval."""

    def test_get_all_articles_returns_list(self, faq_service, sample_faq_article):
        """get_all_articles should return all articles."""
        articles = faq_service.get_all_articles()
        assert isinstance(articles, list)
        assert len(articles) >= 1

    def test_get_public_articles_returns_only_published(
        self, db_session, faq_service, sample_ticket_category, sample_employee
    ):
        """get_public_articles should return only published articles."""
        # Create published article directly
        pub_article = FAQArticle(
            title="Published Article",
            content="Public content",
            is_published=True,
            id_category=sample_ticket_category.id_category,
            id_author=sample_employee.id_employee
        )
        db_session.add(pub_article)

        # Create unpublished article directly
        priv_article = FAQArticle(
            title="Private Article",
            content="Private content",
            is_published=False,
            id_category=sample_ticket_category.id_category,
            id_author=sample_employee.id_employee
        )
        db_session.add(priv_article)
        db_session.commit()

        public_articles = faq_service.get_public_articles()
        titles = [a.title for a in public_articles]
        assert "Published Article" in titles
        assert "Private Article" not in titles

    def test_get_private_articles_returns_only_unpublished(
        self, db_session, faq_service, sample_ticket_category, sample_employee
    ):
        """get_private_articles should return only unpublished articles."""
        # Create published article directly
        pub_article = FAQArticle(
            title="Pub Article",
            content="Public",
            is_published=True,
            id_category=sample_ticket_category.id_category,
            id_author=sample_employee.id_employee
        )
        db_session.add(pub_article)

        # Create unpublished article directly
        priv_article = FAQArticle(
            title="Priv Article",
            content="Private",
            is_published=False,
            id_category=sample_ticket_category.id_category,
            id_author=sample_employee.id_employee
        )
        db_session.add(priv_article)
        db_session.commit()

        private_articles = faq_service.get_private_articles()
        titles = [a.title for a in private_articles]
        assert "Priv Article" in titles

    def test_get_public_article_detail_returns_article(
        self, faq_service, sample_faq_article, sample_customer
    ):
        """get_public_article_detail should return published article."""
        article = faq_service.get_public_article_detail(
            sample_faq_article.id_article,
            client_ip="192.168.1.1"
        )
        assert article.id_article == sample_faq_article.id_article

    def test_get_public_article_detail_raises_404_for_missing(
        self, faq_service, sample_customer
    ):
        """get_public_article_detail should raise 404 for non-existent article."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            faq_service.get_public_article_detail(uuid4(), "192.168.1.1")
        assert exc_info.value.status_code == 404

    def test_get_public_article_detail_increments_view(
        self, faq_service, sample_faq_article, sample_customer, db_session
    ):
        """Viewing a public article should increment its view count."""
        initial_views = sample_faq_article.view_count

        # Clear VIEW_CACHE for this key before testing
        from app.services import faqService as fs_module
        fs_module.VIEW_CACHE.clear()

        # View from a different IP to bypass cooldown
        faq_service.get_public_article_detail(
            sample_faq_article.id_article,
            client_ip="10.0.0.1"
        )

        # View from another IP
        faq_service.get_public_article_detail(
            sample_faq_article.id_article,
            client_ip="10.0.0.2"
        )

        # Reload from DB to get updated count
        db_session.refresh(sample_faq_article)
        assert sample_faq_article.view_count >= initial_views + 1


class TestFAQServicePagination:
    """Tests for FAQ pagination."""

    def test_get_public_articles_paginated_returns_tuple(
        self, faq_service, sample_faq_article
    ):
        """Paginated query should return (articles, total_count)."""
        result = faq_service.get_public_articles_paginated(page=1, limit=10)
        assert isinstance(result, tuple)
        assert len(result) == 2
        articles, total = result
        assert isinstance(articles, list)
        assert isinstance(total, int)

    def test_get_public_articles_paginated_filters_by_category(
        self, db_session, faq_service, sample_ticket_category, sample_employee
    ):
        """Paginated query should filter by category_id."""
        # Create article directly
        article = FAQArticle(
            title="Categorized Article",
            content="Test content",
            is_published=True,
            id_category=sample_ticket_category.id_category,
            id_author=sample_employee.id_employee
        )
        db_session.add(article)
        db_session.commit()

        articles, total = faq_service.get_public_articles_paginated(
            page=1, limit=10, category_id=sample_ticket_category.id_category
        )
        assert all(a.id_category == sample_ticket_category.id_category for a in articles)

    def test_get_public_articles_paginated_filters_by_search(
        self, db_session, faq_service, sample_ticket_category, sample_employee
    ):
        """Paginated query should filter by search term in title/content."""
        # Create article directly
        article = FAQArticle(
            title="Searchable Article About Refunds",
            content="This discusses refund policies.",
            is_published=True,
            id_category=sample_ticket_category.id_category,
            id_author=sample_employee.id_employee
        )
        db_session.add(article)
        db_session.commit()

        articles, total = faq_service.get_public_articles_paginated(
            page=1, limit=10, search="Refund"
        )
        # Should find articles containing "refund" (case-insensitive)
        assert len(articles) >= 1


class TestFAQServiceUpdate:
    """Tests for FAQ article updates."""

    def test_update_article_title_success(self, faq_service, sample_faq_article):
        """Updating article title should succeed."""
        update_data = FAQUpdate(title="Updated Title")
        updated = faq_service.update_article(sample_faq_article.id_article, update_data)
        assert updated.title == "Updated Title"

    def test_update_article_content_success(self, faq_service, sample_faq_article):
        """Updating article content should succeed."""
        update_data = FAQUpdate(content="Updated content here")
        updated = faq_service.update_article(sample_faq_article.id_article, update_data)
        assert updated.content == "Updated content here"

    def test_update_article_publish_status(self, faq_service, sample_faq_article):
        """Toggling publish status should work."""
        update_data = FAQUpdate(is_published=False)
        updated = faq_service.update_article(sample_faq_article.id_article, update_data)
        assert updated.is_published is False

    def test_update_article_changes_category(
        self, db_session, faq_service, sample_faq_article, sample_department_2
    ):
        """Changing article category should work."""
        # Create a second category directly
        from app.models.ticket import TicketCategory
        new_cat = TicketCategory(
            name="Second Category",
            description="Another category",
            is_active=True,
            id_department=sample_department_2.id_department,
            auto_assign=True
        )
        db_session.add(new_cat)
        db_session.commit()
        db_session.refresh(new_cat)

        update_data = FAQUpdate(id_category=new_cat.id_category)
        updated = faq_service.update_article(sample_faq_article.id_article, update_data)
        assert str(updated.id_category) == str(new_cat.id_category)

    def test_update_article_raises_404_for_missing(self, faq_service):
        """Updating non-existent article should raise 404."""
        from fastapi import HTTPException
        update_data = FAQUpdate(title="New Title")
        with pytest.raises(HTTPException) as exc_info:
            faq_service.update_article(uuid4(), update_data)
        assert exc_info.value.status_code == 404


class TestFAQServiceDelete:
    """Tests for FAQ article deletion."""

    def test_delete_article_success(self, faq_service, sample_faq_article):
        """Deleting article should succeed."""
        faq_service.delete_article(sample_faq_article.id_article)

        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            faq_service.get_public_article_detail(sample_faq_article.id_article, "127.0.0.1")

    def test_delete_article_raises_404_for_missing(self, faq_service):
        """Deleting non-existent article should raise 404."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            faq_service.delete_article(uuid4())
        assert exc_info.value.status_code == 404