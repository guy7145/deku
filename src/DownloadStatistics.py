import time


class DownloadStatistics:
    def __init__(self, timestamps_er_measure=30):
        self.downloaded = 0
        self.start_time = None
        self.time_passed = 0
        return

    def report_block_downloaded(self, block_size):
        if self.start_time is None:
            self.start_time = time.time()

        self.downloaded += block_size
        self.time_passed = time.time() - self.start_time
        return

    def get_speed(self):
        if self.time_passed == 0:
            return 0
        return self.downloaded / self.time_passed
