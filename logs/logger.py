# Logger
# Records user actions, timings, and robot responses
import csv
import os

class Logger:
    def __init__(self, log_path):
        self.log_path = log_path
        log_dir = os.path.dirname(log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        if not os.path.exists(log_path):
            with open(log_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["timestamp", "event_type", "details"])

    def log_event(self, event):
        import datetime
        with open(self.log_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            timestamp = datetime.datetime.now().isoformat()
            event_type = event.get('event_type', '')
            details = event.get('details', '')
            writer.writerow([timestamp, event_type, details])
