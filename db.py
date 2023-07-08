import aiosqlite as sql

async def connect_to_db():
    db = await sql.connect('mydatabase.db')
    cur = await db.cursor()
    await cur.execute("""CREATE TABLE if not exists users (
                chatid TEXT
                )""")
    await db.commit()



class database:
    def __init__(self) -> None:
        self.db = None
        self.cur = None

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

    async def insert_product(self, name : str = None, price : float = None, photo_path : str = None, description : str = None):
        if name != None:
            await self.cur.execute(""" SELECT * FROM products WHERE name = ? """, (name,))
            result = await self.cur.fetchall()
            if len(result) < 1:
                if name and price and photo_path and description: await self.cur.execute(""" INSERT INTO products ("name", "price", "photo_path", "description", "views") VALUES (?,?,?,?,?) """, (name, price, photo_path, description, ";"))
                else: return  {"status" : False, "error" : "Произошла ошибка, попробуйте снова"}
            else: return  {"status" : False, "error" : "Товар с таким именем уже существует"}
            await self.db.commit()
            return {"status" : True}
        else: return {"status" : False, "error" : "Произошла ошибка, попробуйте снова"}

