from subprocess import check_output
import re
import os


class Device:
    name = ""
    id = ""


class KDEPath:
    name = ""
    path = ""

# https://github.com/forabi/nautilus-kdeconnect/blob/master/kdeconnect.py
# is a huge fucking resource here, KDE Connect has no "usable" API otherwise.
# So we'll have to make our own, as shown there.


def get_devices():
    devices_a = []
    devices = check_output(["kdeconnect-cli", "-a"]).decode("utf-8").strip().split("\n")
    if devices == [""]:
        return None
    for device in devices:
        device_name = re.search(r"(?<=-\s).+(?=:\s)", device).group(0)
        device_id = re.search(r"(?<=:\s)[a-z0-9_]+(?=\s\()", device).group(0).strip()
        device_thing = Device()
        device_thing.name = device_name
        device_thing.id = device_id
        print(f"Found {device_name} ({device_id}) through KDE Connect!")
        devices_a.append(device_thing)
    return devices_a


def get_userid():
    return re.search(r"(?<=uid=)\d+(?=\()", check_output("id").decode("utf-8").strip()).group(0)
    # get real


# def send_files(files: list, device_id):
#     """
#     :param files: ["/tmp/file.png", "~/cool_cat_pictures/1.png", "questionable-file.png"]
#     :param device_id: the kde connect device ID, obtained through get_devices()
#     :return:
#     """
#     for file in files:
#         # call(["kdeconnect-cli", "-d", device_id, "--share", file.get_uri()])
#         return


def auto_guess_directory(directory: str):
    if os.path.exists(f'{directory}/Music'):
        # Well there we go, we've found a path with a music directory.
        music_path = f'{directory}/Music'
        if len(os.listdir(f'{directory}/Music')) != 0:
            # There's actually something in that folder. It could be music.
            return True


def get_kdeconnect_device_path(device_id: str, attempt_to_guess=True):
    """
    yeah
    :param device_id: the device id obtained using get_devices()
    :param attempt_to_guess: if True, it'll attempt to find one directory with a music directory.
    if one is found, then return that path. if none are found, return everything.
    :return: will return either a KDEPath() object or a list of KDEPath() objects
    """
    device_path = f"/run/user/{get_userid()}/{device_id}/"
    # [f.name for f in os.scandir(device_path) if f.is_dir()]
    subdirectories = [x for x in os.scandir(device_path) if x.is_dir()]
    # find all filesystem exposures
    if len(subdirectories) == 1:
        thing = subdirectories[0]  # Thanks, user, for only having one location for everything! =D
        yeah = KDEPath()
        yeah.path = thing.path
        yeah.name = thing.name
        return yeah
    else:  # god dammit user >:(
        to_return = []
        for uhh_fuck_how_do_I_name_this in subdirectories:
            if attempt_to_guess:
                thingy = auto_guess_directory(uhh_fuck_how_do_I_name_this.path)
                if thingy:
                    thingy = KDEPath()
                    thingy.path = uhh_fuck_how_do_I_name_this.path
                    thingy.name = uhh_fuck_how_do_I_name_this.name
                    return thingy
            subdirectory = KDEPath()
            subdirectory.name = uhh_fuck_how_do_I_name_this.name
            subdirectory.path = uhh_fuck_how_do_I_name_this.path
            to_return.append(subdirectory)
        return to_return


def get_kdeconnect_device():
    shit_yourself = get_devices()  # get connected devices
    if not shit_yourself:
        print("No KDE Connect devices connected.")
        return None  # No devices connected.

    device_to_use = None
    if len(shit_yourself) != 1:  # there are multiple devices connected at once
        print("Multiple KDE Connect devices detected: please pick one.\n")
        for index, x in enumerate(shit_yourself):
            print(f"{index}: {x.name} ({x.id})")  # list all options to the user

        while not device_to_use:
            index = input("\nPlease pick an option: ")
            if not index.isdigit():
                print("That's, uh, not a number.")
            else:
                try:
                    index = int(index)  # turn index to an int
                    device_to_use = shit_yourself[index]
                    # try getting the option the user asked for
                except IndexError:
                    print("Sorry, that's not a valid option.\n")  # that wasn't an option.
    else:
        device_to_use = shit_yourself[0]  # there's only one option. no point in asking.

    paths = get_kdeconnect_device_path(device_to_use.id, False)  # get device's path (s)
    if not paths:
        print("Device not mounted. Please mount it.")
        while not paths:
            try:
                action = input("Abort, Retry or Ignore? ")
            except KeyboardInterrupt:
                print("\nOw.")
                exit(1)
                return
            action = str(list(action.lower())[0])
            if action == 'r':
                paths = get_kdeconnect_device_path(device_to_use.id)
            elif action == 'a':
                exit(1)
            elif action == 'i':
                return None
            else:
                print("That wasn't a valid option.")

    if type(paths) is list:
        # print([f"{x.name} ({x.path})" for x in paths])
        to_use = None
        print("There are multiple filesystem exposures detected. Please pick an option.\n")
        default_index = None
        for index, x in enumerate(paths):
            name = x.name
            if not default_index:
                if auto_guess_directory(x.path):
                    name += " (default)"
                    default_index = index
            print(f"{index}: {name} ({x.path})")
        while not to_use:
            try:
                index = input("\nPlease specify an index: ")
            except KeyboardInterrupt:
                print("Ow. That hurt, you know.")
                exit(1)
                return  # Shut the fuck up, PyCharm.
            if not index:
                if default_index:
                    index = default_index
                else:
                    print("Please enter a number.")
            else:
                if not index.isdigit():
                    print("That's not a number.")
            if index:
                try:
                    index = int(index)
                    to_use = paths[index]
                except IndexError:
                    print("That is not in the list.")
    else:
        to_use = paths
    return to_use
