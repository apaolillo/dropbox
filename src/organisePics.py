
import dropbox
import sys
from pprint import pprint

STORED_PICTURES_PATH = '/Camera Uploads'
TARGET_PICS_DIR = '/antonio/pictures_master'


class PicOrganiser(object):
    def __init__(self, dropboxToken):
        self._dbx = self._getDropboxConnection(dropboxToken)
        self._picList = None

    def _getDropboxConnection(self, dropboxToken):
        return dropbox.Dropbox(dropboxToken)

    def _lsdir(self, dirpath):
        fileList = []

        listFolderResult = self._dbx.files_list_folder(dirpath)

        fileList.extend(map(lambda e: e.name, listFolderResult.entries))

        while(listFolderResult.has_more):
            cursor = listFolderResult.cursor
            listFolderResult = self._dbx.files_list_folder_continue(cursor)
            fileList.extend(map(lambda e: e.name, listFolderResult.entries))

        return sorted(fileList)

    def _fileExists(self, path):
        try:
            self._dbx.files_get_metadata(path)
            return True
        except dropbox.exceptions.ApiError:
            return False

    def _fileExistsAndIsDir(self, dirpath):
        try:
            self._dbx.files_list_folder(dirpath)
            return True
        except dropbox.exceptions.ApiError:
            return False

    def _mkdir(self, dirpath):
            if self._fileExistsAndIsDir(dirpath):
                pass
            elif self._fileExists(dirpath):
                excpetionTpl = "The file '{}' exists and is not a directory."
                raise Exception(excpetionTpl.format(dirpath))
            else:
                self._dbx.files_create_folder(dirpath)

    def _getYmdFromFilename(self, filename):
        date = filename.split(' ')[0]
        [year, month, day] = date.split('-')

        assert(year.isdecimal() and len(year) == 4)
        assert(month.isdecimal() and len(month) == 2)
        assert(day.isdecimal() and len(day) == 2)

        return [year, month, day]

    def getPicList(self):
        if (self._picList is None):
            self._picList = self._lsdir(STORED_PICTURES_PATH)
        return self._picList

    def organisePicMove(self):
        fileList = self.getPicList()

        # Create years-month dictionary
        years = dict()
        for filename in fileList:
            [year, month, day] = self._getYmdFromFilename(filename)

            if year not in years:
                years[year] = dict()

            if month not in years[year]:
                years[year][month] = list()

            years[year][month].append(filename)
        pprint(years)

        # Create directory tree
        self._mkdir(TARGET_PICS_DIR)
        for year in years:
            yearDirpath = '{rd}/{y}'.format(rd=TARGET_PICS_DIR, y=year)
            self._mkdir(yearDirpath)
            for month in years[year]:
                monthDirpath = '{r}/{m}'.format(r=yearDirpath, m=month)
                self._mkdir(monthDirpath)

        # Move the files
        for filename in fileList:
            [year, month, day] = self._getYmdFromFilename(filename)

            file_src = '{r}/{f}'.format(r=STORED_PICTURES_PATH, f=filename)

            file_dst = '{r}/{y}/{m}/{f}'.format(r=TARGET_PICS_DIR,
                                                y=year,
                                                m=month,
                                                f=filename)

            #self._dbx.files_copy(file_src, file_dst)
            #self._dbx.files_move(file_src, file_dst)
            print("Moving {} to {}".format(file_src, file_dst))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        expMsg = "No input dropbox token given " \
                 "(expected first command line argument)"
        raise Exception(expMsg)

    token = sys.argv[1]

    po = PicOrganiser(token)
    po.organisePicMove()
