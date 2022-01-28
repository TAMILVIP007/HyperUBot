# Copyright 2021 nunopenim @github
# Copyright 2021 prototype74 @github
#
# Licensed under the PEL (Penim Enterprises License), v1.0
#
# You may not use this file or any of the content within it, unless in
# compliance with the PE License

from sys import version_info

if (version_info.major, version_info.minor) < (3, 8):
    print("Python v3.8+ is required! Please update "\
          "Python to v3.8 or newer "\
          "(current version: {}.{}.{}).".format(
              version_info.major, version_info.minor, version_info.micro))
    quit(1)

from glob import glob
from json import loads
from platform import system
from shutil import copytree, rmtree
from subprocess import check_call
from sys import argv, executable
from urllib.request import urlopen, urlretrieve
from zipfile import BadZipFile, LargeZipFile, ZipFile, ZIP_DEFLATED
import os

PLATFORM = system().lower()
VERSION = "1.0.0"
BACKUP_DIR = os.path.join(".", "backup")
GITIGNORE = os.path.join(".", ".gitignore")
RELEASE_DIR = os.path.join(".", "releases")
UPDATE_PACKAGE = os.path.join(RELEASE_DIR, "update.zip")
PY_EXEC = executable if " " not in executable else '"' + executable + '"'
WIN_COLOR_ENABLED = False

try:
    if PLATFORM.startswith("win"):
        import colorama
        colorama.init()
        WIN_COLOR_ENABLED = True
except:
    pass

class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN_BG = "\033[46m"
    GREEN_BG = "\033[102m"
    RED_BG = "\033[101m"
    YELLOW_BG = "\033[103m"
    END = "\033[0m"

def setColorText(text: str, color: Colors) -> str:
    if PLATFORM.startswith("win") and not WIN_COLOR_ENABLED:
        return text  # don't use ANSI codes
    return color + text + Colors.END

class _Recovery:
    def __init__(self):
        self.__recovery_mode = "NORMAL"

    def run_userbot(self, safemode: bool = False):
        try:
            if safemode:
                tcmd = [PY_EXEC, "-m", "userbot", "-safemode"]
            else:
                tcmd = [PY_EXEC, "-m", "userbot"]
            os.execle(PY_EXEC, *tcmd, os.environ)
        except Exception as e:
            print(setColorText(
                f"Failed to run HyperUBot: {e}", Colors.RED))
        return

    def _list_dirs(self, source: str, ignore: list = []) -> list:
        do_not_list = [BACKUP_DIR, RELEASE_DIR]
        listed_dirs = []
        if ignore:
            for element in ignore:
                if isinstance(element, str):
                    do_not_list.append(element)
        for name in os.listdir(source):
            srcname = os.path.join(source, name)
            if srcname not in do_not_list:
                listed_dirs.append(srcname)
                if os.path.isdir(srcname):
                    for elem in self._list_dirs(srcname, ignore):
                        listed_dirs.append(elem)
        return listed_dirs

    def _fix_paths(self, rules_paths: list) -> list:
        paths = []
        try:
            for path in rules_paths:
                if PLATFORM.startswith("win"):
                    path = path.replace("/", "\\")
                else:
                    path = path.replace("\\", "/")
                if "*" in path:
                    for name in glob(path):
                        dir_name = os.path.dirname(name)
                        dir_name = os.path.join(".", dir_name)
                        if dir_name not in paths:
                            paths.append(dir_name)
                        paths.append(os.path.join(".", name))
                        if os.path.isdir(name):
                            for elem in self._list_dirs(name):
                                paths.append(os.path.join(".", elem))
                elif os.path.isdir(path):
                    paths.append(os.path.join(".", path))
                    for elem in self._list_dirs(path):
                       paths.append(os.path.join(".", elem))
                else:
                    paths.append(os.path.join(".", path))
        except Exception as e:
            print(setColorText(e, Colors.RED))
        return paths

    def _install_requirements(self):
        try:
            check_call(
               [PY_EXEC, "-m", "pip", "install", "-r", "requirements.txt"])
        except Exception as e:
            print(setColorText(
                f"Failed to install pip requirements: {e}", Colors.RED))
        return

    @property
    def recovery_mode(self) -> str:
        return self.__recovery_mode

    @recovery_mode.setter
    def recovery_mode(self, new_mode: str):
        self.__recovery_mode = new_mode

    def _remove(self, dirs: list = [], ignore: list = []):
        def name_in_list(name_to_check, list_to_check) -> bool:
            return any(name == name_to_check for name in list_to_check)
        for name in reversed(dirs):
            if not name_in_list(name, ignore):
                if os.path.isfile(name):
                    os.remove(name)
                elif os.path.isdir(name):
                    os.rmdir(name)
        return

    def _remove_extracted_update_package(self, package_path: str):
        try:
            rmtree(package_path)
        except Exception as e:
            print(
                setColorText("Failed to remove extracted update package",
                             Color.RED))
        return

    def userbot_version(self) -> str:
        ver_py = os.path.join(".", "userbot", "version.py")
        version = "Unknown"
        try:
            with open(ver_py, "r") as script:
                for line in script.readlines():
                    if (
                        not line.startswith("#")
                        and line != "\n"
                        and line.startswith("VERSION=")
                    ):
                        if line.split("=")[1]:
                            version = line.split("=")[1]
                            version = version.replace("\n", "")
                        break
            if '"' in version:
                version = version.replace('"', "")
            script.close()
        except:
            pass
        return version

class _Backup(_Recovery):
    def __init__(self):
        super().__init__()

    def backup_exists(self, name: str) -> bool:
        bkName = os.path.join(BACKUP_DIR, name + ".hbotbk")
        if os.path.exists(bkName):
            return True
        return False

    def generate_backup(self, bk_name: str):
        if not os.path.exists(BACKUP_DIR):
            try:
                os.mkdir(BACKUP_DIR)
            except Exception as e:
                print(setColorText(
                    f"Failed to create backup directory: {e}", Colors.RED))
                return
        try:
            bkName = os.path.join(BACKUP_DIR, bk_name + ".hbotbk")
            print("Generating backup...")
            with ZipFile(bkName, "w", ZIP_DEFLATED) as bkZIP:
                for name in self._list_dirs("."):
                    bkZIP.write(name)
            bkZIP.close()
            print(setColorText("Backup generated successfully.", Colors.GREEN))
        except BadZipFile as bze:
            print(setColorText(
                f"Bad zip archive: {bze}", Colors.RED))
        except LargeZipFile as lze:
            print(setColorText(
                f"Zip archive too large (>64): {lze}", Colors.RED))
        except Exception as e:
            print(setColorText(
                f"Failed to generate backup archive: {e}", Colors.RED))
        return

class _Installer(_Recovery):
    def __init__(self):
        self.__download_successful = False
        self.__installation_successful = False
        self.__package_path = None
        super().__init__()

    def __extract_update_package(self):
        try:
            contents = None
            with ZipFile(UPDATE_PACKAGE, "r") as zipObject:
                contents = zipObject.namelist()
                zipObject.extractall(RELEASE_DIR)
            zipObject.close()
            if contents and len(contents) > 0:
                root_dir = contents[0][:-1]
                self.__package_path = os.path.join(RELEASE_DIR, root_dir)
        except BadZipFile as bze:
            print(setColorText(
                f"Bad zip archive: {bze}", Colors.RED))
        except LargeZipFile as lze:
            print(setColorText(
                f"Zip archive too large (>64): {lze}", Colors.RED))
        except Exception as e:
            print(setColorText(
                f"Failed to extract update package: {e}", Colors.RED))
        return

    def __get_latest_release(self):
        if not os.path.exists(RELEASE_DIR):
            try:
                os.mkdir(RELEASE_DIR)
            except Exception as e:
                print(f"Failed to create release directory: {e}")
                return

        try:
            print("Parsing latest release data...")
            repo_url = urlopen("https://api.github.com/repos/nunopenim/"\
                               "HyperUBot/releases/latest")
            repo_data = loads(repo_url.read().decode())
            dw_url = repo_data.get("zipball_url")
            if not dw_url:
                print(setColorText("Failed to parse download URL", Colors.RED))
                return
        except Exception as e:
            print(
                setColorText(f"Failed to parse latest release: {e}",
                             Colors.RED))
            return

        try:
            print("Downloading latest release...")
            urlretrieve(dw_url, UPDATE_PACKAGE)
        except Exception as e:
            print(
                setColorText(f"Unable to download latest release: {e}",
                             Colors.RED))
            return

        if os.path.exists(UPDATE_PACKAGE):
            self.__download_successful = True
            print("Download completed.")
        else:
            print(
                setColorText(f"Unable to find update package: {e}",
                             Colors.RED))
        return

    def install_update_package(self):
        self.__get_latest_release()

        if not self.__download_successful:
           print(setColorText("Installation aborted.", Colors.YELLOW))
           return

        print("Extracting update package...")
        self.__extract_update_package()

        if not self.__package_path:
            print(
                setColorText("Extracted update package not found",
                             Colors.YELLOW))
            return

        try:
            print("Removing current environment...")
            self._remove(self._list_dirs("."))
        except Exception as e:
            print(
                setColorText(f"Failed to remove old environment: {e}",
                             Colors.RED))
            self._remove_extracted_update_package(self.__package_path)
            return

        try:
            print("Installing update package...")
            copytree(self.__package_path, ".", dirs_exist_ok=True)
        except Exception as e:
            print(
                setColorText(f"Failed to install update package: {e}",
                             Colors.RED))
            self._remove_extracted_update_package(self.__package_path)
            return

        print("Installing pip requirements...")
        self._install_requirements()

        try:
            print("Cleaning up...")
            self._remove_extracted_update_package(self.__package_path)
            self._remove(self._fix_paths(["releases"]))
        except Exception as e:
            print(
                setColorText(f"Failed to clean updater environment: {e}",
                             Colors.YELLOW))

        self.__installation_successful = True
        print(setColorText("Installation completed.", Colors.GREEN))
        return

    def getInstallationSuccessful(self):
        return self.__installation_successful

class _Restore(_Recovery):
    def __init__(self):
        super().__init__()

    def list_backups(self) -> dict:
        bk_dict = {}
        if not os.path.exists(BACKUP_DIR):
            return bk_dict
        try:
            num = 1
            for name in os.listdir(BACKUP_DIR):
                if os.path.isfile(os.path.join(BACKUP_DIR, name)) and \
                   name.endswith(".hbotbk"):
                    srcname = os.path.join(BACKUP_DIR, name)
                    bk_dict[str(num)] = {"bkname": name.split(".hbotbk")[0],
                                         "source": srcname}
                    num +=1
        except Exception as e:
            print(setColorText(
                f"Failed to list backup directory: {e}", Colors.RED))
        return bk_dict

    def restore(self, name: dict):
        if not name:
            print(setColorText("Name empty!", Colors.YELLOW))
            return

        bkName = name.get("bkname", "HyperUBot")
        bkSource = name.get("source")
        bkName += ".hbotbk"

        if not os.path.exists(bkSource):
            print(
                setColorText(f"{bkSource}: No such file or directory",
                             Colors.YELLOW))
            return

        try:
            contents = None
            userbot = ["userbot/", "userbot/__init__.py",
                       "userbot/__main__.py"]
            bkZIP = ZipFile(bkSource, "r")
            contents = bkZIP.namelist()
            result = 0
            for name in contents:
                for uname in userbot:
                    if uname == name:
                        result +=1
            if result != len(userbot):
                print(setColorText(f"{bkSource}: Invalid archive format!",
                                   Colors.RED))
                return

            try:
                print("Removing current environment...")
                self._remove(self._list_dirs("."))
            except Exception as e:
                print(
                    setColorText(f"Failed to remove current environment: {e}",
                                 Colors.RED))
                return

            print("Restoring backup archive...")
            bkZIP.extractall(".")
            bkZIP.close()
            print(setColorText("Restore completed.", Colors.GREEN))
        except BadZipFile as bze:
            print(setColorText(
                f"Bad zip archive: {bze}", Colors.RED))
        except LargeZipFile as lze:
            print(setColorText(
                f"Zip archive too large (>64): {lze}", Colors.RED))
        except Exception as e:
            print(setColorText(
                f"Failed to restore backup archive: {e}", Colors.RED))
        return

class _Updater(_Recovery):
    def __init__(self, commit_id: str):
        self.__commit_id = commit_id
        self.__package_path = None
        self.__commit_id_package = None
        self.__successful = False
        super().__init__()

    def __extract_update_package(self):
        try:
            contents = None
            with ZipFile(UPDATE_PACKAGE, "r") as zipObject:
                print("Update package found")
                contents = zipObject.namelist()
                print("Extracting update package...")
                zipObject.extractall(RELEASE_DIR)
            zipObject.close()
            if contents and len(contents) > 0:
                root_dir = contents[0][:-1]
                self.__commit_id_package = root_dir.split("-")[-1]
                self.__package_path = os.path.join(RELEASE_DIR, root_dir)
        except BadZipFile as bze:
            print(setColorText(
                f"Bad zip archive: {bze}", Colors.RED))
        except LargeZipFile as lze:
            print(setColorText(
                f"Zip archive too large (>64): {lze}", Colors.RED))
        except Exception as e:
            print(setColorText(
                f"Failed to extract update package: {e}", Colors.RED))
        return

    def __parse_gitignore(self) -> list:
        ignore_paths = []
        try:
            with open(GITIGNORE, "r") as git:
                for line in git.readlines():
                    if (
                        not line.startswith("#")
                        and line != "\n"
                        and "__pycache__" not in line
                    ):
                        line = line.split("#")[0].rstrip()
                        if PLATFORM.startswith("win"):
                            line = line.replace("/", "\\")
                        if "*" in line:
                            for name in glob(line):
                                dir_name = os.path.dirname(name)
                                dir_name = os.path.join(".", dir_name)
                                if dir_name not in ignore_paths:
                                    ignore_paths.append(dir_name)
                                ignore_paths.append(os.path.join(".", name))
                                if os.path.isdir(name):
                                    for elem in self._list_dirs(name):
                                        ignore_paths.append(
                                            os.path.join(".", elem))
                        elif os.path.isdir(line):
                            ignore_paths.append(os.path.join(".", line))
                            for elem in self._list_dirs(line):
                                ignore_paths.append(os.path.join(".", elem))
                        else:
                            ignore_paths.append(
                                os.path.join(".", line.replace("\n", "")))
            git.close()
        except Exception as e:
            print(setColorText(e, Colors.RED))
        return ignore_paths

    def install_update_package(self):
        self.__extract_update_package()

        if not self.__package_path:
            print(
                setColorText("Extracted update package not found",
                             Colors.YELLOW))
            return

        if self.__commit_id != self.__commit_id_package:
            print(setColorText("Commit ID mismatch!", Colors.YELLOW))
            self._remove_extracted_update_package(self.__package_path)
            return

        try:
            import releases.rules as rules
        except ImportError:
            print(setColorText("Unable to find updater rules!", Colors.YELLOW))
            self._remove_extracted_update_package(self.__package_path)
            return
        except Exception as e:
            print(setColorText(f"Invalid format for updater rules: {e}",
                               Colors.RED))
            self._remove_extracted_update_package(self.__package_path)
            print(setColorText("Update cancelled", Colors.YELLOW))
            return

        always_ignore = [os.path.join(".", "userbot"),
                         os.path.join(".", "userbot", "modules_user"),
                         os.path.join(".", "userbot", "config.env"),
                         os.path.join(".", "userbot", "config.py"),
                         os.path.join(".", "recovery.py")]
        for name in self._fix_paths(["__pycache__/*"]):
            always_ignore.append(name)
        parse_gitignore = rules.PARSE_GITIGNORE \
                          if hasattr(rules, "PARSE_GITIGNORE") and \
                          isinstance(rules.PARSE_GITIGNORE, bool) else False
        force_delete = rules.DEL if hasattr(rules, "DEL") and \
                       isinstance(rules.DEL, list) else []
        rules_ignore = rules.IGNORE if hasattr(rules, "IGNORE") and \
                       isinstance(rules.IGNORE, list) else []

        if force_delete:
           force_delete = self._fix_paths(force_delete)

        if rules_ignore:
           rules_ignore = self._fix_paths(rules_ignore)
           for name in rules_ignore:
              always_ignore.append(name)

        ignore = []
        if parse_gitignore:
            try:
                print("Parsing gitignore...")
                if os.path.exists(GITIGNORE):
                    git_ignore = self.__parse_gitignore()
                    for elem in git_ignore:
                        if elem != os.path.join(".", "userbot"):
                            ignore.append(elem)
            except Exception as e:
               print(
                   setColorText(f"Failed to parse gitgignore: {e}",
                                Colors.YELLOW))

        try:
            print("Removing old environment...")
            self._remove(
                self._list_dirs(".", ignore), always_ignore)
        except Exception as e:
            print(
                setColorText(f"Failed to remove old environment: {e}",
                             Colors.RED))
            self._remove_extracted_update_package(self.__package_path)
            return

        if force_delete:
            try:
                print("Force deleting specific directories/files...")
                self._remove(force_delete, rules_ignore)
            except Exception as e:
                print(
                    setColorText(
                        f"Failed to delete specific directories/files: {e}",
                        Colors.YELLOW))

        try:
            print("Installing update package...")
            copytree(self.__package_path, ".", dirs_exist_ok=True)
        except Exception as e:
            print(
                setColorText(f"Failed to install update package: {e}",
                             Colors.RED))
            self._remove_extracted_update_package(self.__package_path)
            return

        print("Installing pip requirements...")
        self._install_requirements()

        try:
            print("Cleaning up...")
            self._remove_extracted_update_package(self.__package_path)
            self._remove(self._fix_paths(["releases"]))
        except Exception as e:
            print(
                setColorText(f"Failed to clean updater environment: {e}",
                             Colors.YELLOW))

        self.__successful = True
        print(setColorText("Update completed.", Colors.GREEN))
        return

    def getSuccessful(self) -> bool:
        return self.__successful

def _apply_update(commit_id: str, auto: bool):
    updater = _Updater(commit_id)
    updater.install_update_package()
    if auto and updater.getSuccessful():
        updater.run_userbot()
    elif updater.getSuccessful():
        print(f"\nHyperUBot version: {updater.userbot_version()}")
    return

def _create_backup():
    if not os.path.exists(os.path.join(".", "userbot")) or \
       not os.path.exists(os.path.join(".", "userbot", "__init__.py")) or \
       not os.path.exists(os.path.join(".", "userbot", "__main__.py")):
       print(setColorText("Failed to backup current version: "\
                          "HyperUBot not installed",
                          Colors.RED))
       return

    temp = None
    try:
        while True:
            temp = input("Do you want to backup the current version? (y/n): ")
            if temp.lower() in ("yes", "y"):
                break
            elif temp.lower() in ("no", "n"):
                raise KeyboardInterrupt
            else:
                print(
                    setColorText("Invalid input. Try again",
                                 Colors.YELLOW))
    except KeyboardInterrupt:
        return
    backup = _Backup()
    bkName = "HyperUBot-" + backup.userbot_version()
    if backup.backup_exists(bkName):
        try:
            while True:
                temp = input(f"A backup of '{bkName}' exists already.\n"\
                             "Overwrite? (y/n): ")
                if temp.lower() in ("yes", "y"):
                    break
                elif temp.lower() in ("no", "n"):
                    raise KeyboardInterrupt
                else:
                    print(
                        setColorText("Invalid input. Try again",
                                     Colors.YELLOW))
        except KeyboardInterrupt:
            return
    backup.generate_backup(bkName)
    return

def _restore_backup():
    restore = _Restore()
    backups = restore.list_backups()
    if not backups:
        print(setColorText("No backups found!", Colors.YELLOW))
        return
    listed_backups = "Select a backup to restore\n\n"
    for key, value in backups.items():
        bkName = value.get("bkname")
        listed_backups += f"[{key}] {bkName}\n"
    print(listed_backups)
    temp = None
    try:
        while True:
            temp = input("Your input (or 'X' to cancel): ")
            if temp.lower() == "x":
                raise KeyboardInterrupt
            elif temp.isnumeric():
                if temp in backups.keys():
                    break
            print(
                setColorText("Invalid input. Try again",
                             Colors.YELLOW))
    except KeyboardInterrupt:
        return
    selected_backup = None
    for key, value in backups.items():
        if temp == key:
            selected_backup = value
            break
    bkName = selected_backup.get("bkname")
    print(f"Are you sure you want to restore '{bkName}'?\n" +\
          setColorText("THIS PROCESS CANNOT BE UNDONE!", Colors.RED))
    try:
        while True:
            temp = input("Your input (y/n): ")
            if temp.lower() in ("yes", "y"):
                break
            elif temp.lower() in ("no", "n"):
                raise KeyboardInterrupt
            else:
                print(
                    setColorText("Invalid input. Try again",
                                 Colors.YELLOW))
    except KeyboardInterrupt:
        return
    restore.restore(selected_backup)
    print(f"\nHyperUBot version: {restore.userbot_version()}")
    return

def _reinstall_userbot():
    print(
        setColorText("This process will delete all downloaded user modules, "\
                     "your configurations including your string "\
                     "session and any other data in HyperUBot's root "\
                     "directory. Please backup your data before you continue. "\
                     "At last, the latest release will be "\
                     "installed automatically.",
                     Colors.YELLOW))
    print(
        setColorText("THIS PROCESS CANNOT BE UNDONE!", Colors.RED))
    try:
        while True:
            temp = input("Continue? (y/n): ")
            if temp.lower() in ("yes", "y"):
                break
            elif temp.lower() in ("no", "n"):
                raise KeyboardInterrupt
            else:
                print(
                    setColorText("Invalid input. Try again",
                                 Colors.YELLOW))
    except KeyboardInterrupt:
        return

    installer = _Installer()
    installer.install_update_package()

    if not installer.getInstallationSuccessful():
        print(setColorText("Reinstallation not successful.", Colors.YELLOW))

    print(f"\nHyperUBot version: {installer.userbot_version()}")
    return


if __name__ == "__main__":
    args = argv
    auto_updater = False
    print("HyperUBot Recovery System")
    print(f"Recovery version: {VERSION}")
    recovery = _Recovery()
    if len(args) > 1 and args[1].lower() == "-autoupdate":
        auto_updater = True
        recovery.recovery_mode = setColorText("AUTO UPDATE", Colors.CYAN)
    print(f"HyperUBot version: {recovery.userbot_version()}")
    print(f"Mode: {recovery.recovery_mode}")
    if auto_updater:
        try:
            commit_id = args[2]
        except:
            print(setColorText("Commit ID required!", Colors.YELLOW))
            quit(1)
        _apply_update(commit_id, auto_updater)
        quit()
    temp = None
    try:
        while True:
            print("\nMain Menu")
            print("[1] Run HyperUBot")
            print("[2] Run HyperUBot (safe mode)")
            print("[3] Apply update")
            print("[4] Backup current version")
            print("[5] Restore")
            print("[6] Reinstall HyperUBot")
            print("[7] Exit\n")
            num = input("Your input [1-7]: ")
            if num == "1":
                recovery.run_userbot()
                break
            elif num == "2":
                recovery.run_userbot(True)
                break
            elif num == "3":
                print("\nMain Menu > Apply update")
                try:
                    while True:
                        temp = input("Commit ID (or 'X' to cancel): ")
                        if temp:
                            break
                        else:
                            print(
                                setColorText("Invalid input. Try again",
                                             Colors.YELLOW))
                except KeyboardInterrupt:
                    pass
                if temp and temp.lower() != "x":
                    _apply_update(temp, auto_updater)
            elif num == "4":
                print("\nMain Menu > Backup current version")
                _create_backup()
            elif num == "5":
                print("\nMain Menu > Restore")
                _restore_backup()
            elif num == "6":
                print("\nMain Menu > Reinstall HyperUBot")
                _reinstall_userbot()
            elif num == "7":
                raise KeyboardInterrupt
            else:
                print(setColorText("Invalid input!", Colors.YELLOW))
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(
            setColorText(f"Recovery crashed: {e}", Colors.RED_BG))
        quit(1)
    quit()
