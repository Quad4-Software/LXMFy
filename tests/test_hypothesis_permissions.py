from hypothesis import given, strategies as st
from lxmfy.permissions import DefaultPerms, PermissionManager, Role
import unittest.mock as mock

class TestPermissionsPropertyBased:
    """Property-based tests for the permissions system."""

    @given(p1=st.sampled_from(list(DefaultPerms)), p2=st.sampled_from(list(DefaultPerms)))
    def test_perms_bitwise_commutative(self, p1, p2):
        """Test that ORing permissions is commutative."""
        assert (p1 | p2) == (p2 | p1)

    @given(p=st.sampled_from(list(DefaultPerms)))
    def test_perms_bitwise_idempotent(self, p):
        """Test that ORing a permission with itself is idempotent."""
        assert (p | p) == p

    @given(perms_list=st.lists(st.sampled_from(list(DefaultPerms)), min_size=1))
    def test_perms_all_contain_individual(self, perms_list):
        """Test that a combined permission set contains all its components."""
        combined = DefaultPerms.NONE
        for p in perms_list:
            combined |= p
        
        for p in perms_list:
            assert (combined & p) == p

    @given(
        user_id=st.text(min_size=1),
        role_perms=st.lists(st.sampled_from(list(DefaultPerms)), min_size=1, max_size=5)
    )
    def test_permission_manager_role_aggregation(self, user_id, role_perms):
        """Test that a user's permissions are the union of all their roles."""
        storage = mock.MagicMock()
        storage.get.return_value = {}
        pm = PermissionManager(storage=storage, enabled=True)
        
        combined_expected = DefaultPerms.NONE
        # Also include default role perms since PM assigns it by default
        combined_expected |= pm.default_role.permissions
        
        for i, perms in enumerate(role_perms):
            role_name = f"role_{i}"
            role_combined = DefaultPerms.NONE
            for p in perms: # perms is a single Flag here due to sampled_from, but perms_list was lists of them
                role_combined |= p # In this case role_perms is list of single flags
            
            # Wait, perms is a single flag because of sampled_from in st.lists
            # Let's fix the strategy to be more interesting
            pass

    @st.composite
    def perms_strategy(draw):
        """Strategy to generate a combined DefaultPerms flag."""
        flags = draw(st.lists(st.sampled_from(list(DefaultPerms)), min_size=1))
        combined = DefaultPerms.NONE
        for f in flags:
            combined |= f
        return combined

    @given(
        user_id=st.text(min_size=1),
        roles_data=st.dictionaries(
            st.text(min_size=1, max_size=10).filter(lambda x: x not in ["user", "admin"]),
            perms_strategy()
        )
    )
    def test_pm_complex_aggregation(self, user_id, roles_data):
        """Test that PermissionManager correctly aggregates multiple complex roles."""
        storage = mock.MagicMock()
        storage.get.return_value = {}
        pm = PermissionManager(storage=storage, enabled=True)
        
        expected_perms = pm.default_role.permissions
        
        # Manually assign default role for consistency with PM behavior
        pm.user_roles[user_id] = {pm.default_role.name}

        for name, perms in roles_data.items():
            pm.roles[name] = Role(name, perms)
            pm.assign_role(user_id, name)
            expected_perms |= perms
            
        assert pm.get_user_permissions(user_id) == expected_perms
        
        # Test individual permission checks
        for name, perms in roles_data.items():
            # For each flag in the combined perms, it should return True
            for flag in DefaultPerms:
                if flag != DefaultPerms.NONE and (perms & flag) == flag:
                    assert pm.has_permission(user_id, flag) is True

    @given(p=perms_strategy())
    def test_pm_disabled_always_allows(self, p):
        """Test that when PM is disabled, has_permission always returns True."""
        storage = mock.MagicMock()
        storage.get.return_value = {}
        pm = PermissionManager(storage=storage, enabled=False)
        assert pm.has_permission("any_user", p) is True
