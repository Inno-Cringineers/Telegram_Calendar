"""Basic hello world test to verify CI/CD pipeline."""

from bot.keyboards.inline import get_main_menu_inline


def test_hello_world():
    """Simple hello world test to verify pytest works."""
    assert True, "Hello World test passed!"


def test_main_menu_keyboard():
    """Test that main menu keyboard is created correctly."""
    keyboard = get_main_menu_inline()

    # Check that keyboard is created
    assert keyboard is not None

    # Check that keyboard has inline_keyboard attribute
    assert hasattr(keyboard, "inline_keyboard")

    # Check that keyboard has 4 buttons (rows)
    assert len(keyboard.inline_keyboard) == 4

    # Check specific buttons and their callback_data
    expected_buttons = [
        ("⚙️ Settings", "menu_settings"),
        ("📅 Events", "menu_events"),
        ("📋 Get Daily Plan", "menu_daily_plan"),
        ("🔗 External calendars", "menu_link_calendar"),
    ]

    for i, (expected_text, expected_callback) in enumerate(expected_buttons):
        button = keyboard.inline_keyboard[i][0]
        assert button.text == expected_text, f"Button {i} text mismatch"
        assert (
            button.callback_data == expected_callback
        ), f"Button {i} callback_data mismatch"
