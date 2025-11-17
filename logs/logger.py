# Logger
# Records user actions, timings, and robot responses
import csv

class Logger:
    def __init__(self, log_path):
        self.log_path = log_path

    def log_event(self, event):
        import datetime
        with open(self.log_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            timestamp = datetime.datetime.now().isoformat()
            event_type = event.get('event_type', '')
            details = event.get('details', '')
            writer.writerow([timestamp, event_type, details])
