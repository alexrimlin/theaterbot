import telebot

from time import sleep

from logger import Logger

import formatter
from database import Database
from markup import Inline, Reply


        
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
            username text NOT NULL,
            id integer NOT NULL UNIQUE,
            role text,
            props integer
        )
        """)
db._change("""
        CREATE TABLE IF NOT EXISTS props (
            category integer NOT NULL,
            name text NOT NULL,
            photo TEXT,
            holder text,
            UNIQUE(category, name)
        )
        """)
db._change("""
           CREATE TABLE IF NOT EXISTS categories (
               name text UNIQUE,
               amount integer
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
        
telebot.apihelper.ENABLE_MIDDLEWARE = True
tb = telebot.TeleBot(token)    

log = Logger()

class Shortcut():
    
    @staticmethod
    def overwrite(call, string, markup):
        return tb.edit_message_text(string, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

    @classmethod
    def overwrite_prop(cls, prop, call, string, markup):
        
        if not prop[2]:
            return cls.overwrite(call, string, markup)
        else:
            cls.purge_call(call)
            return tb.send_message(call.message.chat.id, string, reply_markup=markup, parse_mode="HTML")

    @staticmethod
    def purge_call(call):
        tb.delete_message(call.message.chat.id, call.message.message_id)
        
    @staticmethod
    def purge_messages(msg):
        try:
            for message_id in range(msg.message_id, 0, -1):
                tb.delete_message(msg.chat.id, message_id)
        except: pass

class Next_Step():
    
    @staticmethod
    def add_photo(msg, prop):
        try:
            
            file_id = msg.photo[-1].file_id
            db.Prop.chpic(prop[1], file_id)
            log.edit("@{} изменил фотографию [{}]|{}".format(msg.from_user.username, db.Prop.get_category_name(prop[0]), prop[1]))
        
            prop = db.Prop.get(prop[0], prop[4])
            tb.send_photo(msg.chat.id, prop[2], formatter.prop(prop), parse_mode="HTML", reply_markup=Inline.prop_viewer(msg, prop))
            Shortcut.purge_messages(msg)
        except:
            tb.send_message(msg.from_user.id, "Ошибка")
            
    @classmethod
    def add_category(cls, msg):
        
        if msg.text != "отмена":
            category = msg.text
            
            tb.send_message(msg.from_user.id, "Введите название реквизита", reply_markup=Reply.add_prop())
            tb.register_next_step_handler(msg, cls.add_name, category)
            
        else:
            tb.send_message(msg.from_user.id, formatter.title("Категории"), reply_markup=Inline.categories_list(msg), parse_mode="HTML")
            Shortcut.purge_messages(msg)

    @classmethod
    def add_name(cls, msg, category):
        
        if msg.text != "отмена":
            name = msg.text 
            prop = [category, name, None, None]
            db.Prop.add(*prop)
            prop = db.Prop.get_by_name(category, name)
            log.edit("@{} добавил [{}]|{}".format(msg.from_user.username, category, name))
            tb.send_message(msg.from_user.id, formatter.prop(db.Prop.get(prop[0], prop[4])), 
                            reply_markup=Inline.prop_viewer(msg, prop), parse_mode="HTML")
        else:
            props = db.Prop.get_all(category)
            if props == []:
                tb.send_message(msg.from_user.id, formatter.title("Категории"), reply_markup=Inline.categories_list(msg), parse_mode="HTML")
            else:
                tb.send_message(msg.from_user.id, formatter.title(db.Prop.get_category_name(category)), 
                                reply_markup=Inline.category_viewer(msg, db.Prop.get_category_id(category)), parse_mode="HTML")
            
        Shortcut.purge_messages(msg)
class Bot():
    
    def __init__(self):
        tb.gateway = None  
            
        # Checking the user
        @tb.middleware_handler(update_types=['message'])
        def check_user(bot_instance, msg):
            
            #Return user's id and role if exists in the db
            username = db.User.get_username_by_id(msg.from_user.id)
            
            #Check if the username is in the db
            if not username:
                if not tb.gateway:
                    tb.send_message(msg.from_user.id, "Доступ закрыт. Обратитесь к администратору.")
                    tb.delete_message(msg.chat.id, msg.message_id)
                    msg.text = "deny_access"
                else:
                    db.User.add(msg)
                    string = "Пользователь {} получил доступ\n\n".format(msg.from_user.username)
                    tb.answer_callback_query(tb.gateway.id, string, True)
                    Shortcut.overwrite(tb.gateway, "Пользователи", Inline.user_list(tb.gateway))
                    
                    log.user("@" + db.User.get_username_by_id(tb.gateway.from_user.id) + " открыл доступ для @" + msg.from_user.username)
                    tb.gateway = None
            else: 
                #Update the db entry if the user has changed his/her username
                if msg.from_user.username != username:
                    db.User.update_username(msg.from_user.id, msg.from_user.username)
                    tb.send_message(msg.from_user.id, "Ваш новый юзернейм @{} добавлен в базу данных".format(msg.from_user.username))
                #Force lowercase for any text message
                try:
                    msg.text = msg.text.lower()
                except: pass
                

            # Open menu if no command found
      
        @tb.message_handler(func=lambda msg: msg.text != "deny_access")
        def menu(msg):
            tb.send_message(msg.from_user.id, formatter.title("Главное Меню") ,reply_markup=Inline.menu(msg), parse_mode="HTML")
            Shortcut.purge_messages(msg)
            

        @staticmethod
        @tb.callback_query_handler(func=lambda m: True)
        def callback_handler(call):
            path = call.data.split("_")
            button = path[-1]
            print("Call data: " + call.data)
        
            #Return user's id and role if exists in the db
            username = db.User.get_username_by_id(call.from_user.id)
            
            #Check if the username is in the db
            if not username:
                tb.answer_callback_query(call.id, "Доступ закрыт. Обратитесь к администратору", True)
                path = None
            else: 
                #Update the db entry if the user has changed his/her username
                if call.from_user.username != username:
                    db.User.update_username(call.from_user.id, call.from_user.username)
            del(username)
            
            if not path: pass
            elif len(path) == 1:
                
                if button == "cat":
                    Shortcut.overwrite(call, formatter.title("Категории"), Inline.categories_list(call))
                    
                elif button == "us":
                    Shortcut.overwrite(call, formatter.title("Пользователи"), Inline.user_list(call))
                    
                elif button == "log":
                    Shortcut.overwrite(call, log.get(), Inline.log())
                    
                elif button == "per":
                    Shortcut.overwrite(call, formatter.title("Мой Реквизит"), Inline.personal(call))
                    
            else:
                
                if path[0] == "log":
                    
                    if   button == "back":      Shortcut.overwrite(call, formatter.title("Главное Меню"), Inline.menu(call))
                    elif button == "complete":  Shortcut.overwrite(call, log.get(), Inline.log())
                    elif button == "user":      Shortcut.overwrite(call, log.get("USER"), Inline.log())
                    elif button == "transfers": Shortcut.overwrite(call, log.get("PROP"), Inline.log())
                    elif button == "props":     Shortcut.overwrite(call, log.get("EDIT"), Inline.log())
                    
                elif path[0] == "not": pass
                    
                elif path[0] == "per":
                    
                    if path[1] == "b":
                        
                        Shortcut.overwrite(call, formatter.title("Главное Меню"), Inline.menu(call))
                        
                    else:
                        
                        prop = db.Prop.get(path[1], path[2])
                        
                        if len(path) == 3:
                                
                            if not prop[2]:
                                Shortcut.overwrite(call, formatter.prop(prop), Inline.personal_prop_viewer(prop))
                            else:
                                tb.send_photo(call.message.chat.id, prop[2], formatter.prop(prop), parse_mode="HTML", reply_markup=Inline.personal_prop_viewer(prop))
                                Shortcut.purge_call(call)
                        
                        else:
                            
                            if button == "r":
                                
                                log.prop("@{} вернул [{}]|{}".format(prop[3], db.Prop.get_category_name(prop[0]), prop[1]))
                                db.User.decrement(prop[3])
                                db.Prop.chown(prop[1], None)
                                
                                tb.answer_callback_query(call.id, "Реквизит возвращён", True)
                                
                            Shortcut.overwrite_prop(prop, call, formatter.title("Мой Реквизит"), Inline.personal(call))
                          
                elif path[0] == "us":
                    
                    if len(path) == 2 and button == "back":
                        Shortcut.overwrite(call, formatter.title("Главное Меню"), Inline.menu(call))
                        
                    elif path[1] == "add":
                        
                        if len(path) == 2:
                            
                            if not tb.gateway:
                                Shortcut.overwrite(call, "Чтобы добавить пользователя напишите боту с его аккаунта", Inline.cancel(call.data))
                                
                                tb.gateway = call
                                
                            else:
                                tb.answer_callback_query(call.id, "Шлюз уже открыт @" + db.User.get_username_by_id(tb.gateway.from_user.id), True)
                            
                        else:
                            if button == "c":
                                Shortcut.overwrite(call, db.User.get_pretty_user_list(), Inline.user_list(call))
                                tb.gateway = None
                    
                    else:
                        
                        if button == "back":
                            Shortcut.overwrite(call, formatter.title("Пользователи"), Inline.user_list(call))
                            
                        else: 
                            user = db.User.get_entry_by_username(path[1])
                            props = db.Prop.get_user(user[0])
                            
                            if len(path) == 2:
                                try:
                                    user = db.User.get_entry_by_username(path[1])
                                    props = db.Prop.get_user(user[0])
                                    string = formatter.user(user, props)
                                    
                                    Shortcut.overwrite(call, string, Inline.user_viewer(call, user))
                                    
                                except Exception as e:
                                    raise(e)
                                    tb.answer_callback_query(call.id, "Никнейм не найден в базе данных", True)
                            
                            elif path[2] != "kick":
                            
                                if button == "promote":
                                    promotion = db.User.promote(user)
                                    promotion = "хранителя" if promotion == "keeper" else "админинстратора"
                                    log.user("@" + call.from_user.username + " повысил @" + user[0] + " до уровня " + promotion)
                                
                                elif button == "demote":
                                    demotion = db.User.demote(user)
                                    demotion = "пользователя" if demotion == "user" else "хранителя"
                                    log.user("@" + call.from_user.username + " понизил @" + user[0] + " до уровня " + demotion)
                                    
                                
                                user = db.User.get_entry_by_username(user[0])
                                Shortcut.overwrite(call, formatter.user(user, props), Inline.user_viewer(call, user))
                            
                            else:
                                
                                if button == "kick":
                                    Shortcut.overwrite(call, "Вы уверены, что хотите кикнуть @" + user[0] + "?", Inline.confirm(call.data))
                                    
                                elif button == "yes":
                                    db.User.kick(user[0])
                                    tb.answer_callback_query(call.id, path[1] + " удалён из базы данных", True)
                                    
                                    Shortcut.overwrite(call, formatter.title("Пользователи"), Inline.user_list(call))
                                    
                                    log.user("@" + call.from_user.username + " кикнул @" + user[0])
                                    
                                elif button == "no":
                                    user = db.User.get_entry_by_username(user[0])
                                    Shortcut.overwrite(call, formatter.user(user, props), Inline.user_viewer(call, user))

                elif path[0] == "cat":
                    
                    if path[1] == "back":
                            
                        Shortcut.overwrite(call, formatter.title("Главное Меню"), Inline.menu(call))
                        
                    else:
                        
                        category = path[1]
                        
                        if len(path) == 2:
                            
                            if button != "add":
                                
                                msg = Shortcut.overwrite(call, formatter.title(db.Prop.get_category_name(category)), Inline.category_viewer(call, category))
                                
                            else:
                                
                                tb.send_message(call.message.chat.id, "Введите название категории", reply_markup=Reply.add_category(), parse_mode="HTML")
                                Shortcut.purge_call(call)
                                tb.register_next_step_handler(call.message, Next_Step.add_category)
                        
                        elif path[2] == "back":
                                
                            Shortcut.overwrite(call, formatter.title("Категории"), Inline.categories_list(call))
                            
                        elif path[2] == "add":
                            
                            tb.send_message(call.from_user.id, "Введите название реквизита", reply_markup=Reply.add_prop())
                            tb.register_next_step_handler(call.message, Next_Step.add_name, db.Prop.get_category_name(category))
                            
                        else:
                            
                            prop = db.Prop.get(path[1], path[2])
                            
                            if len(path) == 3:
                                
                                if not prop[2]:
                                    Shortcut.overwrite(call, formatter.prop(prop), Inline.prop_viewer(call, prop))
                                else:
                                    tb.send_photo(call.message.chat.id, prop[2], formatter.prop(prop), parse_mode="HTML", reply_markup=Inline.prop_viewer(call, prop))
                                    Shortcut.purge_call(call)
                                    
                            elif button == "b":
                                
                                Shortcut.overwrite_prop(prop, call, formatter.title(db.Prop.get_category_name(category)), Inline.category_viewer(call, category))
                                
                            elif button == "h":
                                user = db.User.get_entry_by_username(prop[3])
                                props = db.Prop.get_user(user[0])
                                string = formatter.user(user, props)
                                
                                Shortcut.overwrite_prop(prop, call, string, Inline.user_viewer(call, user))
                                    
                            elif button == "t":
                
                                db.Prop.chown(prop[1], call.from_user.username)
                                log.prop("@{} забрал [{}]|{}".format(call.from_user.username, db.Prop.get_category_name(prop[0]), prop[1]))
                                db.User.increment(call.from_user.username)
                                prop = db.Prop.get(path[1], prop[4])  
                                if prop[2]:
                                    tb.edit_message_caption(formatter.prop(prop), call.message.chat.id, call.message.message_id, 
                                                            reply_markup=Inline.prop_viewer(call, prop), parse_mode="HTML")
                                else:
                                    Shortcut.overwrite(call, formatter.prop(prop), Inline.prop_viewer(call, prop))
                                
                                    
                            elif button == "r":
                                
                                log.prop("@{} вернул [{}]|{}".format(prop[3], db.Prop.get_category_name(prop[0]), prop[1]))
                                db.User.decrement(prop[3])
                                db.Prop.chown(prop[1], None)
                                prop = db.Prop.get(path[1], prop[4])
                                if prop[2]:
                                    tb.edit_message_caption(formatter.prop(prop), call.message.chat.id, call.message.message_id, 
                                                            reply_markup=Inline.prop_viewer(call, prop), parse_mode="HTML")
                                else:
                                    Shortcut.overwrite(call, formatter.prop(prop), Inline.prop_viewer(call, prop))
                                
                                
                            elif path[3] == "d":
                                
                                if len(path) == 4:
                                    
                                    tb.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=Inline.confirm(call.data))
                                    
                                elif button == "no":
                                    tb.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=Inline.prop_viewer(call, prop))
                                    
                                elif button == "yes":
                                    
                                    category_name = db.Prop.get_category_name(prop[0])
                                        
                                    db.Prop.delete(prop[0], prop[4])
                                    
                                    log.edit("@{} удалил [{}]|{}".format(call.from_user.username, category_name, prop[1]))
                                    
                                    if prop[3]:
                                        db.User.decrement(prop[3])
                                        
                                    if db.Prop.get_all(prop[0]):
                                        Shortcut.overwrite_prop(prop, call, formatter.title(db.Prop.get_category_name(category)), Inline.category_viewer(call, category))
                                        
                                    else:
                                        Shortcut.overwrite_prop(prop, call, formatter.title("Категории"), Inline.categories_list(call))
                                        
                            elif path[3] == "pic":
                                
                                if len(path) == 4:
                                
                                    msg = Shortcut.overwrite_prop(prop, call, "Пришлите фото для этого реквизита", Inline.cancel(call.data))
                                    tb.register_next_step_handler(msg, Next_Step.add_photo, prop)
                                    
                                else:
                                    
                                    msg = None
                                    if not prop[2]:
                                        msg = Shortcut.overwrite_prop(prop, call, formatter.prop(prop), Inline.prop_viewer(call, prop))
                                    else:
                                        msg = tb.send_photo(call.message.chat.id, prop[2], formatter.prop(prop), 
                                                            reply_markup=Inline.prop_viewer(call, prop), parse_mode="HTML")
                                        Shortcut.purge_messages(call.message)
                                    tb.register_next_step_handler(msg, menu)
                        
                          
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