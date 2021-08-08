import telebot
from telebot.types import KeyboardButton, User

from time import sleep
from logger import Logger
import os

import formatter
from database import Database
from markup import Markup

class Bot():
    
    def __init__(self):
        
        token = ""
        while True:
            try:
                with open('token.txt', 'r') as f:
                    token = f.read()
            except:
                with open('token.txt', 'w') as f:
                    token = input("Enter your bot's token:\n")
                    f.write(token)
            break
        
        db = Database
        db._change("""
                CREATE TABLE IF NOT EXISTS holders (
                    username text NOT NULL UNIQUE,
                    id integer NOT NULL UNIQUE,
                    role text,
                    props integer
                )
                """)
        db._change("""
                CREATE TABLE IF NOT EXISTS props (
                    category text NOT NULL,
                    name text NOT NULL UNIQUE,
                    photo TEXT UNIQUE,
                    holder text
                )
                """)
        
        if not db.has_admins():
            while True:
                try:
                    with open('admin.txt', 'r') as f:
                        admin_id = int(f.read())
                        db._change("DELETE FROM holders WHERE id=?", (admin_id,))
                        db._change("INSERT INTO holders VALUES(?,?,?,?)", ("empty", admin_id, "admin", 0))
                except:
                    with open('admin.txt', 'w') as f:
                        admin = input("Enter the first admin's ID:\n")
                        f.write(admin)
                        continue
                break
        
        log = Logger()
        
        telebot.apihelper.ENABLE_MIDDLEWARE = True
        tb = telebot.TeleBot(token)
        tb.gateway = None


        class Communicator():
            @staticmethod
            def send_prop(msg, prop):
                message = None
                if prop[2]:
                    message = tb.send_photo(msg.from_user.id, prop[2], formatter.prop(prop), reply_markup=Markup.Prop.viewer(msg, prop), parse_mode="HTML")
                else:
                    message = tb.send_message(msg.from_user.id, formatter.prop(prop), reply_markup=Markup.Prop.viewer(msg, prop), parse_mode="HTML")
                return message
            def notify_keepers(msg, text):
                keepers = db.User.get_keepers_ids()
                for keeper_id in keepers:
                    if keeper_id != msg.from_user.id:
                        tb.send_message(keeper_id, text, parse_mode="MARKDOWN")  
        
            
        # Checking the user
        @tb.middleware_handler(update_types=['message'])
        def check_user(bot_instance, msg):
            
            #Return user's id and role if exists in the db
            username = db.User.get_username_by_id(msg.from_user.id)
            
            #Check if the username is in the db
            if not username:
                if not tb.gateway:
                    tb.send_message(msg.from_user.id, "Доступ закрыт. Обратитесь к администратору.")
                    msg.text = "deny_access"
                else:
                    Users.Add.join(msg)
            else: 
                #Update the db entry if the user has changed his/her username
                if msg.from_user.username != username:
                    db.User.update_username(msg.from_user.id, msg.from_user.username)
                    tb.send_message(msg.from_user.id, "Ваш новый юзернейм @{} добавлен в базу данных".format(msg.from_user.username))
                #Force lowercase for any text message
                try:
                    msg.text = msg.text.lower()
                except: pass

        class Menu():
            # Open menu if no command found
            @tb.message_handler(func=lambda msg: msg.text != "deny_access")
            
            def menu(msg):
                msg = tb.send_message(msg.from_user.id, "Главное Меню", reply_markup=Markup.main(msg))
                tb.register_next_step_handler(msg, Menu.choose, msg)

            @staticmethod
            
            def choose(msg, me):
                if msg.text == "реквизит":
                    categories = db.Prop.get_categories()
                    msg = tb.send_message(msg.from_user.id, formatter.categories(categories), reply_markup=Markup.addorback(msg), parse_mode="HTML")
                    tb.register_next_step_handler(msg, Categories.choose, categories)
                elif msg.text == "пользователи":
                    msg = tb.send_message(msg.from_user.id, db.User.get_pretty_user_list(), reply_markup=Markup.Users.menu(msg), parse_mode="HTML")
                    tb.register_next_step_handler(msg, Users.choose)
                elif msg.text == "лог" and db.User.is_keeper(msg.from_user.username):
                    msg = tb.send_message(msg.from_user.id, "Выберите тип Лога", reply_markup=Markup.log())
                    tb.register_next_step_handler(msg, Log.choose)
                else:
                    tb.register_next_step_handler(msg, Menu.choose)
        
        class Log():
            @classmethod
            def choose(cls, msg):
                if msg.text == "назад":
                    Menu.menu(msg)
                else:
                    string = "Такого Лога не существует"
                    if msg.text == "общий": string = log.get()
                    elif msg.text == "админ": string = log.get("USER")
                    elif msg.text == "передачи": string = log.get("PROP")
                    elif msg.text == "реквизит": string = log.get("EDIT")
                    
                    msg = tb.send_message(msg.from_user.id, string)
                    tb.register_next_step_handler(msg, cls.choose)
                    

        class Users():
            
            @classmethod
            
            def choose(cls, msg):
                if msg.text == "назад":
                    msg = tb.send_message(msg.from_user.id, "Возврат в меню", reply_markup=Markup.main(msg))
                    tb.register_next_step_handler(msg, Menu.choose)
                elif msg.text == "добавить пользователя" and db.User.is_admin(msg.from_user.username):
                    if tb.gateway:
                        msg = tb.send_message(msg.from_user.id, "Шлюз уже открыт @" + db.User.get_username_by_id(tb.gateway), reply_markup=Markup.Users.menu(msg))
                        tb.register_next_step_handler(msg, cls.choose)
                    else:
                        tb.gateway = msg.from_user.id
                        msg = tb.send_message(msg.from_user.id, "Чтобы добавить пользователя напишите боту с его аккаунта", reply_markup=Markup.cancel())
                        tb.register_next_step_handler(msg, cls.Add.cancel)
                else:
                    try:
                        if msg.text[0] in ['@', '/']: msg.text = msg.text[1:]
                        user_info = db.User.get_entry_by_username(msg.text)
                        if user_info == None: raise Exception("NoUserFound")
                        cls.Menu.choose(msg, user_info)
                    except:
                        tb.register_next_step_handler(msg, cls.choose)
            
            class Add():
                @classmethod
                
                def cancel(cls, msg):
                    if tb.gateway:
                        tb.gateway = None
                        msg = tb.send_message(msg.from_user.id, db.User.get_pretty_user_list(), reply_markup=Markup.Users.menu(msg), parse_mode="HTML")
                        tb.register_next_step_handler(msg, Users.choose)
                
                @classmethod
                
                def join(cls, msg):
                    db.User.add(msg)
                    Menu.menu(msg)
                    
                    msg = tb.send_message(tb.gateway, "Пользователь /{} получил доступ".format(msg.from_user.username), reply_markup=Markup.Users.menu(msg))
                    tb.register_next_step_handler(msg, Users.choose)
                    log.user("@" + db.User.get_username_by_id(tb.gateway) + " открыл доступ для @" + msg.from_user.username)
                    tb.gateway = None

        
            class Menu():
                @classmethod
                
                def choose(cls, msg, user_info):
                    # Strip off the @ sign from the username
                    if user_info:
                        string = "@{} – ".format(user_info[0])
                        if user_info[2] == "user": string += "Пользователь"
                        elif user_info[2] == "keeper": string += "Хранитель"
                        elif user_info[2] == "admin": string += "Админинстратор"
                        
                        
                        props = db.Prop.get_user(user_info[0])
                        if user_info[3]: 
                            string += formatter.user_props(props)
                        
                        msg = tb.send_message(msg.from_user.id, string, reply_markup=Markup.Users.viewer(msg, user_info), parse_mode="HTML")
                        tb.register_next_step_handler(msg, cls.Options.choose, user_info, props)
                    else:
                        msg = tb.send_message(msg.from_user.id, "Никнейм не найден в базе данных")
                        tb.register_next_step_handler(msg, cls.choose)
                
                class Options():
                    @classmethod
                    
                    def choose(cls, msg, user_info, props):
                        role = user_info[2]
                        if msg.text == "кикнуть" and role == "user":
                            msg = tb.send_message(msg.from_user.id, "Вы уверены, что хотите кикнуть пользователя @{}?".format(user_info[0]), reply_markup=Markup.yesorno())
                            tb.register_next_step_handler(msg, cls.kick, user_info, props)
                        elif msg.text == "назад":
                            msg = tb.send_message(msg.from_user.id, db.User.get_pretty_user_list(), reply_markup=Markup.Users.menu(msg), parse_mode="HTML")
                            tb.register_next_step_handler(msg, Users.choose)
                        elif msg.text == "повысить" and role in ["user", "keeper"]:
                            cls.promote(msg, user_info, props)
                        elif msg.text == "понизить" and role in ["keeper", "admin"]:
                            cls.demote(msg, user_info, props)
                        elif msg.text[3:].isdigit():
                            Categories.Props.choose(msg, props)
                        else:
                            tb.register_next_step_handler(msg, cls.choose, user_info, props)

                    @classmethod
                    
                    def kick(cls, msg, user_info, props):
                        if msg.text == "да":
                            db.User.kick(user_info[0])
                            log.user("@" + msg.from_user.username + " кикнул @" + user_info[0])
                            tb.send_message(user_info[1], "@{} удалил вас из базы данных".format(msg.from_user.username))
                            msg = tb.send_message(msg.from_user.id, "Пользователь @{} удалён из базы данных".format(user_info[0]), reply_markup=Markup.Users.menu(msg))
                            tb.register_next_step_handler(msg, Users.choose)
                        else:
                            msg = tb.send_message(msg.from_user.id, "Возврат в меню пользователя", reply_markup=Markup.Users.viewer(msg, user_info))
                            tb.register_next_step_handler(msg, cls.choose, user_info, props)
                        
                    @classmethod
                    
                    def promote(cls, msg, user_info, props):
                        promotion = db.User.promote(user_info)
                        promotion = "хранителя" if promotion == "keeper" else "админинстратора"
                        log.user("@" + msg.from_user.username + " повысил @" + user_info[0] + " до уровня " + promotion)
                        user_info = db.User.get_entry_by_username(user_info[0])
                        tb.send_message(msg.from_user.id, "@{} повышен до уровня {}".format(user_info[0], promotion), reply_markup=Markup.Users.viewer(msg, user_info))
                        tb.send_message(user_info[1], "@{} повысил вас до уровня {}".format(msg.from_user.username, promotion))
                        tb.register_next_step_handler(msg, cls.choose, user_info, props)

                    @classmethod
                    
                    def demote(cls, msg, user_info, props):
                        demotion = db.User.demote(user_info)
                        demotion = "пользователя" if demotion == "user" else "хранителя"
                        log.user("@" + msg.from_user.username + " понизил @" + user_info[0] + " до уровня " + demotion)
                        user_info = db.User.get_entry_by_username(user_info[0])
                        tb.send_message(msg.from_user.id, "@{} понижен до уровня {}".format(user_info[0], demotion), reply_markup=Markup.Users.viewer(msg, user_info))
                        tb.send_message(user_info[1], "@{} понизил вас до уровня {}".format(msg.from_user.username, demotion))
                        tb.register_next_step_handler(msg, cls.choose, user_info, props)
                    
        class Categories():
            @classmethod
            
            def choose(cls, msg, categories):
                if msg.text[3:].isdigit():
                    cat_id = int(msg.text[3:])
                    category = categories[cat_id]
                    props = db.Prop.get_all(category)
                    msg = tb.send_message(msg.from_user.id, formatter.props(props), reply_markup=Markup.addorback(msg), parse_mode="HTML")
                    tb.register_next_step_handler(msg, cls.Props.choose, props)
                elif msg.text == "назад":
                    msg = tb.send_message(msg.from_user.id, "Возврат в меню", reply_markup=Markup.main(msg))
                    tb.register_next_step_handler(msg, Menu.choose)
                elif msg.text == "добавить" and db.User.is_keeper(msg.from_user.username):
                    msg = tb.send_message(msg.from_user.id, "Введите название\n" + formatter.categories(categories), reply_markup=Markup.back(), parse_mode="HTML")
                    tb.register_next_step_handler(msg, cls.Add.choose_category, categories)
                else:
                    msg = tb.send_message(msg.from_user.id, "Невернй ID категории")
                    tb.register_next_step_handler(msg, cls.choose, db.Prop.get_categories())

            class Add():
                @classmethod
                
                def choose_category(cls, msg, categories):
                    category = msg.text
                    if msg.text[3:].isdigit():
                        category = categories[int(msg.text[3:])]
                    
                    if msg.text != "назад":
                        message = tb.send_message(msg.from_user.id, "Введите название реквизита", reply_markup=Markup.cancel())
                        tb.register_next_step_handler(message, cls.choose_name, category)
                    else:
                        msg = tb.send_message(msg.from_user.id, formatter.categories(categories), reply_markup=Markup.addorback(msg), parse_mode="HTML")
                        tb.register_next_step_handler(msg, Categories.choose, categories)
                
                @classmethod
                
                def choose_name(cls, msg, category):
                    if msg.text != "отмена":
                        name = msg.text 
                        prop = (category, name, None, None)
                        db.Prop.add(*prop)
                        log.edit("@{} добавил [{}]|{}".format(msg.from_user.username, category, name))
                        msg = Communicator.send_prop(msg, prop)
                        tb.register_next_step_handler(msg, Categories.Props.view, prop)
                    else:
                        props = db.Prop.get_all(category)
                        if props == []:
                            categories = db.Prop.get_categories()
                            msg = tb.send_message(msg.from_user.id, formatter.categories(categories), reply_markup=Markup.addorback(msg), parse_mode="HTML")
                            tb.register_next_step_handler(msg, Categories.choose, db.Prop.get_categories())
                        else:
                            msg = tb.send_message(msg.from_user.id, formatter.props(props), reply_markup=Markup.addorback(msg), parse_mode="HTML")
                            tb.register_next_step_handler(msg, Categories.Props.choose, props)
                            
                    
                        


            class Props():
                @classmethod
                
                def choose(cls, msg, props):
                    if msg.text[3:].isdigit():
                        prop_id = int(msg.text[3:])
                        prop = db.Prop.get(props[prop_id][1])
                        message = Communicator.send_prop(msg, prop)
                        tb.register_next_step_handler(message, cls.view, prop)
                    elif msg.text == "назад":
                        categories = db.Prop.get_categories()
                        msg = tb.send_message(msg.from_user.id, formatter.categories(categories), reply_markup=Markup.addorback(msg), parse_mode="HTML")
                        tb.register_next_step_handler(msg, Categories.choose, categories)
                    elif msg.text == "добавить" and db.User.is_keeper(msg.from_user.username):
                        msg = tb.send_message(msg.from_user.id, "Введите название реквизиты", reply_markup=Markup.cancel())
                        tb.register_next_step_handler(msg, Categories.Add.choose_name, props[0][0])
                    else:
                        user = db.User.get_entry_by_username(msg.text[1:])
                        if user:
                            Users.Menu.choose(msg, user)
                        else:
                            msg = tb.send_message(msg.from_user.id, "Неверный ID реквизита")
                            tb.register_next_step_handler(msg, cls.choose, props)

                @classmethod
                
                def view(cls, msg, prop):
                    if msg.text == "назад":
                        props = db.Prop.get_all(prop[0])
                        msg = tb.send_message(msg.from_user.id, formatter.props(props), reply_markup=Markup.addorback(msg), parse_mode="HTML")
                        tb.register_next_step_handler(msg, cls.choose, props)
                    elif msg.text == "забрать" and not prop[3]:
                        cls.take(msg, prop)
                    elif msg.text == "вернуть" and (prop[3] == msg.from_user.username or db.User.is_keeper(msg.from_user.username)):
                        cls.turn(msg, prop)
                    elif msg.text == "удалить" and db.User.is_keeper(msg.from_user.username):
                        msg = tb.send_message(msg.from_user.id, "Вы уверены?", reply_markup=Markup.yesorno())
                        tb.register_next_step_handler(msg, cls.delete, prop)
                    elif msg.text == "фото" and db.User.is_keeper(msg.from_user.username):
                        msg = tb.send_message(msg.from_user.id, "Пришлите фото для этого реквизита", reply_markup=Markup.cancel())
                        tb.register_next_step_handler(msg, cls.photo, prop)
                    else: 
                        user = db.User.get_entry_by_username(msg.text[1:])
                        if user:
                            Users.Menu.choose(msg, user)
                        else:
                            msg = tb.send_message(msg.from_user.id, "Ошибка")
                            tb.register_next_step_handler(msg, cls.view, db.Prop.get(prop[1]))


                @classmethod
                
                def take(cls, msg, prop):
                    db.Prop.chown(prop[1], msg.from_user.username)
                    log.prop("@{} забрал [{}]|{}".format(msg.from_user.username, prop[0], prop[1]))
                    db.User.increment(msg.from_user.username)
                    Communicator.notify_keepers(msg, "@{} забрал _[{}]_*{}*".format(msg.from_user.username, prop[0], prop[1]))
                    prop = db.Prop.get(prop[1])  
                    msg = Communicator.send_prop(msg, prop)
                    tb.register_next_step_handler(msg, cls.view, prop)
                
                @classmethod
                
                def turn(cls, msg, prop):
                    log.prop("@{} вернул [{}]|{}".format(prop[3], prop[0], prop[1]))
                    db.User.decrement(prop[3])
                    db.Prop.chown(prop[1], None)
                    Communicator.notify_keepers(msg, "@{} вернул _[{}]_*{}*".format(prop[3], prop[0], prop[1]))
                    prop = db.Prop.get(prop[1])
                    msg = Communicator.send_prop(msg, prop)
                    tb.register_next_step_handler(msg, cls.view, prop)

                @classmethod
                
                def delete(cls, msg, prop):
                    if msg.text == "да":
                        db.Prop.delete(prop[1])
                        log.edit("@{} удалил [{}]|{}".format(msg.from_user.username, prop[0], prop[1]))
                        props = db.Prop.get_all(prop[0])
                        if props != []:
                            msg = tb.send_message(msg.from_user.id, formatter.props(props), reply_markup=Markup.addorback(msg), parse_mode="HTML")
                            tb.register_next_step_handler(msg, Categories.Props.choose, props)
                        else:
                            categories = db.Prop.get_categories()
                            msg = tb.send_message(msg.from_user.id, formatter.categories(categories), reply_markup=Markup.addorback(msg), parse_mode="HTML")
                            tb.register_next_step_handler(msg, Categories.choose, categories)
                    else:
                        msg = Communicator.send_prop(msg, prop)
                        tb.register_next_step_handler(msg, cls.view, prop)
                        
                @classmethod
                
                def photo(cls, msg, prop):
                    try:
                        if msg.text != "отмена":
                            file_id = msg.photo[-1].file_id
                            db.Prop.chpic(prop[1], file_id)
                            log.edit("@{} изменил фотографию [{}]|{}".format(msg.from_user.username, prop[0], prop[1]))
                    
                        prop = db.Prop.get(prop[1])
                        msg = Communicator.send_prop(msg, prop)
                        tb.register_next_step_handler(msg, cls.view, prop)
                    except:
                        msg = tb.send_message(msg.from_user.id, "Ошибка", reply_markup=Markup.cancel())
                        tb.register_next_step_handler(msg, cls.photo, prop)
                
                
                
                    
                        
        while True:
            exception_count = 0
            try:
                print("[TB] Начало работы")
                tb.polling(none_stop=True)
            except:
                exception_count += 1
                print("Ошибка: " + str(exception_count))
                sleep(5)
                continue
            break
        print("[TB] Завершение работы")

if __name__ == "__main__": Bot()