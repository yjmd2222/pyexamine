from datetime import date

def add_transaction(user_id: int,
                    account_id: int,
                    amount: float,
                    currency: str,
                    category_id: int,
                    merchant: str,
                    note: str,
                    is_recurring: bool,
                    year: int,
                    month: int,
                    day: int):
    transaction_date = date(year, month, day)
    return {
        "user_id": user_id,
        "account_id": account_id,
        "amount": amount,
        "currency": currency,
        "category_id": category_id,
        "merchant": merchant,
        "note": note,
        "is_recurring": is_recurring,
        "date": transaction_date,
    }
