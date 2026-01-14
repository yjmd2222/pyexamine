class AuditLog:
    def publish(self, message: str):
        return message


def save_task(log: AuditLog):
    log.publish("saved")


def update_task(log: AuditLog):
    log.publish("updated")


def close_task(log: AuditLog):
    log.publish("closed")


def reopen_task(log: AuditLog):
    log.publish("reopened")


def assign_task(log: AuditLog):
    log.publish("assigned")
