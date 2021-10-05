import glob
import music_tag
import shutil
from datetime import datetime as d
import re
import filecmp
from .utils.kdeconnect import get_kdeconnect_device
import logging
import argparse
from subprocess import run
from .utils.folderformat import *
from .utils.misc import clean_folders

__version__ = '1.0.0'


def main():
    """
    The main program. Do I need to explain what the program does?
    :return: nothing. it's a program.
    """
    def str2bool(v):
        if isinstance(v, bool):
            return v
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')

    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="warning", help="Provide logging level. Example --log debug")
    parser.add_argument("--path", default=os.path.expanduser("~/Music/"),
                        help="Path where all of the music is stored.")
    parser.add_argument('--excludedartists', help='List of excluded artists. Example: '
                                                  '--excludedartists "Bad Artist,'
                                                  'Garbage,Soundtrack Artist"', type=str)
    parser.add_argument('--excludedalbums', help='List of excluded albums. Example: '
                                                 '--excludedalbums "Bad Album,'
                                                 'Big Soundtrack,I Don\'t Know"', type=str)
    parser.add_argument('--excludedtracks', help='List of excluded tracks. Example: '
                                                 '--excludedtracks "Sad Song,A Hated Song,'
                                                 '1x1,Ouch"', type=str)
    parser.add_argument("--convert", help="If specified, converts music files to "
                                          "specified file extension. Example --convert mp3")
    parser.add_argument("--folderformat", help="If specified, this will format the folder using "
                                               "desktop.ini or .desktop to (hopefully) set the "
                                               "folder's icon to the album artwork.",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("--force-ffmpeg", help="This, combined with --convert, will bypass any "
                                               "checks verifying whether FFmpeg is installed or not.",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("--force-check-files", help="This option forces the program to check if "
                                                    "there are any file differences, if the file "
                                                    "already exists.",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("--automatic-delete", help="This option will make the program delete the "
                                                   "old file after it is done transferring/sorting"
                                                   " said file. Useful for sorting, but can also "
                                                   "be very dangerous if used incorrectly. "
                                                   "Please know what you're doing.",
                        action=argparse.BooleanOptionalAction)
    parser.add_argument("--custom-format", help="If specified, will be used to customize how songs "
                                                "are placed/sorted. Example: "
                                                "--custom-format "
                                                "\"{t.artist}||({t.year}) {t.album}||"
                                                "{t.tracknumber} {t.title}\" will sort songs like "
                                                "Artist Name/(2021) Album Name/1 Title.mp3.\nNOTE: "
                                                "This is experimental, things may break, your cat "
                                                "might bark and sit on the ceiling and your "
                                                "dishwasher might be your new oven.")

    # define KDE Connect arguments
    parser.add_argument("--kconnect", type=str2bool, nargs='?',
                        const=True, default=True,
                        help="Enables or disables KDE Connect features. On by default. To disable, "
                             "use --kconnect false")
    parser.add_argument("--kconnectdir", default="Music",
                        help="If the program will pass through KDE Connect to transfer directly to "
                             "the user's phone, this will specify in which directory it will transfer "
                             "all of the files to.")

    args = parser.parse_args()  # get and parse arguments passed by user

    if args.folderformat:      # if we should inject desktop.ini and .directory files
        if os.name not in ["nt", "posix"]:
            print("Cannot complete folder formatting because Atlas is an idiot")
            logging.error("warned user that directory files is impossible due to macOS "
                          "and the fact that I don't have any Apple products at home "
                          "so I can't even implement this feature for macOS devices.")
            args.folderformat = False
            # I don't have a macOS system and I really don't wanna mess with KVM for now.
        else:
            # import necessary dependencies for that to happen
            from PIL import Image
            import io

    log_level = args.log  # get log level argument
    if log_level:
        numeric_level = getattr(logging, log_level.upper(), None)  # get logging level
        if not isinstance(numeric_level, int):                     # if it couldn't be found
            raise ValueError(f'Invalid log level: {log_level}')    # cry ourselves to sleep
        logging.basicConfig(level=numeric_level)                   # if it was found, tell logging

    path = args.path  # get path argument

    convert_to = None  # define variable
    if args.convert:   # if the user wanted to convert their music files
        if shutil.which('ffmpeg') or args.force_ffmpeg:
            # if args.convert in (check_output(["ffmpeg", "-formats"])).decode("utf-8").strip() \
            #         or args.force_ffmpeg:
            #     # It just works.
            #     convert_to = args.convert
            # else:
            #     print('Audio file type not supported by ffmpeg (or at least I don\'t think so)')
            # messy approach to detect if the music format is supported
            convert_to = args.convert  # set our variable to file extension to convert to
        else:
            # ffmpeg is not installed; cry at the user
            print('FFmpeg not installed; to convert music files to a certain type, '
                  'please install ffmpeg first.')
            exit(1)

    glob_path = f"{path}**/*.*" if path.endswith('/') else f"{path}/**/*.*"  # get glob directory stuff

    check_if_files_are_different = args.force_check_files
    delete_file = args.automatic_delete

    print(f"Looking for files in {path}...")      # tell the user where we're looking
    thing = glob.glob(glob_path, recursive=True)  # get files
    logging.debug(f"{len(thing)} files found.")   # we found 1234 files

    tracks = []  # list used to store tracks

    excluded_artists = [item.lower() for item in (args.excludedartists.split(',')
                                                  if args.excludedartists else [])]
    excluded_albums = [item.lower() for item in (args.excludedalbums.split(',')
                                                 if args.excludedalbums else [])]
    excluded_tracks = [item.lower() for item in (args.excludedtracks.split(',')
                                                 if args.excludedtracks else [])]

    exclude_regex_pattern = re.compile("[\0<>:\"\\|?\-*]")  # IT JUST WORKS.
    # 2021-09-07: I don't exactly remember what this does.

    logging.info("Looking for tracks in files found...")
    scan_time = d.timestamp(d.now())  # set a variable for when we started scanning, for debugging
    for file in thing:
        logging.debug(f"scanning {file}")
        if file.lower().endswith('.zip'):  # mutagen might hate us otherwise
            tags = None
        else:
            try:
                tags = music_tag.load_file(file)  # load music tags
            except NotImplementedError:  # if the music format is not supported
                tags = None              # the file isn't music.
        if tags:  # if the file is music
            try:
                track = Track(tags, file)  # store tags into a class
            except KeyError:
                logging.debug(f"{file} isn't an actual music file. whoops.")
            else:
                # should we exclude it?
                exclude = False
                for artist in excluded_artists:
                    if exclude_regex_pattern.sub('', artist) == exclude_regex_pattern. \
                            sub('', track.artist.lower().replace('ç', '').replace('é', '')
                                                        .replace('à', '')):  # fucking stupid.
                        exclude = True
                for album in excluded_albums:
                    if exclude_regex_pattern.sub('', album) == \
                            exclude_regex_pattern.sub('', track.album.lower()):
                        exclude = True
                for track_name in excluded_tracks:
                    if exclude_regex_pattern.sub('', track_name) == \
                            exclude_regex_pattern.sub('', track.title.lower()):
                        exclude = True
                # I don't know what the fuck this code is doing but it works.
                if not exclude:           # if it shouldn't be excluded
                    tracks.append(track)  # add it to the list of tracks
                else:                                                # if it should be excluded
                    logging.debug("uh oh, this should be excluded")  # don't add it to the list
        else:  # if it just isn't a music file
            logging.debug(f"{file} is not an audio file.")
    print(f"{len(tracks)} tracks found.")  # hey we found 1200 tracks
    logging.info(f"It also took me {d.timestamp(d.now()) - scan_time} seconds to scan all that.")

    # get output directory
    remote_path = ""  # copy music over there

    # KDE Connect
    kconnect_device_id = None
    if os.name == 'posix' and args.kconnect:  # KDE Connect integration only works on Linux. :(
        thing = get_kdeconnect_device()       # get the KDE Connect device we should use
        if thing:                             # if there is a kde connect device we will use
            kconnect_device_id = thing[1]     # get the device's ID for later, see bottom of code
            thing = thing[0]                  # get the path item
            print(f"Using {thing.name} ({thing.path}) through KDE Connect.")
            dir_to_copy = args.kconnectdir.replace('/', '').replace('\\', '')  # we just need names
            remote_path = thing.path + f"/{dir_to_copy}/"  # set directory we should copy to

    # Regular path copying
    if not remote_path:  # if we aren't using KDE Connect
        while not remote_path:
            maybe_path = None
            try:
                maybe_path = input("Which path should I use for copying? ")
            except KeyboardInterrupt:
                # user did Ctrl+C to interrupt
                print("Alright, alright, jeez.")
                exit(1)
            if not maybe_path:
                print("That's nothing.")  # user didn't insert anything.
            else:
                if os.path.isdir(maybe_path):     # if it is a directory
                    logging.info("Valid path, sir!")
                    remote_path = maybe_path      # use it
                elif os.path.isfile(maybe_path):  # if it's a file
                    print("That is a file, not a directory.")
                else:                             # if it's nothing
                    print("That directory does not exist.")

    # Finalize remote_path string
    if os.name == 'nt':  # de-windows-ify the path
        remote_path = remote_path.replace('\\', '/')
    if not remote_path.endswith('/'):
        remote_path += '/'  # for standardization.

    new_format_string = False  # is there a new format replacing an old one?
    raw_format_string = None   # the format string we should follow
    old_format = None          # the saved format string in the specified directory
    if args.custom_format:                      # if the user wanted custom directory formats
        raw_format_string = args.custom_format  # sure thing i guess
    if os.path.exists(remote_path + '.outsyncer_format'):  # if there's already a custom format
        file_content = open(f'{remote_path}.outsyncer_format', 'r').read().replace('\n', '')
        if raw_format_string != file_content:  # if the directory's custom format is different
            new_format_string = True
            old_format = file_content
            # so that we can delete the old format later
        else:
            # if the directory has a custom format and the user didn't input any custom format
            # use the directory's custom format
            raw_format_string = file_content

    # atlas was here. continue writing comments. i don't wanna miss the bus.
    # gotcha, past atlas!
    try:
        directory_file_name = directory_file_names[os.name]
        # get the OS' equivalent of .directory or desktop.ini
    except KeyError:
        # what the hell is this OS?
        directory_file_name = None

    overall_time = d.timestamp(d.now())     # start transfer timer
    for index, track in enumerate(tracks):  # loop through every track
        old_dist_path = None  # OH MY FUCKING GOD PYCHARM SHUT THE FUCK UP THIS WON'T BE UNDEFINED
        # I think I was angry here?
        if raw_format_string:  # if we should format according to the user
            format_string = raw_format_string.format(t=track).replace('/', '')
            # format the actual string for our needs, and don't make any accidental directories
            path_strings = format_string.split('||')  # differentiate the different directories
            path_strings = [exclude_regex_pattern.sub('', x) for x in path_strings]
            # pass our magic regex thing to make sure that creating a directory won't error
            if len(path_strings) != 3:  # if we don't have 3 directories to create
                print("The custom directory format is invalid. There must be exactly three "
                      "directories (separated by ||), the first one for the artist, the second one "
                      "for the album and the third one for the song's name. Use --help for more info.")
                # whine about it
                exit(1)
            artist_dir = path_strings[0] + "/"             # artist directory
            album_dir = path_strings[1] + "/"              # album directory
            song_directories = f"{artist_dir}{album_dir}"  # the song's directory
            song_file = f"{song_directories}" \
                        f"{path_strings[2]}"               # the song's file path
            song_path = song_file + f".{track.file_ext}"   # the song's file name and type
            dist_path = f"{remote_path}{song_path}"        # the ACTUAL song path
            if new_format_string:  # if we're replacing an old format already saved in directory
                path_strings = old_format.format(t=track).replace('/', '').split('||')
                path_strings = [exclude_regex_pattern.sub('', x) for x in path_strings]
                # do the custom format path directories nonsense

                old_artist_dir = path_strings[0] + "/"                     # artist's old directory
                old_album_dir = path_strings[1] + "/"                      # album's old directory
                old_song_directories = f"{old_artist_dir}{old_album_dir}"  # old directories
                old_song_file = f"{old_song_directories}" \
                                f"{path_strings[2]}"                       # old song file path
                old_song_path = old_song_file + f".{track.file_ext}"       # old song file name
                old_dist_path = f"{remote_path}{old_song_path}"            # old song TRUE filepath

        else:  # if we DON'T have to format the format string nonsense things
            artist_dir = f"{exclude_regex_pattern.sub('', track.artist.lower())}/".replace(' ', '')
            # format artist name in a way that "Three Days Grace" becomes "threedaysgrace"
            album_dir = f"{exclude_regex_pattern.sub('', track.album.lower())}/".replace(' ', '')
            # format album name so that "One-X" becomes "onex"
            song_directories = f"{artist_dir}{album_dir}".replace(' ', '')  # directories for song
            song_file = f"{song_directories}" \
                        f"{exclude_regex_pattern.sub('', track.title.lower())}".replace(' ', '')
            # also format file name around the title, so if it's "It's All Over",
            # it should look like "itsallover"

            # directories for song
            song_path = song_file + f".{track.file_ext}"  # song file name and extension
            dist_path = f"{remote_path}{song_path}"       # song file path

        if not os.path.exists(remote_path):  # if the specified directory doesn't exist
            os.mkdir(remote_path)            # make one
        if not os.path.exists(f"{remote_path}{artist_dir}"):  # if the artist directory existn't
            os.mkdir(f"{remote_path}{artist_dir}")            # make one
        if not os.path.exists(f"{remote_path}{artist_dir}{album_dir}"):  # if album dir no exist
            os.mkdir(f"{remote_path}{artist_dir}{album_dir}")            # make

        do_copy = True  # if we should, ha, y'know, copy.
        if convert_to:  # if we should convert
            if os.path.exists(dist_path):  # if unconverted file exists
                print(f"{dist_path} has been found; deleting in favor of the converted file...")
                # warn the user
                os.remove(dist_path)  # remove unconverted file
            song_path = song_file + f".{convert_to}"  # remake song filename to use the new format
            dist_path = f"{remote_path}{song_path}"   # remake song path
        if os.path.exists(dist_path):  # seems like this song was already transferred
            logging.info(f"Whoop! {dist_path} already exists.")
            if check_if_files_are_different and not convert_to:
                # we're allowed to see the file differences
                logging.info(f"Is {dist_path} the same as {track.filename}?")
                do_copy = not filecmp.cmp(track.filename, dist_path)
                # verify if the two are different
                if not do_copy:  # they're identical
                    logging.info(f"{dist_path} and {track.filename} are identical. Skipping.")
                else:  # they're different
                    logging.info(f"{dist_path} and {track.filename} are different; overwriting.")
                    os.remove(dist_path)
            else:
                # we're not allowed to check for differences.
                do_copy = False  # don't copy, it already exists
        if new_format_string:
            if os.path.exists(old_dist_path):
                # the old format's equivalent of the song we're transferring was found
                print(f"{old_dist_path} has been found; deleting in favor of the new path format...")
                os.remove(old_dist_path)
                # remove so that it can also migrate to the new format
        if do_copy or (convert_to and do_copy):  # if we're allowed to copy
            song_path = song_path.replace('  ', ' ')  # no funky song path anomalies
            logging.debug(f"copy {track.filename} ({track.title} by {track.artist}) to "
                          f"{remote_path}{song_path}")
            start = d.timestamp(d.now())  # start the timer for how much time it takes to transfer
            print(f"Copying {track.title} by {track.artist}...")
            converted_filename = None  # initializing the variable for the filename for conversion
            do_convert = False  # should we convert
            # hey me, pick up the slack. I don't wanna miss the bus.
            # can do, past me.
            if convert_to:  # if we must convert
                if dist_path.endswith(convert_to):
                    # if the file we're trying to convert is already in said format
                    logging.info(f'whoops, {song_path} is already in {convert_to}, we won\'t convert')
                    # no need to convert
                    do_convert = False  # remember that we don't need to convert
                else:
                    # file type is different, we should convert.
                    converted_filename = f"output.{convert_to}"  # set the variable
                    do_convert = True   # remember that we do    need to convert
            try:
                # Putting this in a try: except: block so that the user can do KeyboardInterrupt
                # and the program will automatically clean up after itself.
                if do_convert:  # if we should convert
                    # convert
                    run_results = run(['ffmpeg', '-i', track.filename,  # hey FFmpeg, convert this
                                       '-map_metadata', '0',            # keep its metadata
                                       converted_filename],             # save it to output.mp3
                                      capture_output=True)              # to inspect errors
                    if run_results.returncode != 0:  # if FFmpeg is unhappy
                        if f"Unable to find a suitable output format for '{converted_filename}'" \
                                in run_results.stderr.decode('utf-8'):
                            # the user passed an invalid file extension
                            print(f"\nUh oh, it seems like FFmpeg does not "
                                  f"support \"{convert_to}\" as a file extension. "
                                  f"Make sure it's written properly, or use another "
                                  f"format.")
                        else:
                            # FFmpeg is just unhappy and we don't know why.
                            print(f"\nUh oh. Something's not right. FFmpeg had an error.\n"
                                  f"Here are a few last lines from the ffmpeg output:\n")
                            print('\n'.join(run_results.stderr.decode('utf-8').split('\n')[-6:-1]))
                        exit(run_results.returncode)
                    shutil.move(converted_filename, dist_path)  # then transfer converted file
                else:
                    # just copy the file. easy. no need to do complex funky conversion stuff.
                    shutil.copy(track.filename, dist_path)
                if delete_file:
                    # delete the file, as we are done sorting it.
                    os.remove(track.filename)
            except KeyboardInterrupt:
                # delete the file
                print("\n\nKeyboardInterrupt received, attempting to delete file...\n"
                      "You can abort this process completely by sending KeyboardInterrupt now.")
                # Or if you were less kind, pkill python3
                try:
                    os.remove(dist_path)
                except FileNotFoundError:
                    # oh well
                    pass
                if converted_filename:
                    os.remove(converted_filename)  # remove temporary converted file
                print("File deleted. Aborting.")
                exit(1)
            milliseconds = (d.timestamp(d.now()) - start) * 1000
            # how much time did we take to transfer that file?
            logging.info(f"{milliseconds}ms to transfer {track.title} by {track.artist}.")
        if (not os.path.exists(f"{remote_path}{artist_dir}{album_dir}{directory_file_name}")) and \
                args.folderformat:
            # if the directory doesn't have a directory file and
            # if the user told us to generate one

            # generate favicon.ico file
            artwork = Image.open(io.BytesIO(track.artwork.data))           # open the artwork image
            artwork.save(f'{remote_path}{artist_dir}{album_dir}favicon.ico')  # save it as .ico

            # generate desktop.ini/.directory file
            open(f"{remote_path}{artist_dir}{album_dir}{directory_file_name}", 'wt'). \
                write(format_directory_file(track).replace('\n', '\r\n'))
            if os.name == 'nt':
                # because fucking Windows is fucking Windows.
                # you have to use these commands to make Windows look at the desktop.ini file.
                os.system(f'attrib +S +H "{remote_path}{artist_dir}{album_dir}{directory_file_name}"')
                os.system(f'attrib +R "{remote_path}{artist_dir}{album_dir.removesuffix("/")}"')
                # I don't know what these commands do.

    print("Cleaning empty directories...")
    clean_folders(remote_path)
    clean_folders(path)

    print(f"\nAll done! It took me {d.timestamp(d.now()) - overall_time} seconds "
          f"to transfer {len(tracks)} songs.")

    if kconnect_device_id:
        # send notification to the device we were transferring to.
        os.system(f'kdeconnect-cli -d "{kconnect_device_id}" --ping-msg "Outsyncer: '
                  f'{len(tracks)} songs have been transferred to this device; check them out."')

    if raw_format_string:
        # save format string for future formatting stuff.
        open(f'{remote_path}.outsyncer_format', 'w+').write(raw_format_string)
