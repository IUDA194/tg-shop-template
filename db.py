import aiosqlite as sql


class database:
    def __init__(self) -> None:
        self.db = None
        self.cur = None
        self.products_rows = {
            "Имя" : "name",
            "Цена" : "price",
            "Фото" : "photo_path",
            "Описание" : "description"
        }

    async def connect_to_db(self):
        self.db = await sql.connect('mydatabase.db')
        self.cur = await self.db.cursor()
        await self.cur.execute("""CREATE TABLE if not exists users (
                    chatid TEXT,
                    balance TEXT,
                    cart TEXT
                    )""")
        await self.cur.execute("""CREATE TABLE if not exists products (
                    name TEXT,
                    price TEXT,
                    photo_path TEXT,
                    description TEXT
                    )""")
        await self.cur.execute("""CREATE TABLE if not exists products_view (
                    name TEXT,
                    chat_id TEXT,
                    view TEXT
                    )""")
        await self.db.commit()

    async def insert_user(self, user_id : str = None):
        if user_id != None:
            await self.cur.execute(""" SELECT * FROM users WHERE chatid = ? """, (user_id,))
            result = await self.cur.fetchall()
            if len(result) < 1:
                await self.cur.execute(""" INSERT INTO users ("chatid", "balance", "cart") VALUES (?,?,?) """, (user_id,"0", ";"))
            await self.db.commit()
            return {"status" : True}
        else: return {"status" : False}

    async def select_user(self, user_id : str = None):
        if user_id != None:
            await self.cur.execute(""" SELECT * FROM users WHERE chatid = ?""", (user_id,))
            result = await self.cur.fetchall()
            if len(result) >= 1:
                result = {"user_id" : result[0][0],
                          "balance" : float(result[0][1]), 
                          "cart" : result[0][2]}
                return {"status" : True, "result" : result}
            else: 
                await self.cur.execute(""" INSERT INTO users ("chatid", "balance", "cart") VALUES (?,?,?) """, (user_id,"0", ";"))
                await self.db.commit()
                result = {"user_id" : user_id,
                          "balance" : 0, 
                          "cart" : ";"}
                return {"status" : True, "result" : result}
        else: return {"status" : False, "error" : "Произошла ошибка попробуйте позже"}

    async def add_to_cart(self, user_id : str = None, product : str = None):
        if user_id != None and product != None:
            pass

    async def insert_product(self, name : str = None, price : float = None, photo_path : str = None, description : str = None):
        if name != None:
            await self.cur.execute(""" SELECT * FROM products WHERE name = ? """, (name,))
            result = await self.cur.fetchall()
            if len(result) < 1:
                if name and price and photo_path and description: await self.cur.execute(""" INSERT INTO products ("name", "price", "photo_path", "description") VALUES (?,?,?,?) """, (name, price, photo_path, description))
                else: return  {"status" : False, "error" : "Произошла ошибка, попробуйте снова"}
            else: return  {"status" : False, "error" : "Товар с таким именем уже существует"}
            await self.db.commit()
            return {"status" : True}
        else: return {"status" : False, "error" : "Произошла ошибка, попробуйте снова"}
    
    async def select_all_products(self):
        await self.cur.execute(""" SELECT * FROM products """)
        result = await self.cur.fetchall()
        return {"status" : True, "result" : result}

    async def select_product(self, name : str = None):
        if name != None:
            await self.cur.execute(""" SELECT * FROM products WHERE name = ?""", (name,))
            result = await self.cur.fetchall()
            if len(result) >= 1:
                result = {"name" : result[0][0],
                          "price" : result[0][1], 
                          "photo_path" : result[0][2], 
                          "description" : result[0][3]}
                return {"status" : True, "result" : result}
            else: return {"status" : False, "error" : "Товара с тиким именем не существует, напишите /start для получения актуального списка"}
        else: return {"status" : False, "error" : "Произошла ошибка попробуйте позже"}

    async def edit_product(self, edit : str = None, old_value : str = None, new_value : str = None):
        if edit and new_value and old_value:
            await self.cur.execute(""" SELECT * FROM products WHERE name = ? """, (old_value,))
            exist = await self.cur.fetchall()
            print(exist)
            if len(exist) >= 1:
                try: await self.cur.execute(f""" UPDATE products SET {edit} = ? WHERE name = ? """, (new_value, old_value))
                except : return {"status" : False, "error" : "Произошла ошибка попробуйте позже"}
                await self.db.commit()
                return {"status" : True}
            else: return {"status" : False, "error" : "Продукта с таким именем не существует"}
        else: return {"status" : False, "error" : "Произошла ошибка попробуйте позже"}

    async def dalete_product(self, name : str = None):
        if name:
            await self.cur.execute(""" SELECT * FROM products WHERE name = ? """, (name,))
            exist = await self.cur.fetchall()
            print(exist)
            if len(exist) >= 1:
                try: await self.cur.execute(f""" DELETE FROM products WHERE name = ? """, (name,))
                except : return {"status" : False, "error" : "Произошла ошибка попробуйте позже"}
                await self.db.commit()
                return {"status" : True}
            else: return {"status" : False, "error" : "Продукта с таким именем не существует"}
        else: return {"status" : False, "error" : "Произошла ошибка попробуйте позже"}