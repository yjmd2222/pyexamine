from datetime import date


def categorize_income(amount: float,
                      currency: str,
                      source: str,
                      received_at: date,
                      description: str,
                      category_code: str):
    label = "income"
    if source.lower() == "salary":
        label = "salary"
    return {
        "amount": amount,
        "currency": currency,
        "source": source,
        "received_at": received_at,
        "description": description,
        "category_code": category_code,
        "label": label,
    }


def categorize_expense(amount: float,
                       currency: str,
                       source: str,
                       received_at: date,
                       description: str,
                       category_code: str):
    label = "expense"
    if source.lower() in {"coffee", "snack"}:
        label = "food"
    return {
        "amount": amount,
        "currency": currency,
        "source": source,
        "received_at": received_at,
        "description": description,
        "category_code": category_code,
        "label": label,
    }
