from time import perf_counter


class DownloadStatistics:
    def __init__(self, timestamps_er_measure=30):
        self.last_time = 0
        self.speed = 0
        self.current_timestamp = 0
        self.max_timestamp = timestamps_er_measure
        return

    def report_block_downloaded(self, block_size):
        self.current_timestamp += 1
        if self.current_timestamp == self.max_timestamp:
            current_time = perf_counter()
            self.speed = block_size / (current_time - self.last_time)
            self.last_time = current_time
            self.current_timestamp = 0
        return

    def get_speed(self):
        return self.speed
