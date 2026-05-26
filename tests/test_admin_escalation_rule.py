"""
Tests for admin escalation rule service.
"""

import pytest
from uuid import uuid4

from app.services.admin.escalationRuleService import EscalationRuleService
from app.schemas.admin.escalation import EscalationRuleCreate, EscalationRuleUpdate


class TestCreateRule:
    """Tests for create_rule method."""

    def test_create_rule_success(self, db_session):
        """Happy path: create a valid escalation rule."""
        data = EscalationRuleCreate(
            name="High severity overdue",
            priority="1",
            condition_type="priority",
            condition_value="high",
            action_type="notify",
            action_target="manager@example.com",
            is_active=True
        )

        rule = EscalationRuleService(db_session).create_rule(data)

        assert rule.name == "High severity overdue"
        assert rule.priority == "1"
        assert rule.condition_type == "priority"
        assert rule.condition_value == "high"
        assert rule.action_type == "notify"
        assert rule.action_target == "manager@example.com"
        assert rule.is_active is True

    def test_create_rule_with_minimal_fields(self, db_session):
        """Edge case: create rule with only required fields."""
        data = EscalationRuleCreate(
            name="Minimal Rule",
            condition_type="category",
            condition_value="billing",
            action_type="reassign",
            action_target=str(uuid4()),
            is_active=False
        )

        rule = EscalationRuleService(db_session).create_rule(data)

        assert rule.name == "Minimal Rule"
        assert rule.is_active is False

    def test_create_rule_generates_unique_id(self, db_session):
        """Business rule: new rule gets a UUID."""
        data = EscalationRuleCreate(
            name="Unique ID Rule",
            condition_type="time_elapsed",
            condition_value="4h",
            action_type="escalate",
            action_target="senior_team"
        )

        rule = EscalationRuleService(db_session).create_rule(data)

        assert rule.id is not None
        assert len(rule.id) == 36


class TestGetAllRules:
    """Tests for get_all_rules method."""

    def test_get_all_rules_returns_all_rules(self, db_session):
        """Happy path: get all rules including inactive."""
        service = EscalationRuleService(db_session)
        service.create_rule(EscalationRuleCreate(
            name="Rule One",
            condition_type="priority",
            condition_value="critical",
            action_type="notify",
            action_target="admin@example.com"
        ))
        service.create_rule(EscalationRuleCreate(
            name="Rule Two",
            condition_type="category",
            condition_value="tech",
            action_type="reassign",
            action_target=str(uuid4()),
            is_active=False
        ))

        rules = service.get_all_rules()

        assert len(rules) >= 2

    def test_get_all_rules_returns_empty_list_when_no_rules(self, db_session):
        """Edge case: no rules exist."""
        rules = EscalationRuleService(db_session).get_all_rules()

        assert rules == []


class TestGetRule:
    """Tests for get_rule method."""

    def test_get_rule_by_id_returns_rule(self, db_session):
        """Happy path: get existing rule by ID."""
        service = EscalationRuleService(db_session)
        created = service.create_rule(EscalationRuleCreate(
            name="Get By ID Rule",
            condition_type="priority",
            condition_value="low",
            action_type="notify",
            action_target="team@example.com"
        ))

        rule = service.get_rule(created.id)

        assert rule.id == created.id
        assert rule.name == "Get By ID Rule"

    def test_get_rule_by_id_rejects_missing_rule(self, db_session):
        """Validation: missing rule raises HTTPException 404."""
        with pytest.raises(Exception) as exc_info:
            EscalationRuleService(db_session).get_rule(str(uuid4()))

        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()


class TestGetActiveRules:
    """Tests for get_active_rules method."""

    def test_get_active_rules_returns_only_active_rules(self, db_session):
        """Business rule: only active rules returned."""
        service = EscalationRuleService(db_session)
        service.create_rule(EscalationRuleCreate(
            name="Active Rule",
            condition_type="priority",
            condition_value="high",
            action_type="notify",
            action_target="active@example.com",
            is_active=True
        ))
        service.create_rule(EscalationRuleCreate(
            name="Inactive Rule",
            condition_type="priority",
            condition_value="medium",
            action_type="notify",
            action_target="inactive@example.com",
            is_active=False
        ))

        active_rules = service.get_active_rules()

        assert all(rule.is_active is True for rule in active_rules)
        assert any(rule.name == "Active Rule" for rule in active_rules)
        assert not any(rule.name == "Inactive Rule" for rule in active_rules)


class TestUpdateRule:
    """Tests for update_rule method."""

    def test_update_rule_success(self, db_session):
        """Happy path: update name and priority of existing rule."""
        service = EscalationRuleService(db_session)
        rule = service.create_rule(EscalationRuleCreate(
            name="Original Name",
            priority="3",
            condition_type="priority",
            condition_value="medium",
            action_type="notify",
            action_target="old@example.com"
        ))

        updated = service.update_rule(
            rule.id,
            EscalationRuleUpdate(name="Updated Name", priority="1")
        )

        assert updated.name == "Updated Name"
        assert updated.priority == "1"
        assert updated.action_target == "old@example.com"

    def test_update_rule_overrides_is_active(self, db_session):
        """Business rule: update can deactivate a rule."""
        service = EscalationRuleService(db_session)
        rule = service.create_rule(EscalationRuleCreate(
            name="Toggle Rule",
            condition_type="category",
            condition_value="billing",
            action_type="reassign",
            action_target=str(uuid4()),
            is_active=True
        ))

        updated = service.update_rule(rule.id, EscalationRuleUpdate(is_active=False))

        assert updated.is_active is False

    def test_update_rule_rejects_missing_rule(self, db_session):
        """Validation: update non-existent rule raises 404."""
        with pytest.raises(Exception) as exc_info:
            EscalationRuleService(db_session).update_rule(
                str(uuid4()),
                EscalationRuleUpdate(name="Ghost Rule")
            )

        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()


class TestDeleteRule:
    """Tests for delete_rule method."""

    def test_delete_rule_removes_rule_from_db(self, db_session):
        """Happy path: delete removes rule."""
        service = EscalationRuleService(db_session)
        rule = service.create_rule(EscalationRuleCreate(
            name="To Be Deleted",
            condition_type="priority",
            condition_value="high",
            action_type="notify",
            action_target="delete@example.com"
        ))

        service.delete_rule(rule.id)

        # now get_rule should raise
        with pytest.raises(Exception):
            service.get_rule(rule.id)

    def test_delete_rule_rejects_missing_rule(self, db_session):
        """Validation: delete non-existent rule raises 404."""
        with pytest.raises(Exception) as exc_info:
            EscalationRuleService(db_session).delete_rule(str(uuid4()))

        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()


class TestToggleRule:
    """Tests for toggle_rule method."""

    def test_toggle_rule_activates_inactive_rule(self, db_session):
        """Business rule: toggle flips is_active from False to True."""
        service = EscalationRuleService(db_session)
        rule = service.create_rule(EscalationRuleCreate(
            name="Toggle Active",
            condition_type="priority",
            condition_value="low",
            action_type="notify",
            action_target="toggle@example.com",
            is_active=False
        ))

        toggled = service.toggle_rule(rule.id)

        assert toggled.is_active is True

    def test_toggle_rule_deactivates_active_rule(self, db_session):
        """Business rule: toggle flips is_active from True to False."""
        service = EscalationRuleService(db_session)
        rule = service.create_rule(EscalationRuleCreate(
            name="Toggle Inactive",
            condition_type="priority",
            condition_value="low",
            action_type="notify",
            action_target="toggle2@example.com",
            is_active=True
        ))

        toggled = service.toggle_rule(rule.id)

        assert toggled.is_active is False

    def test_toggle_rule_rejects_missing_rule(self, db_session):
        """Validation: toggle non-existent rule raises 404."""
        with pytest.raises(Exception) as exc_info:
            EscalationRuleService(db_session).toggle_rule(str(uuid4()))

        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()
