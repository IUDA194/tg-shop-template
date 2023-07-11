from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram import types, Dispatcher
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.types.input_file import InputFile
from aiogram.types.message import ContentType

from config import TOKEN, ADMINS_ID, PAYMENTS_PROVIDER_TOKEN
from db import database
from texts import texts

#Модель бота и клас диспетчер
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())
db = database()
texts = texts("usd")

#Клавиатуры
admin_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("Добавить товар", callback_data="add_product"),
    InlineKeyboardButton("Изменить товар", callback_data="edit_product"),
    InlineKeyboardButton("Удалить товар", callback_data="delete_product"),
    InlineKeyboardButton("Меню", callback_data="to_main"))

back_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Назад")
)

admin_back_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад", callback_data=f"admin"))

menu_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton("Меню", callback_data="menu")
)

main_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("Товары", callback_data="products_list"),
    #InlineKeyboardButton("Аккаунт", callback_data="akk"),
    InlineKeyboardButton("Про магазин (И другие доп кнопки)", callback_data="faq")
)

# FSM классы
class add_product(StatesGroup):
    name = State()
    price = State()
    photo = State()
    description = State()

class edit_product(StatesGroup):
    old_value = State()
    edit = State()
    new_value = State()

class delete_product(StatesGroup):
    name = State()

###################
##Клиентская часть##
###################


@dp.message_handler(commands=["start"])
async def start_command(message : types.Message):
    db_ansver = await db.insert_user(message.from_user.id)
    if db_ansver["status"]:
        await bot.send_message(message.from_user.id, """Привет!
            
<b>Главное меню</b>""", reply_markup=main_kb)
    else: await bot.send_message("Что-то пошло не так")
    await message.delete()

@dp.callback_query_handler(text="start")
async def callback_query_result(callback_query: types.CallbackQuery):
    db_ansver = await db.insert_user(callback_query.from_user.id)
    if db_ansver["status"]:
        await bot.send_message(callback_query.from_user.id, """Привет!
            
<b>Главное меню</b>""", reply_markup=main_kb)
    else: await bot.send_message("Что-то пошло не так")
    await callback_query.message.delete()

@dp.callback_query_handler(text="faq")
async def callback_query_result(callback_query: types.CallbackQuery):
    await callback_query.answer("Будет подставленно независимо от пользователя!", show_alert=True)

@dp.callback_query_handler(text="products_list")
async def callback_query_result(callback_query: types.CallbackQuery):
    products_list = await db.select_all_products()
    if products_list['status']:
        list_kb = InlineKeyboardMarkup()
        for i in products_list['result']:
            list_kb.add(InlineKeyboardButton(i[0], callback_data=f"open_product_cart_{i[0]}"))
        list_kb.add(InlineKeyboardButton("Назад", callback_data=f"start"))
        await callback_query.message.edit_text("Список товаров: ")
        await callback_query.message.edit_reply_markup(reply_markup=list_kb)

@dp.callback_query_handler(text_startswith="open_product_cart_")
async def photo_state(callback_query: types.CallbackQuery, state: FSMContext):
    product_name = callback_query.data[len("open_product_cart_"):]
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Оплатить", callback_data=f"buy_{product_name}"),
        InlineKeyboardButton("Назад", callback_data="products_list")
    )
    product = await db.select_product(product_name)
    if product['status']:
        await callback_query.message.edit_text(texts.gen_product_text(product['result']["name"],
                                                                      product["result"]['price'],
                                                                      product['result']['description']),
                                                                      reply_markup=kb)
    else: await callback_query.message(product["error"], reply_markup=main_kb)

@dp.callback_query_handler(text_startswith="buy_")
async def photo_state(callback_query: types.CallbackQuery, state: FSMContext):
    product_name = callback_query.data[len("buy_"):]
    product = await db.select_product(product_name)
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Оплатить", callback_data=f"pay_{product_name}"),
        InlineKeyboardButton("Назад", callback_data="products_list")
    )
    if product['status']:
        await callback_query.message.edit_text(texts.gen_buy_text(product['result']["name"],
                                                                  product["result"]['price']), 
                                                                  reply_markup=kb)
    else: await callback_query.message(product["error"], reply_markup=main_kb)

buys_list = {}

@dp.callback_query_handler(text_startswith="pay_")
async def photo_state(callback_query: types.CallbackQuery, state: FSMContext):
    global buys_list
    product_name = callback_query.data[len("pay_"):]
    buys_list[callback_query.from_user.id] = product_name
    product = await db.select_product(product_name)
    if product['status']:
        PRICE = types.LabeledPrice(label=f'Покупка {product["result"]["name"]} на сумму {product["result"]["price"]} {texts.currency}', amount=100*int(product["result"]["price"]))
        await bot.answer_callback_query(callback_query.id)
        await bot.send_invoice(callback_query.from_user.id,
                            title=f'Пополнение кошелька IM BOT',
                            description=f'Покупка на {product["result"]["price"]} {texts.currency}',
                            provider_token=PAYMENTS_PROVIDER_TOKEN,
                            currency='rub',
                            photo_height=512,  # !=0/None, иначе изображение не покажется
                            photo_width=512,
                            photo_size=512,
                            is_flexible=False,  # True если конечная цена зависит от способа доставки
                            prices=[PRICE],
                            start_parameter='time-machine-example',
                            payload='some-invoice-payload-for-our-internal-use'
                            )


@dp.pre_checkout_query_handler(lambda query: True)
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: types.Message):
    global buys_list
    product_name = buys_list[message.from_user.id]
    product = await db.select_product(product_name)
    if product['status']:
        product = product['result']
        for id in ADMINS_ID:
            await bot.send_message(id, texts.new_offer(product['name'],
                                                       product["price"], 
                                                       message.from_user.username,
                                                       message.from_user.id))
        await bot.send_message(message.from_user.id, "Ваш заказ оформлен, с вами свяжется менеджер", reply_markup=main_kb)
    else: await message.reply(product["error"], reply_markup=main_kb)

###################
##Админская часть##
###################

@dp.message_handler(commands=["admin"])
async def start_command(message : types.Message):
    for id in ADMINS_ID:
        if str(message.chat.id) == id:
            await bot.send_message(message.from_user.id, "Привет админ!", reply_markup=admin_kb)
            await message.delete()
            break

@dp.callback_query_handler(text="admin", state="*")
async def callback_query_result(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    for id in ADMINS_ID:
        if str(callback_query.from_user.id) == id:
            await bot.send_message(callback_query.from_user.id, "Привет админ!", reply_markup=admin_kb)
            break
@dp.callback_query_handler(text="add_product")
async def callback_query_result(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Введите название продукта(До 40-ка символов): ", reply_markup=back_kb)
    await add_product.name.set()

@dp.message_handler(state=add_product.name)
async def start_command(message : types.Message, state: FSMContext):
    if message.text.upper() != "НАЗАД":
        if len(message.text) <= 40:
            async with state.proxy() as data:
                data['name'] = message.text
            await bot.send_message(message.from_user.id, "Введите цену продукта: ", reply_markup=back_kb)
            await add_product.price.set()
        else:  await bot.send_message(message.from_user.id, "Введите название продукта(До 40-ка символов): ")
    else:
        await state.finish()
        await message.answer("Отмена", reply_markup=ReplyKeyboardRemove())
        await message.reply("Действие отменено", reply_markup=menu_kb)

@dp.message_handler(state=add_product.price)
async def start_command(message : types.Message, state: FSMContext):
    if message.text.upper() != "НАЗАД":
        try:
            async with state.proxy() as data:
                data['price'] = float(message.text)
            await bot.send_message(message.from_user.id, "Отправьте фото продукта: ", reply_markup=back_kb)
            await add_product.photo.set()
        except: await message.reply("Пожалуйста введите только число!", reply_markup=back_kb)
    else:
        await state.finish()
        await message.answer("Отмена", reply_markup=ReplyKeyboardRemove())
        await message.reply("Действие отменено", reply_markup=menu_kb)

@dp.message_handler(state=add_product.photo, content_types=ContentType.ANY)
async def start_command(message : types.Message, state: FSMContext):
        if message.content_type == ContentType.PHOTO:
            try:
                async with state.proxy() as data:
                    await message.photo[-1].download(f"media/{data['name']}.png")
                    data['photo_path'] = f"media/{data['name']}.png"
                await bot.send_message(message.from_user.id, "Введите описание продукта: ", reply_markup=back_kb)
                await add_product.description.set()
            except: 
                await state.finish()
                await message.answer("Отмена", reply_markup=ReplyKeyboardRemove())
                await message.reply("Что-то пошло не так(Возможно токое имя товара уже существует)!", reply_markup=menu_kb)
        elif message.content_type == ContentType.DOCUMENT:
            try:
                async with state.proxy() as data:
                    await message.document.download(f"media/{data['name']}.png")
                    data['photo_path'] = f"media/{data['name']}.png"
                await bot.send_message(message.from_user.id, "Введите описание продукта: ", reply_markup=back_kb)
                await add_product.description.set()
            except: 
                await state.finish()
                await message.reply("Что-то пошло не так(Возможно токое имя товара уже существует)!", reply_markup=menu_kb)
        elif message.content_type == ContentType.TEXT:
            if message.text.upper() != "НАЗАД":
                await bot.send_message(message.from_user.id, "Отправьте картинку, а не текст")
            else:
                await state.finish()
                await message.answer("Отмена", reply_markup=ReplyKeyboardRemove())
                await message.reply("Действие отменено", reply_markup=menu_kb)

        else: await message.reply("Пожалуйста отправьте только картинку!", reply_markup=back_kb)

@dp.message_handler(state=add_product.description)
async def start_command(message : types.Message, state: FSMContext):
    if message.text.upper() != "НАЗАД":
        async with state.proxy() as data:
            data['description'] = message.text
            result_of_insert = await db.insert_product(data['name'],
                                                       str(data['price']), 
                                                       data['photo_path'], 
                                                       data['description'])
            if result_of_insert['status']:
                await message.answer("Отмена", reply_markup=ReplyKeyboardRemove())
                await bot.send_message(message.from_user.id, 
                                       f"Товар {data['name']} успешно добавлен с ценой {data['price']}", 
                                       reply_markup=admin_kb)
            else:
                await bot.send_message(message.from_user.id, result_of_insert['error'], reply_markup=admin_kb)
        await state.finish()
    else:
        await state.finish()
        await message.reply("Действие отменено", reply_markup=menu_kb)

@dp.callback_query_handler(text="edit_product")
async def callback_query_result(callback_query: types.CallbackQuery):
    products_list = await db.select_all_products()
    if products_list['status']:
        product_kb = InlineKeyboardMarkup()
        for i in products_list['result']:
            product_kb.add(InlineKeyboardButton(i[0], callback_data=f"{i[0]}"))
        product_kb.add(InlineKeyboardButton("Назад", callback_data=f"admin"))

        await bot.send_message(callback_query.from_user.id, "Выберете продукт для редактирования:", reply_markup=product_kb)
        await edit_product.old_value.set()
    else: await bot.send_message(callback_query.from_user.id, products_list['error'])

@dp.message_handler(state=edit_product.old_value, content_types=ContentType.ANY)
async def start_command(message : types.Message, state: FSMContext):
    await message.delete()
    await bot.send_message(message.from_user.id, "<b>Пожалуйста нажмите на кнопки выше!</b>")

@dp.callback_query_handler(state=edit_product.old_value)
async def callback_query_result(callback_query: types.CallbackQuery, state: FSMContext):
    if db.products_rows:
        async with state.proxy() as data:
            data['old_value'] = callback_query.data
        do_kb = InlineKeyboardMarkup()
        for row in db.products_rows:
            do_kb.add(InlineKeyboardButton(row, callback_data=db.products_rows[row]))
        do_kb.add(InlineKeyboardButton("Назад", callback_data=f"admin"))
        await bot.send_message(callback_query.from_user.id, "Выберете поле для редактирования: ", reply_markup=do_kb)
        await edit_product.edit.set()
    else: 
        await bot.send_message(callback_query.from_user.id, "Произошла ошибка попробуйте позже")
        await state.finish()

@dp.message_handler(state=edit_product.edit, content_types=ContentType.ANY)
async def start_command(message : types.Message, state: FSMContext):
    await message.delete()
    await bot.send_message(message.from_user.id, "<b>Пожалуйста нажмите на кнопки выше!</b>")

@dp.callback_query_handler(state=edit_product.edit)
async def callback_query_result(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data:
        async with state.proxy() as data:
            data['edit'] = callback_query.data
            await bot.send_message(callback_query.from_user.id, f"Введите новое значение поля {data['edit']}: ", reply_markup=admin_back_kb)
        await edit_product.new_value.set()
    else: 
        await bot.send_message(callback_query.from_user.id, "Пожалуйста введите новое значение сообщением!")

@dp.message_handler(state=edit_product.new_value, content_types=ContentType.ANY)
async def start_command(message : types.Message, state: FSMContext):
    if message.content_type == ContentType.TEXT:
        async with state.proxy() as data:
            data['new_value'] = message.text
            result = await db.edit_product(data["edit"], data['old_value'], data['new_value'])
            if result['status']: await bot.send_message(message.from_user.id, f"Поле {data['edit']} товара {data['old_value']} успешно заменено на {data['new_value']}", reply_markup=admin_back_kb)
            else: await bot.send_message(message.from_user.id, result['error'])
        await state.finish()
    else: 
        await bot.send_message(message.from_user.id, "Пожалуйста введите новое значение сообщением!")

@dp.callback_query_handler(state=edit_product.edit)
async def callback_query_result(callback_query: types.CallbackQuery, state: FSMContext):
    callback_query.answer("Пожалуйста введите новое значение сообщением!", show_alert=True)

@dp.callback_query_handler(text="delete_product")
async def callback_query_result(callback_query: types.CallbackQuery):
    products_list = await db.select_all_products()
    if products_list['status']:
        product_kb = InlineKeyboardMarkup()
        for i in products_list['result']:
            product_kb.add(InlineKeyboardButton(i[0], callback_data=f"{i[0]}"))
        product_kb.add(InlineKeyboardButton("Назад", callback_data=f"admin"))

        await bot.send_message(callback_query.from_user.id, "Выберете продукт для удаления:", reply_markup=product_kb)
        await delete_product.name.set()
    else: await bot.send_message(callback_query.from_user.id, products_list['error'])

@dp.callback_query_handler(state=delete_product.name)
async def callback_query_result(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data:
        result = await db.dalete_product(callback_query.data)
        if result['status']:
            await bot.send_message(callback_query.from_user.id, f"Продукт {callback_query.data} успешно удалён", reply_markup=admin_back_kb)
            await state.finish()
        else:
            await bot.send_message(callback_query.from_user.id, result['error'])
            await state.finish()
    else: 
        await bot.send_message(callback_query.from_user.id, "Произошла ошибка попробуйте позже")
        await state.finish()

@dp.message_handler(state=edit_product.edit, content_types=ContentType.ANY)
async def start_command(message : types.Message, state: FSMContext):
    await message.delete()
    await bot.send_message(message.from_user.id, "<b>Пожалуйста нажмите на кнопки выше!</b>")

#Функция которая запускается со стартом бота
async def on_startup(_):
    await db.connect_to_db()
    print('bot online')
#Пулинг бота
executor.start_polling(dp,skip_updates=True, on_startup=on_startup) #Пуллинг бота

#Вывод уведомления про отключение бота
print("Bot offline")