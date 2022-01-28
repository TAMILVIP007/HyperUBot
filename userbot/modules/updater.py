# Copyright 2020-2021 nunopenim @github
# Copyright 2020-2021 prototype74 @github
#
# Licensed under the PEL (Penim Enterprises License), v1.0
#
# You may not use this file or any of the content within it, unless in
# compliance with the PE License

from userbot import PROJECT
from userbot.include.git_api import getLatestData
from userbot.include.language_processor import UpdaterText as msgRep, ModuleDescriptions as descRep, ModuleUsages as usageRep
from userbot.sysutils.configuration import getConfig, setConfig
from userbot.sysutils.event_handler import EventHandler
from userbot.sysutils.registration import register_cmd_usage, register_module_desc, register_module_info
from userbot.version import VERSION
from logging import getLogger
from urllib.request import urlretrieve
from zipfile import BadZipFile, LargeZipFile, ZipFile
import os

log = getLogger(__name__)
ehandler = EventHandler(log)

RELEASE_DIR = os.path.join(".", "releases")
UPDATE_PACKAGE = os.path.join(RELEASE_DIR, "update.zip")
_LATEST_VER = {}

def _get_latest_release(updater_rules: str, release: str) -> bool:
    if not os.path.exists(RELEASE_DIR):
        try:
            os.mkdir(RELEASE_DIR)
        except Exception as e:
            log.error(f"Failed to create release directory: {e}")
            return False

    try:
        try:
            log.info("Downloading updater rules...")
            urlretrieve(updater_rules, os.path.join(RELEASE_DIR, "rules.py"))
        except Exception as e:
            log.error("Unable to download updater rules")
            raise Exception(e)
        log.info("Downloading update package...")
        urlretrieve(release, UPDATE_PACKAGE)
        log.info("Download successful")
        return True
    except Exception as e:
        log.error(f"Unable to download latest release: {e}")
    return False

def _get_commit_id():
    commit_id = None
    if not os.path.exists(UPDATE_PACKAGE):
        log.warning("Update package not found")
        return commit_id

    try:
        contents = None
        with ZipFile(UPDATE_PACKAGE, "r") as updateZIP:
            contents = updateZIP.namelist()
        updateZIP.close()
        if contents and len(contents) >= 1:
            commit_id = contents[0][:-1].split("-")[-1]
    except BadZipFile as bze:
        log.error(f"Bad zip archive: {bze}", exc_info=True)
    except LargeZipFile as lze:
        log.error(f"Zip archive too large (>64): {lze}", exc_info=True)
    except Exception as e:
        log.error(f"Failed to get commit id from update package: {e}", exc_info=True)
    return commit_id

def _set_autoupdate(commit_id: str) -> bool:
    try:
        setConfig("UPDATE_COMMIT_ID", commit_id)
        setConfig("START_RECOVERY", True)
        return True
    except Exception as e:
        log.error(f"Unable to set reboot reason: {e}")
    return False

@ehandler.on(command="update", hasArgs=True, outgoing=True)
async def updater(event):
    arg = event.pattern_match.group(1)
    update_now = arg.lower() == "upgrade"
    global _LATEST_VER

    if not update_now or not _LATEST_VER:
        await event.edit(msgRep.CHECKING_UPDATES)

    if update_now and _LATEST_VER:
        await event.edit(msgRep.DOWNLOADING_RELEASE)
        if not _get_latest_release(_LATEST_VER.get("rules"), _LATEST_VER.get("zip")):
            await event.edit("Update failed")
            log.error("Failed to download latest release. Aborting process", exc_info=True)
            _LATEST_VER = {}
            return
        _LATEST_VER = {}
        commit_id = _get_commit_id()
        if not commit_id:
            await event.edit(msgRep.UPDATE_FAILED)
            return
        await event.edit(msgRep.DOWNLOAD_SUCCESS)
        if _set_autoupdate(commit_id):
            await event.client.disconnect()
        else:
            await event.edit(msgRep.START_RECOVERY_FAILED)
        return

    try:
        current_version = tuple(map(int, VERSION.split(".")))
    except Exception:
        await event.edit(msgRep.UPDATE_FAILED)
        log.error("Failed to parse bot version", exc_info=True)
        return

    try:
        release_data = getLatestData("nunopenim/HyperUBot")
        if not release_data:
            raise Exception
    except Exception:
        await event.edit(msgRep.UPDATE_FAILED)
        log.error("Failed to get latest release")
        return

    try:
        tag_version = release_data["tag_name"][1:]
        release_version = tuple(map(int, tag_version.split(".")))
    except ValueError:
        await event.edit(msgRep.UPDATE_FAILED)
        log.error("Invalid tag version from release", exc_info=True)
        return
    except Exception:
        await event.edit(msgRep.UPDATE_FAILED)
        log.error("Failed to parse tag version from release", exc_info=True)
        return

    if current_version > release_version:
        log.warning(f"Current version newer than on release server ({VERSION} > {tag_version})")
        await event.edit(f"{msgRep.UPDATE_FAILED}: {msgRep.UPDATE_INTERNAL_FAILED}")
        if _LATEST_VER:
            _LATEST_VER = {}
        return

    if current_version == release_version:
        log.info(f"Already up-to-date ({VERSION} == {tag_version})")
        reply = f"**{msgRep.ALREADY_UP_TO_DATE}**\n\n"
        reply += f"{msgRep.LATEST}: {tag_version}\n"
        reply += f"{msgRep.CURRENT}: {VERSION}\n"
        if _LATEST_VER:
            _LATEST_VER = {}
        await event.edit(reply)
        return

    if current_version < release_version:
        try:
            if assets := release_data.get("assets", []):
                for asset in assets:
                    if asset.get("name", "") == "rules.py":
                        _LATEST_VER["rules"] = asset.get("browser_download_url")
                        break
        except Exception:
            await event.edit(msgRep.UPDATE_FAILED)
            log.error("Failed to get assets from release", exc_info=True)
            return
        _LATEST_VER["zip"] = release_data.get("zipball_url")
        release_url = release_data.get("html_url")
        log.info(f"Update available ({VERSION} < {tag_version})")
        reply = f"**{msgRep.UPDATE_AVAILABLE}**\n\n"
        reply += f"**{msgRep.LATEST}: {tag_version}**\n"
        reply += f"{msgRep.CURRENT}: {VERSION}\n\n"
        reply += msgRep.CHANGELOG_AT.format(f"[GitHub]({release_url})\n\n")
        if update_now:
            reply += msgRep.DOWNLOADING_RELEASE
            await event.edit(reply)
            if not _get_latest_release(_LATEST_VER.get("rules"), _LATEST_VER.get("zip")):
                await event.edit(reply.replace(msgRep.DOWNLOADING_RELEASE, msgRep.UPDATE_FAILED))
                log.error("Failed to download latest release. Aborting process", exc_info=True)
                _LATEST_VER = {}
                return
            _LATEST_VER = {}
            commit_id = _get_commit_id()
            if not commit_id:
                 await event.edit(reply.replace(msgRep.DOWNLOADING_RELEASE, msgRep.UPDATE_FAILED))
                 return
            await event.edit(reply.replace(msgRep.DOWNLOADING_RELEASE, msgRep.DOWNLOAD_SUCCESS))
            if _set_autoupdate(commit_id):
                await event.client.disconnect()
            else:
                await event.edit(reply.replace(msgRep.DOWNLOAD_SUCCESS,
                                               msgRep.START_RECOVERY_FAILED))  
        else:
            reply += msgRep.UPDATE_QUEUED
            await event.edit(reply)
    return

register_cmd_usage("update", usageRep.UPDATER_USAGE.get("update", {}).get("args"), usageRep.UPDATER_USAGE.get("update", {}).get("usage"))
register_module_desc(descRep.UPDATER_DESC)
register_module_info(
    name="Updater",
    authors="nunopenim, prototype74",
    version=VERSION
)
