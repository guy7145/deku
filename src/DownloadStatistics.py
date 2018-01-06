from time import perf_counter


class DownloadStatistics:
    def __init__(self, timestamps_er_measure=30):
        self.downloaded = 0
        self.time_passed = 0
        self.last_time = 0
        return

    def report_block_downloaded(self, block_size):
        current_time = perf_counter()
        current_time_passed = current_time - self.last_time
        self.last_time = current_time
        self.downloaded += block_size
        self.time_passed += current_time_passed
        return

    def get_speed(self):
        if self.time_passed == 0:
            return 0
        return self.downloaded / self.time_passed
