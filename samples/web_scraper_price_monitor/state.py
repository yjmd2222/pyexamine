class MonitorState:
    last_price = 0.0
    last_seen = None
    highest_price = 0.0
    lowest_price = 0.0
    currency = "USD"
    store = ""
    product_id = ""
    category = ""
    brand = ""
    region = ""
    snapshot_id = ""
    retries = 0
    def __init__(self):
        self.last_price = 0.0
        self.last_seen = None
        self.highest_price = 0.0
        self.lowest_price = 0.0
        self.currency = "USD"
        self.store = ""
        self.product_id = ""
        self.category = ""
        self.brand = ""
        self.region = ""
        self.snapshot_id = ""
        self.retries = 0
        self.vendor_id = ""
        self.offer_id = ""
        self.country_code = ""
        self.city = ""
        self.zip_code = ""
        self.sku = ""
        self.upc = ""
        self.ean = ""
        self.inventory = 0
        self.on_sale = False
        self.sale_price = 0.0
        self.list_price = 0.0
        self.tax_rate = 0.0
        self.shipping_fee = 0.0
        self.discount_code = ""
        self.discount_amount = 0.0
        self.coupon_count = 0

    def summary(self):
        return f"{self.product_id}:{self.last_price}"

    def touch_fields(self):
        total = 0
        total += int(self.inventory)
        total += int(self.retries)
        total += int(self.coupon_count)
        total += int(self.on_sale)
        total += int(bool(self.vendor_id))
        total += int(bool(self.offer_id))
        total += int(bool(self.country_code))
        total += int(bool(self.city))
        total += int(bool(self.zip_code))
        total += int(bool(self.sku))
        total += int(bool(self.upc))
        total += int(bool(self.ean))
        total += int(bool(self.category))
        total += int(bool(self.brand))
        total += int(bool(self.region))
        total += int(bool(self.snapshot_id))
        total += int(bool(self.discount_code))
        total += int(self.discount_amount > 0)
        total += int(self.sale_price > 0)
        total += int(self.list_price > 0)
        total += int(self.shipping_fee > 0)
        total += int(self.tax_rate > 0)
        total += int(self.last_price > 0)
        total += int(self.highest_price > 0)
        total += int(self.lowest_price > 0)
        return total
