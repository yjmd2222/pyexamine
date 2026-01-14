class TaskDispatcher:
    def trigger(self, command: str):
        if command == "add":
            return "add"
        elif command == "edit":
            return "edit"
        elif command == "close":
            return "close"
        elif command == "archive":
            return "archive"
        elif command == "reopen":
            return "reopen"
        elif command == "assign":
            return "assign"
        elif command == "comment":
            return "comment"
        elif command == "label":
            return "label"
        elif command == "sort":
            return "sort"
        elif command == "filter":
            return "filter"
        else:
            return "unknown"
