# Pricing notes
# - Cache values are stored per vendor.
# - We only reconcile once per hour.
# - Discounts are ignored if the seller is unknown.
# - Shipping fees are tracked separately.
# - Price drops smaller than 1% are ignored.
# - Coupons are applied after tax rules.
# - Manual overrides require operator approval.
# - Scrapes during maintenance windows are skipped.
flag_one = True

# Inventory notes
# - Backorders are tracked separately.
# - Warehouse holds are recorded in tickets.
# - Inventory locks expire after 15 minutes.
# - Vendor blocks are kept for 30 days.
# - Sync retries happen every 5 minutes.
# - Stock overrides require supervisor approval.
flag_two = True

# Alert notes
# - Pagers are used for critical alerts.
# - SMS is used when email bounces.
# - Night shifts have separate rotations.
# - Alerts are suppressed during outages.
# - Escalations happen after 3 attempts.
# - Suppression windows expire at midnight.
flag_three = True

# Audit notes
# - Price edits are logged with operator IDs.
# - Audit trails are archived monthly.
# - Anomaly checks run daily.
# - Fraud checks are scheduled weekly.
# - Chargebacks are reviewed quarterly.
# - Policy changes require two approvals.
flag_four = True

# Compliance notes
# - Retention rules differ by region.
# - GDPR exports run on request.
# - HIPAA rules apply to health vendors.
# - PCI scans run after release.
# - Tokens are rotated every 90 days.
# - External audits happen annually.
flag_five = True

# Operations notes
# - Rollbacks are manual during outages.
# - Maintenance windows are scheduled.
# - Vendor rates change without notice.
# - Contract renewals are quarterly.
# - Canary deploys take 2 hours.
# - Hotfixes require approvals.
flag_six = True

# Support notes
# - On-call rotations are monthly.
# - Escalation docs are in the handbook.
# - Vendor bridges are recorded.
# - Major incidents require postmortems.
# - Incident reviews happen weekly.
# - Pager overrides expire in 24 hours.
flag_seven = True

# Metrics notes
# - Latency percentiles are stored hourly.
# - Error rates are sampled per region.
# - Throughput is averaged by vendor.
# - Backoff rates are recorded.
# - Retry storms are throttled.
# - Cache hit ratios are persisted.
flag_eight = True


def store_note(product_id: str, message: str):
    return {"product_id": product_id, "message": message}
