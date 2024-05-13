import shutil
import os

class FileManager():
    def __init__(self):
        self.file_move_record = list()

    def is_dir_exist(self, dir_path):
        return os.path.exists(dir_path)
    
    def create_dir(self, path):
        os.makedirs(path, exist_ok=True)
        return

    def clear_dir(self, path, folder_name, remove_folder = True):

        if remove_folder == False:
            self.create_dir(path, folder_name)
        return

    def move_file(self, file_name, src, dst):
        if self.is_dir_exist(dst) == False:
            self.creat_dir(dst)
        shutil.move(os.path.join(src, file_name), os.path.join(dst, file_name))
        return True