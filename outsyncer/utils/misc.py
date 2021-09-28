import logging
import glob
import shutil
from .folderformat import *


def clean_folders(folder_to_clean):
    for folder in [x for x in os.listdir(folder_to_clean) if os.path.isdir(f"{folder_to_clean}{x}")]:
        # iterate through every subdirectory in directory
        logging.debug(folder)
        logging.debug(f"{folder_to_clean}{folder}")
        folder_path = f"{folder_to_clean}{folder}"  # get the full path of the directory
        subdirectories = [x for x in os.listdir(folder_path) if
                          os.path.isdir(f"{folder_path}/{x}")]
        im_fucking_tired_i_cant_come_up_with_variable_names = False
        if not subdirectories:
            subdirectories = [folder_path]
            im_fucking_tired_i_cant_come_up_with_variable_names = True
        for subdirectory in subdirectories:
            # for subdirectory in directory we just found
            if not im_fucking_tired_i_cant_come_up_with_variable_names:
                subdirectory_path = f"{folder_path}/{subdirectory}"  # get full path of subdir
            else:
                subdirectory_path = folder_path
            files = glob.glob(f"{subdirectory_path}/*", recursive=True)  # get list of files
            for dir_file_name in directory_file_names.values():
                files = [x for x in files if x != dir_file_name]
                # exclude directory files like .directory or desktop.ini, they aren't actual files.
            if not files:  # if there are no files
                # folder is empty, we will remove it.
                logging.info(f"{subdirectory_path} is empty!")
                shutil.rmtree(subdirectory_path)
