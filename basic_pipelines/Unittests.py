import pytest
from unittest.mock import MagicMock, patch
from keye_detection import user_app_callback_class, app_callback

@pytest.fixture
def user_data():
    return user_app_callback_class()

def test_initialization(user_data):
    assert user_data.target_object == "person"
    assert not user_data.is_it_active
    assert user_data.in_zone_frames == 0
    assert user_data.out_zone_frames == 0

def test_zone_definitions(user_data):
    assert 0 <= user_data.zone1_x_min < user_data.zone1_x_max <= 1
    assert 0 <= user_data.zone2_x_min < user_data.zone2_x_max <= 1


def test_app_callback_no_detection(mock_get_roi, mock_get_caps, mock_get_numpy, user_data):
    pad = MagicMock()
    info = MagicMock()
    roi_mock = MagicMock()
    roi_mock.get_objects_typed.return_value = []  # Keine erkannten Objekte
    mock_get_roi.return_value = roi_mock
    
    result = app_callback(pad, info, user_data)
    assert result == MagicMock()
    assert user_data.in_zone_frames == 0
    assert user_data.out_zone_frames == 1

@patch("keye_detection.hailo.get_roi_from_buffer")
def test_object_detected_in_zone(mock_get_roi, user_data):
    pad = MagicMock()
    info = MagicMock()
    roi_mock = MagicMock()
    detection_mock = MagicMock()
    detection_mock.get_label.return_value = "person"
    detection_mock.get_confidence.return_value = 0.5
    detection_mock.get_bbox.return_value.xmin.return_value = 0.65  # Innerhalb von Zone 1
    detection_mock.get_bbox.return_value.width.return_value = 0.1
    detection_mock.get_bbox.return_value.height.return_value = 0.1
    roi_mock.get_objects_typed.return_value = [detection_mock]
    mock_get_roi.return_value = roi_mock
    
    app_callback(pad, info, user_data)
    assert user_data.in_zone_frames == 1
    assert user_data.out_zone_frames == 0

@patch("keye_detection.hailo.get_roi_from_buffer")
def test_object_in_zone_long_enough(mock_get_roi, user_data):
    user_data.in_zone_frames = 3  # Fast erreicht
    pad = MagicMock()
    info = MagicMock()
    roi_mock = MagicMock()
    detection_mock = MagicMock()
    detection_mock.get_label.return_value = "person"
    detection_mock.get_confidence.return_value = 0.5
    detection_mock.get_bbox.return_value.xmin.return_value = 0.65
    detection_mock.get_bbox.return_value.width.return_value = 0.1
    detection_mock.get_bbox.return_value.height.return_value = 0.1
    roi_mock.get_objects_typed.return_value = [detection_mock]
    mock_get_roi.return_value = roi_mock
    
    with patch("keye_detection.print") as mock_print:
        app_callback(pad, info, user_data)
        mock_print.assert_any_call("Person in Gefahrenzone, Sicherheitskreis wird abgeschaltet!")
    assert user_data.is_it_active
