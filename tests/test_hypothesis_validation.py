from hypothesis import given, strategies as st
from lxmfy.validation import ConfigValidator, ValidationResult
import unittest.mock as mock

class ConfigObject:
    """A simple class to hold configuration attributes."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class TestValidationPropertyBased:
    """Property-based tests for bot configuration validation."""

    @st.composite
    def config_strategy(draw):
        """Strategy for generating bot configuration objects."""
        return ConfigObject(
            name=draw(st.text()),
            announce=draw(st.integers(min_value=-1000, max_value=10000)),
            rate_limit=draw(st.integers(min_value=-100, max_value=1000)),
            cooldown=draw(st.integers(min_value=-100, max_value=1000))
        )

    @given(config=config_strategy())
    def test_config_validation_robustness(self, config):
        """Test that validation never crashes and returns expected result types."""
        results = ConfigValidator.validate_config(config)
        assert isinstance(results, list)
        for res in results:
            assert isinstance(res, ValidationResult)
            assert isinstance(res.valid, bool)
            assert isinstance(res.messages, list)
            assert all(isinstance(m, str) for m in res.messages)

    @given(name=st.text(min_size=0, max_size=2))
    def test_short_name_invalid(self, name):
        """Test that names shorter than 3 characters always trigger an error."""
        config = ConfigObject(name=name, announce=300, rate_limit=5, cooldown=30)
        results = ConfigValidator.validate_config(config)
        
        errors = [r for r in results if not r.valid and r.severity == "error"]
        assert any("Bot name should be at least 3 characters long" in m for r in errors for m in r.messages)

    @given(announce=st.integers(min_value=1, max_value=299))
    def test_short_announce_warning(self, announce):
        """Test that announce intervals < 300 trigger a warning."""
        config = ConfigObject(name="ValidBotName", announce=announce, rate_limit=5, cooldown=30)
        results = ConfigValidator.validate_config(config)
        
        warnings = [r for r in results if not r.valid and r.severity == "warning"]
        assert any("Announce interval should be at least 300 seconds" in m for r in warnings for m in r.messages)
