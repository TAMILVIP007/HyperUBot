# Copyright 2020-2021 nunopenim @github
# Copyright 2020-2021 prototype74 @github
#
# Licensed under the PEL (Penim Enterprises License), v1.0
#
# You may not use this file or any of the content within it, unless in
# compliance with the PE License

from userbot import MODULE_DESC, MODULE_DICT, MODULE_INFO, OS, SAFEMODE
from userbot.include.aux_funcs import sizeStrMaker
from userbot.include.language_processor import ModulesUtilsText as msgRep, ModuleUsages as usageRep
from userbot.sysutils.configuration import getConfig
from userbot.sysutils.event_handler import EventHandler
from userbot.sysutils.registration import (getAllModules, getLoadModules, getUserModules,
                                           getModuleDesc, getModuleInfo, getRegisteredCMDs,
                                           register_cmd_usage)
from logging import getLogger
from os.path import basename, exists, getctime, getsize, join
from os import stat
from time import ctime

log = getLogger(__name__)
ehandler = EventHandler(log)
MODULES_LISTED = {}

@ehandler.on(command="listcmds", alt="help", hasArgs=True, outgoing=True)
async def list_commands(event):
    arg_from_event = event.pattern_match.group(1)
    cmd_not_found = False
    command = None
    cmds_dict = getRegisteredCMDs()
    if arg_from_event:
        command, command_value = (None,)*2
        for key, value in cmds_dict.items():
            alt_cmd = value.get("alt_cmd")
            if (
                key == arg_from_event.lower()
                or key != arg_from_event.lower()
                and alt_cmd
                and alt_cmd == arg_from_event.lower()
            ):
                command, command_value = key, value
                break
        if command_value:
            if not command_value.get("success"):
                name_of_module = command_value.get("module_name")
                if name_of_module in MODULE_DICT.keys():
                    log.info(f"MODULE_DICT is obsolete, please use register_cmd_usage() instead (in module '{name_of_module}')")
                    cmd_info = MODULE_DICT.get(name_of_module)
                    await event.edit(cmd_info)
                    return
            cmd_alt = command_value.get("alt_cmd")
            cmd_hasArgs = command_value.get("hasArgs")
            cmd_args = command_value.get("args")
            cmd_usage = command_value.get("usage")
            if not cmd_hasArgs:
                cmd_args = f"__{msgRep.ARGS_NOT_REQ}__"
            elif not cmd_args:
                cmd_args = f"__{msgRep.ARGS_NOT_AVAILABLE}__"
            if not cmd_usage:
                cmd_usage = f"__{msgRep.MODULE_NO_USAGE.lower()}__"
            if cmd_alt:
                cmd_info = f"`.{command}`/`.{cmd_alt}` {cmd_args}\n{msgRep.USAGE}: {cmd_usage}\n\n"
            else:
                cmd_info = f"`.{command}` {cmd_args}\n{msgRep.USAGE}: {cmd_usage}\n\n"
            await event.edit(cmd_info)
            return
        else:
            cmd_not_found = True

    cmds_amount = len(cmds_dict)
    all_cmds = f"**{msgRep.LISTCMDS_TITLE} ({cmds_amount})**\n\n"
    if cmd_not_found:
        all_cmds += msgRep.CMD_NOT_FOUND.format(arg_from_event) + "\n"
    all_cmds += msgRep.LISTCMDS_USAGE.format("`.listcmds`/`.help`") + "\n\n"
    for cmd, value in cmds_dict.items():
        if alt_cmd := value.get("alt_cmd"):
            all_cmds += f"`{cmd}` (`{alt_cmd}`)\t\t\t\t"
        else:
            all_cmds += f"`{cmd}`\t\t\t\t"
    await event.edit(all_cmds)

def update_list() -> list:
    modules_list = []
    for module, isRunning in getLoadModules().items():
        if module != basename(__file__)[:-3]:  # exclude this module
            if module in getModuleInfo().keys():
                # Append [Name of module, filename of module, running] -> []
                modules_list.append([getModuleInfo().get(module, {}).get("name", msgRep.UNKNOWN), module, isRunning])
            elif module in MODULE_INFO.keys():
                modules_list.append([MODULE_INFO.get(module, {}).get("name", msgRep.UNKNOWN), module, isRunning])
            else:
                modules_list.append([module, module, isRunning])

    global MODULES_LISTED

    if MODULES_LISTED:
        MODULES_LISTED = {}  # reset dict

    for num, module in enumerate((modules[1] for modules in sorted(modules_list)), start=1):
        MODULES_LISTED[str(num)] = module
    return sorted(modules_list)

def installed_modules() -> tuple:
    syspath = join(".", "userbot", "modules")
    userpath = join(".", "userbot", "modules_user")

    sys_count, user_count = (0,)*2

    for module in getAllModules():
        if exists(join(syspath, (module + ".py"))):
            sys_count += 1
        elif exists(join(userpath, (module + ".py"))):
            user_count += 1
    return (sys_count, user_count)

def modules_listing(error_text: str = None) -> str:
    modules_listed = '**Modules**\n\n'

    if error_text:
        modules_listed += f"{error_text}\n\n"

    modules_listed += f"{msgRep.USAGE}:\n`.modules -d, --desc [{msgRep.NUMBER_OF_MODULE}]`\n"\
                                       f"`.modules -i, --info [{msgRep.NUMBER_OF_MODULE}]`\n"\
                                       f"`.modules -u, --usage [{msgRep.NUMBER_OF_MODULE}]`\n\n"

    sys_count, user_count = installed_modules()

    modules_listed += f"`{msgRep.SYSTEM_MODULES}: {sys_count}`\n"
    modules_listed += f"`{msgRep.USER_MODULES}: {user_count}`\n\n" if not SAFEMODE else "\n"

    modules_listed += f"{msgRep.AVAILABLE_MODULES}:\n"

    modules_list = update_list()
    all_running = all(ir == True for ir in [modules[-1] for modules in modules_list])
    num = 0
    warning = u"\u26A0"  # warn emoji
    user_modules = getUserModules()

    for module_name, module, isRunning in modules_list:
        num += 1
        if module in user_modules:
            if isRunning:
                modules_listed += f'`({num}) {module_name}* ({module})`\n'
            else:
                modules_listed += f'`({num}) {module_name}* ({module}) {warning}`\n'
        elif isRunning:
            modules_listed += f'`({num}) {module_name} ({module})`\n'
        else:
            modules_listed += f'`({num}) {module_name} ({module}) {warning}`\n'

    if not_load_modules := getConfig("NOT_LOAD_MODULES"):
        all_modules = getAllModules()
        for module in not_load_modules:
            if module in module:
                modules_listed += "\n"
                modules_listed += f"{msgRep.DISABLED_MODULES}:\n"
                break
        for module in sorted(not_load_modules):
            if module in module:
                if module in user_modules:
                    modules_listed += f"`- {module}*`\n"
                else:
                    modules_listed += f"`- {module}`\n"
                num += 1

    if (user_modules and not SAFEMODE) or not all_running:
        modules_listed += "--------------------------------\n"
    if user_modules and not SAFEMODE:
        modules_listed += f"__* = {msgRep.ASTERISK}__\n"
    if not all_running:
        modules_listed += f"__{warning} = {msgRep.NOT_RUNNING_INFO}__\n"
    return modules_listed

def module_desc(name_of_module: str, module: str) -> str:
    if module not in getLoadModules().keys():
        raise IndexError
    if module in getModuleDesc().keys():
        return msgRep.NAME_MODULE.format(name_of_module) + "\n\n" + getModuleDesc().get(module)
    elif module in MODULE_DESC.keys():
        log.info(f"MODULE_DESC is obsolete, please use register_module_desc() instead (in module '{module}')")
        return msgRep.NAME_MODULE.format(name_of_module) + "\n\n" + MODULE_DESC.get(module)
    else:
        return msgRep.NAME_MODULE.format(name_of_module) + "\n\n" + msgRep.MODULE_NO_DESC

def module_info(name_of_module: str, module: str) -> str:
    if module not in getLoadModules().keys():
        raise IndexError
    package_name, moduletype, installation_date = (msgRep.UNKNOWN,)*3
    size = 0
    if module in getModuleInfo().keys():
        authors = getModuleInfo().get(module, {}).get("authors", msgRep.UNKNOWN)
        version = getModuleInfo().get(module, {}).get("version", 0)
    elif module in MODULE_INFO.keys():
        log.info(f"MODULE_INFO is obsolete, please use register_module_info() instead (in module '{module}')")
        authors = MODULE_INFO.get(module, {}).get("authors", msgRep.UNKNOWN)
        version = MODULE_INFO.get(module, {}).get("version", 0)
    if not authors:
        authors = msgRep.UNKNOWN
    if not version:
        version = 0
    package_name = module
    module += ".py"
    syspath = join(".", "userbot", "modules")
    userpath = join(".", "userbot", "modules_user")
    if exists(join(syspath, module)):
        moduletype = msgRep.SYSTEM
        size = sizeStrMaker(getsize(join(syspath, module)))
        if OS and OS.lower().startswith("win"):
            installation_date = getctime(join(syspath, module))
        elif OS and OS.lower().startswith("darwin"):
            installation_date = stat(join(syspath, module)).st_birthtime
        else:
            installation_date = stat(join(syspath, module)).st_ctime
    elif exists(join(userpath, module)):
        moduletype = msgRep.USER
        size = sizeStrMaker(getsize(join(userpath, module)))
        if OS and OS.lower().startswith("win"):
            installation_date = getctime(join(userpath, module))
        elif OS and OS.lower().startswith("darwin"):
            installation_date = stat(join(userpath, module)).st_birthtime
        else:
            installation_date = stat(join(userpath, module)).st_ctime
    result = f"{msgRep.PKG_NAME}: {package_name}\n"
    result += f"{msgRep.MODULE_TYPE}: {moduletype}\n"
    result += f"{msgRep.AUTHORS}: {authors}\n"
    result += f"{msgRep.VERSION}: {version}\n"
    result += f"{msgRep.SIZE}: {size}\n"
    result += f"{msgRep.INSTALL_DATE}: {ctime(installation_date)}"
    return msgRep.NAME_MODULE.format(name_of_module) + "\n\n" + result

def module_usage(name_of_module: str, module: str) -> str:
    if module not in getLoadModules().keys():
        raise IndexError
    usage = msgRep.NAME_MODULE.format(name_of_module) + "\n\n"
    cmds_usage_registered = False
    for cmd, value in getRegisteredCMDs().items():
        if value.get("module_name") == module and value.get("success", False):
            if not cmds_usage_registered:
                cmds_usage_registered = True
            cmd_alt = value.get("alt_cmd")
            cmd_hasArgs = value.get("hasArgs")
            cmd_args = value.get("args")
            cmd_usage = value.get("usage")
            if not cmd_hasArgs:
                cmd_args = f"__{msgRep.ARGS_NOT_REQ}__"
            elif not cmd_args:
                cmd_args = f"__{msgRep.ARGS_NOT_AVAILABLE}__"
            if not cmd_usage:
                cmd_usage = f"__{msgRep.MODULE_NO_USAGE.lower()}__"
            if cmd_alt:
                usage += f"`.{cmd}`/`.{cmd_alt}` {cmd_args}\n{msgRep.USAGE}: {cmd_usage}\n\n"
            else:
                usage += f"`.{cmd}` {cmd_args}\n{msgRep.USAGE}: {cmd_usage}\n\n"
    if not cmds_usage_registered:
        if module in MODULE_DICT.keys():
            log.info(f"MODULE_DICT is obsolete, please use register_cmd_usage() instead (in module '{module}')")
            usage += MODULE_DICT.get(module)
        else:
            usage += msgRep.MODULE_NO_USAGE
    return usage

@ehandler.on(command="modules", alt="module", hasArgs=True, outgoing=True)
async def modules(event):
    args_from_event = event.pattern_match.group(1).split(" ", 1)
    if len(args_from_event) == 2:
        first_arg, sec_arg = args_from_event
    else:
        first_arg, sec_arg = args_from_event[0], None

    desc, info, usage = (False,)*3

    if not first_arg:
        await event.edit(modules_listing())
        return

    if first_arg.lower() in ("-d", "--desc"):
        desc = True
    elif first_arg.lower() in ("-i", "--info"):
        info = True
    elif first_arg.lower() in ("-u", "--usage"):
        usage = True
    else:
        await event.edit(modules_listing(msgRep.INVALID_ARG.format(first_arg)))
        return

    if not sec_arg:
        await event.edit(modules_listing(msgRep.MISSING_NUMBER_MODULE))
        return

    modules_list = update_list()
    global MODULES_LISTED
    name_of_module = None
    module_to_load = MODULES_LISTED.get(sec_arg)
    for module_name, module in [modules[:-1] for modules in modules_list]:
        if module_to_load is module:
            name_of_module = module_name
            break
    try:
        if desc:
            await event.edit(module_desc(name_of_module, module_to_load))
        elif info:
            await event.edit(module_info(name_of_module, module_to_load))
        elif usage:
            await event.edit(module_usage(name_of_module, module_to_load))
    except IndexError:
        await event.edit(modules_listing(msgRep.MODULE_NOT_AVAILABLE.format(sec_arg)))
    return

register_cmd_usage("listcmds", usageRep.MODULES_UTILS_USAGE.get("listcmds", {}).get("args"), usageRep.MODULES_UTILS_USAGE.get("listcmds", {}).get("usage"))
register_cmd_usage("modules", usageRep.MODULES_UTILS_USAGE.get("modules", {}).get("args"), usageRep.MODULES_UTILS_USAGE.get("modules", {}).get("usage"))
