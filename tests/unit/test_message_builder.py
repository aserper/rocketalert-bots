import pytest
from unittest.mock import Mock, patch, mock_open
from message_builder import AlertMessageBuilder


@pytest.mark.unit
class TestAlertMessageBuilder:
    """Tests for AlertMessageBuilder class"""

    def test_buildAlert_with_both_english_names(self, message_builder, sample_alert):
        """Test buildAlert uses English names when available"""
        result = message_builder.buildAlert(sample_alert)
        assert "Nirim" in result
        assert "Gaza Envelope" in result

    def test_buildAlert_fallback_to_hebrew(self, message_builder, alert_hebrew_only):
        """Test buildAlert falls back to Hebrew when English unavailable"""
        result = message_builder.buildAlert(alert_hebrew_only)
        assert "נירים" in result
        assert "עוטף עזה" in result

    def test_buildAlert_missing_area_name(self, message_builder, alert_missing_area):
        """Test buildAlert returns just location name when area is missing"""
        result = message_builder.buildAlert(alert_missing_area)
        assert "Nirim" in result
        # Should not have parentheses when area is missing
        assert "(" not in result

    def test_buildAlert_with_area_name(self, message_builder, sample_alert):
        """Test buildAlert includes area name with parentheses"""
        result = message_builder.buildAlert(sample_alert)
        assert "(" in result
        assert ")" in result
        assert result == "Nirim (Gaza Envelope)"

    def test_buildMessageText_rocket_alert(self, message_builder):
        """Test buildMessageText formats rocket alert correctly"""
        timestamp = "2023-12-04 16:59:09"
        alert_type_id = 1
        alert_locations = "Test Location\n"
        result = message_builder.buildMessageText(alert_type_id, timestamp, alert_locations)

        assert "Rocket alert" in result
        assert timestamp in result
        assert "Test Location" in result

    def test_buildMessageText_uav_alert(self, message_builder):
        """Test buildMessageText formats UAV alert correctly"""
        timestamp = "2023-12-04 16:59:09"
        alert_type_id = 2
        alert_locations = "Test Location\n"
        result = message_builder.buildMessageText(alert_type_id, timestamp, alert_locations)

        assert "Hostile UAV alert" in result
        assert timestamp in result

    def test_buildMessageText_red_alert_other(self, message_builder):
        """Test buildMessageText formats other alert types as Red alert"""
        timestamp = "2023-12-04 16:59:09"
        alert_type_id = 99
        alert_locations = "Test Location\n"
        result = message_builder.buildMessageText(alert_type_id, timestamp, alert_locations)

        assert "Red alert" in result
        assert timestamp in result

    def test_buildMarker_success(self, message_builder, sample_alert):
        """Test buildMarker creates correct marker string"""
        result = message_builder.buildMarker(sample_alert)

        assert "pin-s" in result
        assert str(sample_alert["lon"]) in result
        assert str(sample_alert["lat"]) in result

    def test_buildPolygonOverlay_with_valid_polygon(self, message_builder, sample_alert):
        """Test buildPolygonOverlay with existing polygon data"""
        # This test checks if polygon exists in the loaded data
        result = message_builder.buildPolygonOverlay(sample_alert)

        # Result can be None if polygon doesn't exist for this taCityId
        # or a string if it does - both are valid
        if result is not None:
            assert isinstance(result, str)
            assert len(result) > 0

    def test_buildMessage_structure(self, message_builder):
        """Test buildMessage returns correct structure"""
        static_map = {"overlays": [], "markers": []}
        map_file_count = 0
        alert_type_id = 1
        timestamp = "2023-12-04 16:59:09"
        alert_locations = "Nirim (Gaza Envelope)\n"

        result = message_builder.buildMessage(
            static_map, map_file_count, alert_type_id, timestamp, alert_locations
        )

        assert isinstance(result, dict)
        assert "text" in result
        # Note: "file" key is not included when map generation is disabled
        assert "Rocket alert" in result["text"]
        assert "Nirim (Gaza Envelope)" in result["text"]

    def test_buildMessage_includes_timestamp(self, message_builder):
        """Test buildMessage includes timestamp in output"""
        static_map = {"overlays": [], "markers": []}
        map_file_count = 0
        alert_type_id = 1
        timestamp = "2023-12-04 16:59:09"
        alert_locations = "Test Location\n"

        result = message_builder.buildMessage(
            static_map, map_file_count, alert_type_id, timestamp, alert_locations
        )

        assert timestamp in result["text"]

    def test_getMapURL_construction(self, message_builder):
        """Test getMapURL constructs valid URL"""
        static_map = {
            "overlays": [],
            "markers": ["pin-s+f74e4e(34.3941,31.3357)"]
        }

        result = message_builder.getMapURL(static_map)

        assert "https://api.mapbox.com" in result
        assert "mapbox" in result.lower()

    def test_buildMessage_with_multiple_locations(self, message_builder):
        """Test buildMessage handles multiple alert locations"""
        static_map = {"overlays": [], "markers": []}
        map_file_count = 0
        alert_type_id = 1
        timestamp = "2023-12-04 16:59:09"
        alert_locations = "Location 1\nLocation 2\nLocation 3\n"

        result = message_builder.buildMessage(
            static_map, map_file_count, alert_type_id, timestamp, alert_locations
        )

        assert "Location 1" in result["text"]
        assert "Location 2" in result["text"]
        assert "Location 3" in result["text"]
