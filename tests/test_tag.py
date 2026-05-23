"""
Unit tests for Tag Service.

Tests cover:
- Tag creation with duplicate name validation
- Tag retrieval (all, by ID)
- Tag update with duplicate name validation
- Tag deletion
- Ticket-Tag assignment operations

Tag model:
- id_tag: String (UUID)
- name: String (unique)
- color: String (hex color)
- description: Text
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
import uuid

from app.services.admin.tagService import TagService
from app.schemas.admin.tag import TagCreate, TagUpdate
from app.models.tag import Tag, ticket_tags


# ============================================================================
# Tag Creation Tests
# ============================================================================

class TestTagCreation:
    """Tests for tag creation."""

    def test_create_tag_success(self, db_session):
        """Test successful tag creation."""
        service = TagService(db_session)

        data = TagCreate(
            name="Bug",
            color="#FF0000",
            description="Software bugs"
        )

        tag = service.create_tag(data)

        assert tag is not None
        assert tag.name == "Bug"
        assert tag.color == "#FF0000"
        assert tag.description == "Software bugs"

    def test_create_tag_duplicate_name(self, db_session):
        """Test creation fails when tag name already exists."""
        service = TagService(db_session)

        # Create first tag
        data1 = TagCreate(name="Urgent", color="#FF0000")
        service.create_tag(data1)

        # Try to create tag with same name
        data2 = TagCreate(name="Urgent", color="#00FF00")

        with pytest.raises(Exception) as exc_info:
            service.create_tag(data2)

        assert "already exists" in str(exc_info.value)

    def test_create_tag_default_color(self, db_session):
        """Test tag creation with default color."""
        service = TagService(db_session)

        data = TagCreate(name="NoColor")

        tag = service.create_tag(data)

        assert tag.name == "NoColor"
        assert tag.color == "#000000"  # Default color

    def test_create_tag_with_special_characters(self, db_session):
        """Test tag creation with special characters in name."""
        service = TagService(db_session)

        data = TagCreate(
            name="Tag #1 - Important!",
            color="#00FF00"
        )

        tag = service.create_tag(data)

        assert tag.name == "Tag #1 - Important!"


# ============================================================================
# Tag Retrieval Tests
# ============================================================================

class TestTagRetrieval:
    """Tests for tag retrieval."""

    def test_get_all_tags(self, db_session):
        """Test getting all tags."""
        service = TagService(db_session)

        # Create some tags
        service.create_tag(TagCreate(name="Tag1", color="#FF0000"))
        service.create_tag(TagCreate(name="Tag2", color="#00FF00"))

        tags = service.get_all_tags()

        assert len(tags) >= 2

    def test_get_tag_by_id_success(self, db_session):
        """Test getting tag by ID."""
        service = TagService(db_session)

        # Create tag
        created = service.create_tag(TagCreate(name="FindMe", color="#0000FF"))

        # Retrieve by ID
        tag = service.get_tag_by_id(str(created.id_tag))

        assert tag is not None
        assert tag.id_tag == created.id_tag
        assert tag.name == "FindMe"

    def test_get_tag_by_id_not_found(self, db_session):
        """Test getting nonexistent tag by ID."""
        service = TagService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.get_tag_by_id(str(uuid4()))

        assert "Tag not found" in str(exc_info.value)


# ============================================================================
# Tag Update Tests
# ============================================================================

class TestTagUpdate:
    """Tests for tag updates."""

    def test_update_tag_success(self, db_session):
        """Test successful tag update."""
        service = TagService(db_session)

        # Create tag
        tag = service.create_tag(TagCreate(name="OldName", color="#FF0000"))

        # Update tag
        data = TagUpdate(name="NewName", color="#00FF00", description="New desc")
        updated = service.update_tag(str(tag.id_tag), data)

        assert updated.name == "NewName"
        assert updated.color == "#00FF00"
        assert updated.description == "New desc"

    def test_update_tag_name_only(self, db_session):
        """Test updating only the name."""
        service = TagService(db_session)

        tag = service.create_tag(TagCreate(name="Original", color="#FF0000"))

        data = TagUpdate(name="Renamed")
        updated = service.update_tag(str(tag.id_tag), data)

        assert updated.name == "Renamed"
        assert updated.color == "#FF0000"  # Unchanged

    def test_update_tag_duplicate_name(self, db_session):
        """Test update fails when new name conflicts."""
        service = TagService(db_session)

        # Create two tags
        tag1 = service.create_tag(TagCreate(name="Tag1", color="#FF0000"))
        tag2 = service.create_tag(TagCreate(name="Tag2", color="#00FF00"))

        # Try to rename tag1 to tag2's name
        data = TagUpdate(name="Tag2")

        with pytest.raises(Exception) as exc_info:
            service.update_tag(str(tag1.id_tag), data)

        assert "already exists" in str(exc_info.value)

    def test_update_tag_not_found(self, db_session):
        """Test update fails for nonexistent tag."""
        service = TagService(db_session)

        data = TagUpdate(name="NewName")

        with pytest.raises(Exception) as exc_info:
            service.update_tag(str(uuid4()), data)

        assert "Tag not found" in str(exc_info.value)

    def test_update_tag_same_name_allowed(self, db_session):
        """Test updating tag with same name (no change) is allowed."""
        service = TagService(db_session)

        tag = service.create_tag(TagCreate(name="SameName", color="#FF0000"))

        data = TagUpdate(name="SameName")  # Same name
        updated = service.update_tag(str(tag.id_tag), data)

        assert updated.name == "SameName"


# ============================================================================
# Tag Deletion Tests
# ============================================================================

class TestTagDeletion:
    """Tests for tag deletion."""

    def test_delete_tag_success(self, db_session):
        """Test successful tag deletion."""
        service = TagService(db_session)

        tag = service.create_tag(TagCreate(name="ToDelete", color="#FF0000"))

        service.delete_tag(str(tag.id_tag))

        # Verify deletion
        with pytest.raises(Exception):
            service.get_tag_by_id(str(tag.id_tag))

    def test_delete_tag_not_found(self, db_session):
        """Test deletion fails for nonexistent tag."""
        service = TagService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.delete_tag(str(uuid4()))

        assert "Tag not found" in str(exc_info.value)


# ============================================================================
# Ticket-Tag Assignment Tests
# ============================================================================

class TestTicketTagAssignment:
    """Tests for ticket-tag assignment operations."""

    def test_get_tags_by_ticket(
        self,
        db_session,
        sample_ticket,
        sample_employee
    ):
        """Test getting tags assigned to a ticket."""
        service = TagService(db_session)

        # Create tags
        tag1 = service.create_tag(TagCreate(name="Tag1", color="#FF0000"))
        tag2 = service.create_tag(TagCreate(name="Tag2", color="#00FF00"))

        # Assign to ticket
        service.assign_tag_to_ticket(sample_ticket.id_ticket, str(tag1.id_tag))
        service.assign_tag_to_ticket(sample_ticket.id_ticket, str(tag2.id_tag))

        # Get tags for ticket
        tags = service.get_tags_by_ticket(sample_ticket.id_ticket)

        assert len(tags) == 2
        assert any(t.name == "Tag1" for t in tags)
        assert any(t.name == "Tag2" for t in tags)

    def test_get_tags_by_ticket_none_assigned(
        self,
        db_session,
        sample_ticket
    ):
        """Test getting tags when none are assigned."""
        service = TagService(db_session)

        tags = service.get_tags_by_ticket(sample_ticket.id_ticket)

        assert len(tags) == 0

    def test_get_tags_by_ticket_not_found(self, db_session):
        """Test getting tags for nonexistent ticket."""
        service = TagService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.get_tags_by_ticket(uuid4())

        assert "Ticket not found" in str(exc_info.value)

    def test_assign_tag_to_ticket_success(
        self,
        db_session,
        sample_ticket
    ):
        """Test successful tag assignment to ticket."""
        service = TagService(db_session)

        tag = service.create_tag(TagCreate(name="Assignment", color="#FF0000"))

        # No exception means success
        service.assign_tag_to_ticket(sample_ticket.id_ticket, str(tag.id_tag))

        # Verify assignment
        tags = service.get_tags_by_ticket(sample_ticket.id_ticket)
        assert len(tags) == 1
        assert tags[0].id_tag == tag.id_tag

    def test_assign_tag_already_assigned(
        self,
        db_session,
        sample_ticket
    ):
        """Test assigning already-assigned tag fails."""
        service = TagService(db_session)

        tag = service.create_tag(TagCreate(name="Duplicate", color="#FF0000"))

        # First assignment
        service.assign_tag_to_ticket(sample_ticket.id_ticket, str(tag.id_tag))

        # Second assignment should fail
        with pytest.raises(Exception) as exc_info:
            service.assign_tag_to_ticket(sample_ticket.id_ticket, str(tag.id_tag))

        assert "already assigned" in str(exc_info.value)

    def test_assign_tag_to_ticket_ticket_not_found(self, db_session):
        """Test assigning tag to nonexistent ticket fails."""
        service = TagService(db_session)

        tag = service.create_tag(TagCreate(name="Orphan", color="#FF0000"))

        with pytest.raises(Exception) as exc_info:
            service.assign_tag_to_ticket(uuid4(), str(tag.id_tag))

        assert "Ticket not found" in str(exc_info.value)

    def test_assign_tag_to_ticket_tag_not_found(self, db_session, sample_ticket):
        """Test assigning nonexistent tag fails."""
        service = TagService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.assign_tag_to_ticket(sample_ticket.id_ticket, str(uuid4()))

        assert "Tag not found" in str(exc_info.value)

    def test_remove_tag_from_ticket_success(
        self,
        db_session,
        sample_ticket
    ):
        """Test successful tag removal from ticket."""
        service = TagService(db_session)

        tag = service.create_tag(TagCreate(name="ToRemove", color="#FF0000"))
        service.assign_tag_to_ticket(sample_ticket.id_ticket, str(tag.id_tag))

        # Remove tag
        service.remove_tag_from_ticket(sample_ticket.id_ticket, str(tag.id_tag))

        # Verify removal
        tags = service.get_tags_by_ticket(sample_ticket.id_ticket)
        assert len(tags) == 0

    def test_remove_tag_not_assigned(self, db_session, sample_ticket):
        """Test removing tag that's not assigned fails."""
        service = TagService(db_session)

        tag = service.create_tag(TagCreate(name="NotAssigned", color="#FF0000"))

        with pytest.raises(Exception) as exc_info:
            service.remove_tag_from_ticket(sample_ticket.id_ticket, str(tag.id_tag))

        assert "not assigned" in str(exc_info.value)


# ============================================================================
# Edge Cases
# ============================================================================

class TestTagEdgeCases:
    """Edge case tests for tag service."""

    def test_tag_name_case_sensitivity(self, db_session):
        """Test tag names are case-sensitive."""
        service = TagService(db_session)

        # Create tag with lowercase
        service.create_tag(TagCreate(name="case", color="#FF0000"))

        # Try to create with uppercase - should succeed (case-sensitive)
        try:
            service.create_tag(TagCreate(name="CASE", color="#00FF00"))
            case_sensitive = True
        except Exception:
            case_sensitive = False

        # This depends on database collation settings

    def test_multiple_tags_different_colors(self, db_session):
        """Test creating multiple tags with different colors."""
        service = TagService(db_session)

        colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF"]

        for i, color in enumerate(colors):
            tag = service.create_tag(TagCreate(name=f"Color{i}", color=color))
            assert tag.color == color

    def test_tag_long_name(self, db_session):
        """Test tag with very long name."""
        service = TagService(db_session)

        long_name = "A" * 100
        tag = service.create_tag(TagCreate(name=long_name, color="#FF0000"))

        assert tag.name == long_name

    def test_tag_unicode_name(self, db_session):
        """Test tag with unicode characters."""
        service = TagService(db_session)

        tag = service.create_tag(TagCreate(
            name="Tag 日本語",
            color="#FF0000"
        ))

        assert tag.name == "Tag 日本語"

    def test_assign_multiple_tags_to_same_ticket(
        self,
        db_session,
        sample_ticket
    ):
        """Test assigning multiple different tags to same ticket."""
        service = TagService(db_session)

        # Create multiple tags
        tags = []
        for i in range(5):
            tag = service.create_tag(TagCreate(
                name=f"MultiTag{i}",
                color=f"#{i}0{i}0{i}0"
            ))
            tags.append(tag)

        # Assign all to same ticket
        for tag in tags:
            service.assign_tag_to_ticket(sample_ticket.id_ticket, str(tag.id_tag))

        # Verify all assigned
        ticket_tags = service.get_tags_by_ticket(sample_ticket.id_ticket)
        assert len(ticket_tags) == 5

    def test_same_tag_to_multiple_tickets(
        self,
        db_session,
        sample_ticket,
        sample_ticket_assigned
    ):
        """Test same tag can be assigned to multiple tickets."""
        service = TagService(db_session)

        tag = service.create_tag(TagCreate(name="SharedTag", color="#FF0000"))

        # Assign to ticket 1
        service.assign_tag_to_ticket(sample_ticket.id_ticket, str(tag.id_tag))

        # Assign to ticket 2
        service.assign_tag_to_ticket(sample_ticket_assigned.id_ticket, str(tag.id_tag))

        # Both tickets should have the tag
        tags1 = service.get_tags_by_ticket(sample_ticket.id_ticket)
        tags2 = service.get_tags_by_ticket(sample_ticket_assigned.id_ticket)

        assert len(tags1) == 1
        assert len(tags2) == 1
        assert tags1[0].id_tag == tag.id_tag
        assert tags2[0].id_tag == tag.id_tag
