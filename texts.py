class texts:
    currency = None
    def __init__(self, currency : str = "usd") -> None:
        self.currency = currency
    def gen_product_text(self, name : str = False, price : str = False, description : str = False):
        if name and price and description:
            return f"""<b>{name}</b>

{description}

Цена: <code>{price} {self.currency}</code>"""

    def gen_buy_text(self, name : str = False, price : str = False):
        if name and price:
            return f"""Покупка {name} 
                                        
К оплате {price} {self.currency}"""

    def new_offer(self, name : str = False, price : str = False, user_name : str = False, user_id : str = False):
        if name and price and user_name and user_id:
            return f"""Пользователь {user_name} с айди {user_id}

переобрёл {name} на сумму {price}"""