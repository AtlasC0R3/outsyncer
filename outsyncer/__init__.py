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

__version__ = '1.0.0'


def main():
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

    args = parser.parse_args()

    if args.folderformat:
        from PIL import Image
        import io

    log_level = args.log
    if log_level:
        log_level = log_level
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % log_level)
        logging.basicConfig(level=numeric_level)

    # path = "/run/media/atlas/Backup Plus/Music/"  # know where music is stored
    path = args.path

    convert_to = None
    if args.convert:
        if shutil.which('ffmpeg') or args.force_ffmpeg:
            # if args.convert in (check_output(["ffmpeg", "-formats"])).decode("utf-8").strip() \
            #         or args.force_ffmpeg:
            #     # It just works.
            #     convert_to = args.convert
            # else:
            #     print('Audio file type not supported by ffmpeg (or at least I don\'t think so)')
            convert_to = args.convert
        else:
            print('FFmpeg not installed; to convert music files to a certain type, '
                  'please install ffmpeg first.')
            exit(1)

    glob_path = f"{path}**/*.*" if path.endswith('/') else f"{path}/**/*.*"  # get glob directory stuff

    check_if_files_are_different = False

    print(f"Looking for files in {path}...")
    thing = glob.glob(glob_path, recursive=True)  # get files
    logging.debug(f"{len(thing)} files found.")

    tracks = []

    excluded_artists = [item.lower() for item in (args.excludedartists.split(',')
                                                  if args.excludedartists else [])]
    excluded_albums = [item.lower() for item in (args.excludedalbums.split(',')
                                                 if args.excludedalbums else [])]
    excluded_tracks = [item.lower() for item in (args.excludedtracks.split(',')
                                                 if args.excludedtracks else [])]

    pattern = re.compile(r"[\0<>:\"/\\|?*]")  # IT JUST WORKS.

    logging.info("Looking for tracks in files found...")
    scan_time = d.timestamp(d.now())
    for file in thing:
        logging.debug(f"scanning {file}")
        if file.lower().endswith('.zip'):
            tags = None
        else:
            try:
                tags = music_tag.load_file(file)
            except NotImplementedError:
                tags = None
        if tags:
            try:
                track = Track(tags, file)
            except KeyError:
                logging.debug(f"{file} isn't an actual music file. whoops.")
            else:
                exclude = False
                for artist in excluded_artists:
                    if pattern.sub('', artist) == pattern. \
                            sub('', track.artist.lower().replace('ç', '').replace('é', '')
                                                        .replace('à', '')):  # fucking stupid.
                        exclude = True
                for album in excluded_albums:
                    if pattern.sub('', album) == pattern.sub('', track.album.lower()):
                        exclude = True
                for track_name in excluded_tracks:
                    if pattern.sub('', track_name) == pattern.sub('', track.title.lower()):
                        exclude = True
                if not exclude:
                    tracks.append(track)
                else:
                    logging.debug("uh oh, this should be excluded")
        else:
            logging.debug(f"{file} is not an audio file.")
    print(f"{len(tracks)} tracks found.")
    logging.info(f"It also took me {d.timestamp(d.now()) - scan_time} seconds to scan all that.")

    # get output directory
    remote_path = ""  # copy music over there

    # KDE Connect
    kconnect_device_id = None
    if os.name == 'posix' and args.kconnect:  # KDE Connect integration only works on Linux.
        thing = get_kdeconnect_device()
        if thing:
            kconnect_device_id = thing[1]
            thing = thing[0]
            print(f"Using {thing.name} ({thing.path}) through KDE Connect.")
            dir_to_copy = args.kconnectdir.replace('/', '').replace('\\', '')
            remote_path = thing.path + f"/{dir_to_copy}/"
            # so that it moves the music to a dedicated directory

    # Regular path copying
    if not remote_path:
        while not remote_path:
            maybe_path = None
            try:
                maybe_path = input("Which path should I use for copying? ")
            except KeyboardInterrupt:
                print("Alright, alright, jeez.")
                exit(1)
            if not maybe_path:
                print("That's nothing.")
            else:
                if os.path.isdir(maybe_path):
                    logging.info("Valid path, sir!")
                    remote_path = maybe_path
                elif os.path.isfile(maybe_path):
                    print("That is a file, not a directory.")
                else:
                    print("That directory does not exist.")

    # Finalize remote_path string
    if os.name == 'nt':  # de-windows-ify the path
        remote_path = remote_path.replace('\\', '/')
    if not remote_path.endswith('/'):
        remote_path += '/'

    new_format_string = False
    raw_format_string = None
    old_format = None
    if args.custom_format:
        raw_format_string = args.custom_format
    if os.path.exists(f'{remote_path}.outsyncer_format'):
        file_content = open(f'{remote_path}.outsyncer_format', 'r').read().replace('\n', '')
        if raw_format_string != file_content:
            new_format_string = True
            old_format = file_content
        else:
            raw_format_string = file_content

    try:
        directory_file_name = directory_file_names[os.name]
    except KeyError:
        directory_file_name = None

    overall_time = d.timestamp(d.now())  # Start the timer, I guess.
    for index, track in enumerate(tracks):
        old_dist_path = None  # OH MY FUCKING GOD PYCHARM SHUT THE FUCK UP THIS WON'T BE UNDEFINED FUCK
        if raw_format_string:
            format_string = raw_format_string.format(t=track).replace('/', '')
            path_strings = format_string.split('||')
            path_strings = [pattern.sub('', x) for x in path_strings]
            if len(path_strings) != 3:
                print("The custom directory format is invalid. There must be exactly three "
                      "directories (separated by ||), the first one for the artist, the second one "
                      "for the album and the third one for the song's name. Use --help for more info.")
                exit(1)
            artist_dir = path_strings[0] + "/"
            album_dir = path_strings[1] + "/"
            song_directories = f"{artist_dir}{album_dir}"
            song_file = f"{song_directories}" \
                        f"{path_strings[2]}"
            song_path = song_file + f".{track.file_ext}"
            dist_path = f"{remote_path}{song_path}"
            if new_format_string:
                path_strings = old_format.format(t=track).replace('/', '').split('||')
                path_strings = [pattern.sub('', x) for x in path_strings]

                old_artist_dir = path_strings[0] + "/"
                old_album_dir = path_strings[1] + "/"
                old_song_directories = f"{old_artist_dir}{old_album_dir}"
                old_song_file = f"{old_song_directories}" \
                                f"{path_strings[2]}"
                old_song_path = old_song_file + f".{track.file_ext}"
                old_dist_path = f"{remote_path}{old_song_path}"
        else:
            artist_dir = f"{pattern.sub('', track.artist.lower())}/".replace(' ', '')
            album_dir = f"{pattern.sub('', track.album.lower())}/".replace(' ', '')
            song_directories = f"{artist_dir}{album_dir}".replace(' ', '')
            song_file = f"{song_directories}" \
                        f"{pattern.sub('', track.title.lower())}".replace(' ', '')
            song_path = song_file + f".{track.file_ext}"
            dist_path = f"{remote_path}{song_path}"

        if not os.path.exists(remote_path):
            os.mkdir(remote_path)
        if not os.path.exists(f"{remote_path}{artist_dir}"):
            os.mkdir(f"{remote_path}{artist_dir}")
        if not os.path.exists(f"{remote_path}{artist_dir}{album_dir}"):
            os.mkdir(f"{remote_path}{artist_dir}{album_dir}")

        do_copy = True
        if convert_to:
            if os.path.exists(dist_path):  # if unconverted file exists
                print(f"{dist_path} has been found; deleting in favor of the converted file...")
                # warn the user
                os.remove(dist_path)  # remove unconverted file
            song_path = song_file + f".{convert_to}"
            dist_path = f"{remote_path}{song_path}"
            # too lazy to explain
        if os.path.exists(dist_path):
            logging.info(f"Whoop! {dist_path} already exists.")
            if check_if_files_are_different and not convert_to:
                logging.info(f"Is {dist_path} the same as {track.filename}?")
                do_copy = not filecmp.cmp(track.filename, dist_path)
                if not do_copy:
                    logging.info(f"{dist_path} and {track.filename} are identical. Skipping.")
                else:
                    logging.info(f"{dist_path} and {track.filename} are different; overwriting.")
                    os.remove(dist_path)
            else:
                do_copy = False
        if new_format_string:
            if os.path.exists(old_dist_path):
                print(f"{old_dist_path} has been found; deleting in favor of the new path format...")
                os.remove(old_dist_path)
        if do_copy or (convert_to and do_copy):
            song_path = song_path.replace('  ', ' ')
            logging.debug(f"copy {track.filename} ({track.title} by {track.artist}) to "
                          f"{remote_path}{song_path}")
            start = d.timestamp(d.now())
            print(f"Copying {track.title} by {track.artist}...")
            converted_filename = None
            do_convert = False
            if convert_to:
                if dist_path.endswith(convert_to):
                    logging.info(f'whoops, {song_path} is already in {convert_to}, we won\'t convert')
                    # no need to convert
                    do_convert = False
                else:
                    # file type is different, we should convert.
                    converted_filename = f"output.{convert_to}"
                    do_convert = True
            try:
                if do_convert:
                    # convert
                    run_results = run(['ffmpeg', '-i', track.filename,  # hey FFmpeg, convert this
                                       '-map_metadata', '0',  # and keep its metadata
                                       converted_filename],  # and save it to output.mp3
                                      capture_output=True)  # capture output
                    if run_results.returncode != 0:
                        if f"Unable to find a suitable output format for '{converted_filename}'" \
                                in run_results.stderr.decode('utf-8'):
                            # invalid file extension
                            print(f"\nUh oh, it seems like FFmpeg does not "
                                  f"support \"{convert_to}\" as a file extension. "
                                  f"Make sure it's written properly, or use another "
                                  f"format.")
                        else:
                            print(f"\nUh oh. Something's not right. FFmpeg had an error.\n"
                                  f"Here are a few last lines from the ffmpeg output:\n")
                            print('\n'.join(run_results.stderr.decode('utf-8').split('\n')[-6:-1]))
                        exit(run_results.returncode)
                    shutil.move(converted_filename, dist_path)  # then transfer it to device
                else:
                    # copy
                    shutil.copy(track.filename, dist_path)
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
                    os.remove(converted_filename)
                print("File deleted. Aborting.")
                exit(1)
            milliseconds = (d.timestamp(d.now()) - start) * 1000
            logging.info(f"{milliseconds}ms to transfer {track.title} by {track.artist}.")
        if not os.path.exists(f"{remote_path}{artist_dir}{album_dir}{directory_file_name}"):
            # generate favicon.ico file
            # open(f'{remote_path}{artist_dir}{album_dir}favicon.png', 'wb').write(track.artwork.data)
            artwork = Image.open(io.BytesIO(track.artwork.data))
            artwork.save(f'{remote_path}{artist_dir}{album_dir}favicon.ico')
            # generate desktop.ini/.directory file
            open(f"{remote_path}{artist_dir}{album_dir}{directory_file_name}", 'wt'). \
                write(format_directory_file(track).replace('\n', '\r\n'))
            if os.name == 'nt':
                os.system(f'attrib +S +H "{remote_path}{artist_dir}{album_dir}{directory_file_name}"')
                os.system(f'attrib +R "{remote_path}{artist_dir}{album_dir.removesuffix("/")}"')

    print("Cleaning empty directories...")
    for folder in [x for x in os.listdir(remote_path) if os.path.isdir(f"{remote_path}{x}")]:
        logging.debug(folder)
        logging.debug(f"{remote_path}{folder}")
        folder_path = f"{remote_path}{folder}"
        for subdirectory in [x for x in os.listdir(folder_path) if
                             os.path.isdir(f"{folder_path}/{x}")]:
            subdirectory_path = f"{folder_path}/{subdirectory}"
            files = glob.glob(f"{subdirectory_path}/*", recursive=True)
            if not files:
                logging.info(f"{subdirectory_path} is empty!")
                shutil.rmtree(subdirectory_path)

    print(f"\nAll done! It took me {d.timestamp(d.now()) - overall_time} seconds "
          f"to transfer {len(tracks)} songs.")

    if kconnect_device_id:
        os.system(f'kdeconnect-cli -d "{kconnect_device_id}" --ping-msg "Outsyncer: '
                  f'{len(tracks)} songs have been transferred to this device; check them out."')

    if raw_format_string:
        open(f'{remote_path}.outsyncer_format', 'w+').write(raw_format_string)
