from src.pages.mobile import base_content_block
from src.pages.mobile.base_content_block import MobileInteractionMixin


def test_swipe_by_w3c_actions_uses_touch_action_chain(monkeypatch):
    action_events = []
    performed = []
    pointer_inputs = []

    class FakePointerAction:
        def move_to_location(self, x, y):
            action_events.append(("move", x, y))

        def pointer_down(self):
            action_events.append(("down",))

        def release(self):
            action_events.append(("release",))

    class FakeActionBuilder:
        def __init__(self, driver, mouse):
            action_events.append(("builder", driver, mouse))
            self.pointer_action = FakePointerAction()

    class FakePointerInput:
        def __init__(self, pointer_type, name):
            self.pointer_type = pointer_type
            self.name = name
            pointer_inputs.append(self)

    class FakeActionChains:
        def __init__(self, driver):
            self.driver = driver
            self.w3c_actions = None

        def perform(self):
            performed.append((self.driver, self.w3c_actions))

    class FakePage(MobileInteractionMixin):
        def __init__(self):
            self.driver = object()

        def _log_ui(self, _message):
            return None

    monkeypatch.setattr(base_content_block, "ActionChains", FakeActionChains)
    monkeypatch.setattr(base_content_block, "ActionBuilder", FakeActionBuilder)
    monkeypatch.setattr(base_content_block, "PointerInput", FakePointerInput)

    page = FakePage()

    page.swipe_by_w3c_actions(10, 20, 30, 40)

    assert pointer_inputs[0].pointer_type == base_content_block.interaction.POINTER_TOUCH
    assert pointer_inputs[0].name == "touch"
    assert action_events == [
        ("builder", page.driver, pointer_inputs[0]),
        ("move", 10, 20),
        ("down",),
        ("move", 30, 40),
        ("release",),
    ]
    assert performed == [(page.driver, performed[0][1])]
