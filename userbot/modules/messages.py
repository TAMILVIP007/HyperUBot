# Copyright 2020-2021 nunopenim @github
# Copyright 2020-2021 prototype74 @github
#
# Licensed under the PEL (Penim Enterprises License), v1.0
#
# You may not use this file or any of the content within it, unless in
# compliance with the PE License

from userbot.include.aux_funcs import event_log, fetch_user, isRemoteCMD
from userbot.include.language_processor import MessagesText as msgRep, ModuleDescriptions as descRep, ModuleUsages as usageRep
from userbot.sysutils.configuration import getConfig
from userbot.sysutils.event_handler import EventHandler
from userbot.sysutils.registration import register_cmd_usage, register_module_desc, register_module_info
from userbot.version import VERSION
from telethon.errors import ChatAdminRequiredError, InputUserDeactivatedError, SearchQueryEmptyError
from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import InputMessagesFilterEmpty, ChannelParticipantsAdmins
from logging import getLogger
from os.path import basename

log = getLogger(__name__)
ehandler = EventHandler(log)
LOGGING = getConfig("LOGGING")

@ehandler.on(command="msgs", hasArgs=True, outgoing=True)
async def countmessages(event):
    user, chat = await fetch_user(event, get_chat=True)

    if not user:
        return

    if not chat:
        await event.edit(msgRep.FAIL_CHAT)
        return

    remote = isRemoteCMD(event, chat.id)

    try:
        msg_info = await event.client(SearchRequest(peer=chat.id, q="",  # search for any message
                                                    filter=InputMessagesFilterEmpty(),
                                                    min_date=None, max_date=None,
                                                    add_offset=0, offset_id=0,
                                                    limit=0, max_id=0, min_id=0,
                                                    hash=0, from_id=user.id))
    except ChatAdminRequiredError:
        await event.edit(msgRep.NO_ADMIN)
        return
    except InputUserDeactivatedError:
        await event.edit(msgRep.CANNOT_COUNT_DEL)
        return
    except SearchQueryEmptyError as sqee:
        log.warning(sqee)
        await event.edit(msgRep.CANNOT_COUNT_FWD)
        return
    except Exception as e:
        log.warning(e)
        await event.edit(msgRep.FAIL_COUNT_MSG)
        return

    user_link = "@" + user.username if user.username else f"[{user.first_name}](tg://user?id={user.id})"

    if hasattr(msg_info, "count"):
        if remote:
            await event.edit(msgRep.USER_HAS_SENT_REMOTE.format(user_link, msg_info.count, chat.title))
        else:
            await event.edit(msgRep.USER_HAS_SENT.format(user_link, msg_info.count))
    elif remote:
        await event.edit(msgRep.CANNOT_COUNT_MSG_REMOTE.format(chat.title))
    else:
        await event.edit(msgRep.CANNOT_COUNT_MSG)
    return

@ehandler.on(command="pin", hasArgs=True, outgoing=True)
async def pin(event):
    if event.reply_to_msg_id:
        msg_id = event.reply_to_msg_id
    else:
        await event.edit(msgRep.PIN_REPLY_TO_MSG)
        return

    chat = await event.get_chat()
    if not chat:
        await event.edit(msgRep.FAIL_CHAT)
        return

    arg_from_event = event.pattern_match.group(1)
    notify = arg_from_event.lower() == "loud"
    try:
        await event.client.pin_message(chat.id, msg_id, notify=notify)
        await event.edit(msgRep.PIN_SUCCESS)
        if LOGGING:
            await event_log(event, "PINNED MESSAGE", chat_title=chat.title if hasattr(chat, "title") else None,
                            chat_link=chat.username if hasattr(chat, "username") else None,
                            chat_id=chat.id, custom_text=f"{msgRep.LOG_PIN_MSG_ID}: {event.reply_to_msg_id}")
    except ChatAdminRequiredError:
        await event.edit(msgRep.NO_ADMIN)
    except Exception as e:
        log.warning(e)
        await event.edit(msgRep.PIN_FAILED)

    return

@ehandler.on(command="unpin", hasArgs=True, outgoing=True)
async def pin(event):
    arg_from_event = event.pattern_match.group(1)
    all_msgs = arg_from_event.lower() == "all"

    if not all_msgs:
        if event.reply_to_msg_id:
            msg_id = event.reply_to_msg_id
        else:
            await event.edit(msgRep.UNPIN_REPLY_TO_MSG)
            return

    chat = await event.get_chat()
    if not chat:
        await event.edit(msgRep.FAIL_CHAT)
        return

    try:
        if all_msgs:
            await event.client.unpin_message(chat.id)
            await event.edit(msgRep.UNPIN_ALL_SUCCESS)
            log_text = f"**{msgRep.LOG_UNPIN_ALL_TEXT}**"
        else:
            await event.client.unpin_message(chat.id, msg_id)
            await event.edit(msgRep.UNPIN_SUCCESS)
            log_text = f"{msgRep.LOG_PIN_MSG_ID}: {event.reply_to_msg_id}"
        if LOGGING:
            await event_log(event, "UNPINNED MESSAGES" if all_msgs else "UNPINNED MESSAGE",
                            chat_title=chat.title if hasattr(chat, "title") else None,
                            chat_link=chat.username if hasattr(chat, "username") else None,
                            chat_id=chat.id, custom_text=log_text)
    except ChatAdminRequiredError:
        await event.edit(msgRep.NO_ADMIN)
    except Exception as e:
        log.warning(e)
        await event.edit(msgRep.UNPIN_FAILED)

    return

for cmd in ("msgs", "pin", "unpin"):
    register_cmd_usage(cmd, usageRep.MESSAGES_USAGE.get(cmd, {}).get("args"), usageRep.MESSAGES_USAGE.get(cmd, {}).get("usage"))

register_module_desc(descRep.MESSAGES_DESC)
register_module_info(
    name="Messages",
    authors="nunopenim, prototype74",
    version=VERSION
)
