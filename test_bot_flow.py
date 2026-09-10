import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace

module_path = Path(__file__).with_name("thon.py")
spec = importlib.util.spec_from_file_location("thon", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert hasattr(module, "build_role_keyboard")
assert hasattr(module, "handle_name")
assert hasattr(module, "handle_role_selection")
assert hasattr(module, "handle_teacher_password")
assert hasattr(module, "check_answers")
assert hasattr(module, "list_user_ids")
assert module.ANSWER_VIEWER_NAMES == {"muy lyly", "heng"}


class FakeBot:
	def __init__(self):
		self.sent_messages = []

	async def send_message(self, **kwargs):
		self.sent_messages.append(kwargs)


async def test_developer_can_send_to_current_group():
	developer_id = 987654321
	group_id = -1001234567890
	module.users[developer_id] = {"role": "dev"}
	bot = FakeBot()
	replies = []

	async def reply_text(text):
		replies.append(text)

	update = SimpleNamespace(
		effective_user=SimpleNamespace(id=developer_id),
		effective_chat=SimpleNamespace(id=group_id, type="group"),
		message=SimpleNamespace(
			reply_to_message=None,
			reply_text=reply_text,
		),
	)
	context = SimpleNamespace(
		args=["The", "server", "is", "ready"],
		bot=bot,
	)

	await module.send_user_message(update, context)

	assert bot.sent_messages == [{
		"chat_id": group_id,
		"text": "The server is ready",
	}]
	assert replies == ["✅ Message sent to this group."]


async def test_teacher_can_send_message():
	teacher_id = 555111222
	student_id = 222333444
	module.users[teacher_id] = {"role": "teacher"}
	bot = FakeBot()
	replies = []

	async def reply_text(text):
		replies.append(text)

	update = SimpleNamespace(
		effective_user=SimpleNamespace(id=teacher_id),
		effective_chat=SimpleNamespace(id=-100987654321, type="private"),
		message=SimpleNamespace(
			reply_to_message=None,
			reply_text=reply_text,
		),
	)
	context = SimpleNamespace(
		args=[str(student_id), "Hello", "students"],
		bot=bot,
	)

	await module.send_user_message(update, context)

	assert bot.sent_messages == [{
		"chat_id": student_id,
		"text": "Hello students",
	}]
	assert replies == [f"✅ Message sent to user {student_id}."]


asyncio.run(test_developer_can_send_to_current_group())
asyncio.run(test_teacher_can_send_message())
