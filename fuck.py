from kdeconnect import *

# shit_yourself = get_devices()
#
# # os.system(f"ls /run/user/{get_userid()}/{shit_yourself[0].id}/primary/")
# # This approach will definitely work. Definitely. I'm more concerned about the user/1000/ part.
# # The id command seems to be my answer though. Fun. Gotta work with regexes now.
# # import re; from subprocess import check_output;
# # re.search(r"(?<=uid=)\d+(?=\()", check_output("id").decode("utf-8").strip()).group(0)
#
# paths = get_kdeconnect_device_path(shit_yourself[0].id, True)
# if not paths:
#     exit("Hey, uh, mind mounting your device for me?")
#
# if type(paths) is list:
#     # print([f"{x.name} ({x.path})" for x in paths])
#     to_use = None
#     while not to_use:
#         print("hey so uh there are many options here, gimme some help.\n")
#         for index, x in enumerate(paths):
#             print(f"{index}: {x.name} ({x.path})")
#         index = input("\nso, what's your option?: ")
#         if not index.isdigit():
#             print("I'M ASKING FOR A DAMN NUMBER.")
#         else:
#             try:
#                 index = int(index)
#                 to_use = paths[index]
#             except IndexError:
#                 print("invalid. fuck you.\n")
# else:
#     print("There's only one answer, " + paths.path)

# os.system(f"ls kdeconnect://{shit_yourself[0].id}/primary/") Nope.
