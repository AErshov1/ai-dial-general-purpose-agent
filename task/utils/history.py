import copy
from typing import Any

from aidial_sdk.chat_completion import Message, Role

from task.utils.constants import TOOL_CALL_HISTORY_KEY, CUSTOM_CONTENT


def unpack_messages(messages: list[Message], state_history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Unpack and flatten a list of Message objects into a list of dictionaries suitable for API consumption.

    This function processes assistant and non-assistant messages differently:
    - For assistant messages: extracts and unpacks tool call history from the custom state,
      removes custom_content, and converts the message to a dictionary
    - For other messages: extracts message content and appends any attachment URLs from custom content
    - Appends any additional state history messages, excluding custom_content fields

    Args:
        messages: A list of Message objects to unpack
        state_history: A list of historical state dictionaries to append to the result

    Returns:
        A flattened list of dictionaries containing all messages and history, with keys like
        "role", "content", and "tool_call_id" (for tool messages)
    """
    result: list[dict[str, Any]] = []
    for message in messages:
        if message.role == Role.ASSISTANT:
            if custom_content := message.custom_content:
                # Unpack tool call history from Assistant message State
                state = custom_content.state
                if state and isinstance(state, dict):
                    tool_call_history = state.get(TOOL_CALL_HISTORY_KEY)
                    if tool_call_history and isinstance(tool_call_history, list):
                        for history_msg in tool_call_history:
                            if history_msg.get("role") == Role.TOOL.value:
                                result.append(
                                    {
                                        "role": Role.TOOL.value,
                                        "content": history_msg.get("content"),
                                        "tool_call_id": history_msg.get("tool_call_id"),
                                    }
                                )
                            else:
                                result.append(history_msg)

                    msg = copy.deepcopy(message)
                    msg.custom_content = None
                    result.append(msg.dict(exclude_none=True))
        else:
            attachments_urls_content = ''
            if message.custom_content and message.custom_content.attachments:
                attachments_urls_content = '\n\nAttached files URLs:\n'
                for attachment in message.custom_content.attachments:
                    if attachment.url:
                        attachments_urls_content += f"{attachment.url}\n"
                    elif attachment.reference_url:
                        attachments_urls_content += f"{
                            attachment.reference_url}\n"

            content = message.content or ''
            if attachments_urls_content:
                content += attachments_urls_content

            result.append(
                {
                    "role": message.role,
                    "content": content
                }
            )

    if state_history:
        for history_msg in state_history:
            if history_msg.get(CUSTOM_CONTENT):
                del history_msg[CUSTOM_CONTENT]
            result.append(history_msg)

    return result
