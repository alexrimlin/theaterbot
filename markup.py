
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from database import Database as db

def get_markup(*args, menu="", initial=None):
    markup = initial if initial else InlineKeyboardMarkup()
    if menu != "": menu += "_"
    for arg in args:
        markup.row(*list(InlineKeyboardButton(button[0], callback_data=menu + button[1]) for button in arg))
    return markup

class Reply():
    @staticmethod
    def add_category():
        markup = ReplyKeyboardMarkup(row_width=3)
        categories = db.Prop.get_categories()
        
        if categories:
            markup.add(*list(category[0].title() for category in categories))
        
        markup.add("Отмена")
        
        return markup
    
    @staticmethod
    def add_prop():
        markup = ReplyKeyboardMarkup()
        markup.row(KeyboardButton("Отмена"))
        return markup

class Inline():
    
    @staticmethod
    def menu(msg):
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("Реквизит", callback_data="cat"))
        markup.row(InlineKeyboardButton("Мой Реквизит", callback_data="per"))
        markup.row(InlineKeyboardButton("Пользователи", callback_data="us"))
        if db.User.is_keeper(msg.from_user.username):
            markup.row(InlineKeyboardButton("Лог", callback_data="log"))
        return markup
    
    @staticmethod
    def cancel(path):
        markup = get_markup((("Отмена", "c"),), menu=path)
        return markup
    
    @staticmethod
    def confirm(path):
        path += "_"
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("Подтвердить", callback_data=path+"yes"),
            InlineKeyboardButton("Отменить", callback_data=path+"no")
        )
        return markup
    

    @staticmethod
    def addorback(call):
        markup = InlineKeyboardMarkup()
        if db.User.is_keeper(call.from_user.username):
            markup.row(InlineKeyboardButton("Добавить", callback_data="add"))
        markup.row(InlineKeyboardButton("Назад", callback_data="back"))
        return markup
    
    @staticmethod
    def personal(call):
        entries = db.Prop.get_user(call.from_user.username)
        props = []
        print(entries)
        for prop in entries:
            string = "[" + db.Prop.get_category_name(prop[0]).title() + "] " + prop[1]
            props.append(("per_" + str(prop[0]) + "_" + str(prop[3]), string))
            
        print(props)
            
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(*list(InlineKeyboardButton(prop[1], callback_data=prop[0]) for prop in props))
        
        markup.add(InlineKeyboardButton("Назад", callback_data="per_b"))
        
        return markup
    
    def personal_prop_viewer(prop):
        
        path = 'per_' + str(prop[0]) + "_" + str(prop[4]) + "_"
        markup = InlineKeyboardMarkup(row_width=4)
        markup.add(InlineKeyboardButton("Вернуть", callback_data=path+"r"))
        markup.add(InlineKeyboardButton("Назад", callback_data=path+"b"))
        
        return markup
    
    @staticmethod
    def log():
        markup = get_markup((("Общий", "complete"), ("Пользовательский", "user")),
                            (("Передачи", "transfers"), ("Реквизит", "props")),
                            (("Назад", "back"),),
                            menu="log")                   
        return markup
    
    @staticmethod
    def user_list(call):
        entries = db._query("SELECT username,props,role FROM holders ORDER BY role DESC, props")
        usernames = []
        for entry in entries:
            emoji = ""
            if entry[2] == "user": emoji = "🙋"
            elif entry[2] == "keeper": emoji = "👨‍🔧️"
            else: emoji = "👨‍⚖️"
            usernames.append(("us_" + entry[0], (str(entry[1]) if entry[1] else "") + emoji + entry[0]))
            
        markup = InlineKeyboardMarkup(row_width=3)
        markup.add(*list(InlineKeyboardButton(name[1], callback_data=name[0]) for name in usernames))
        
        if db.User.is_admin(call.from_user.username):
            markup = get_markup((("|Добавить пользователя|", "add"),),
                                menu="us", initial=markup
        )
        
        markup = get_markup((("|Назад|", "back"),),
                            menu="us", initial=markup)
        return markup
    
    @staticmethod
    def user_viewer(call, user_info):
        role = user_info[2]
        markup = InlineKeyboardMarkup()
        if db.User.is_admin(call.from_user.username):
            row = ()
            if role == "user":
                row = (("Повысить", "promote"), ("Кикнуть", "kick"))
            elif role == "keeper":
                row = (("Повысить", "promote"), ("Понизить", "demote"))
            elif role == "admin":
                row = (("Понизить", "demote"),)
            markup = get_markup(row, menu="us_"+user_info[0])
        markup = get_markup((("Назад", "back"),), menu="us_"+user_info[0], initial=markup)
        return markup
    
    @staticmethod
    def categories_list(call):
        categories = db.Prop.get_categories()
        markup = InlineKeyboardMarkup(row_width=2)
        
        if categories:
            markup.add(*list(InlineKeyboardButton("[" + str(category[1]) + "]" + category[0].title(), callback_data="cat_" + str(category[2])) for category in categories))
        
        if db.User.is_keeper(call.from_user.username):
            markup.add(InlineKeyboardButton("|Добавить|", callback_data="cat_add"))
        markup.add(InlineKeyboardButton("|Назад|", callback_data="cat_back"))
        
        return markup
    
    @staticmethod
    def category_viewer(call, category):
        entries = db.Prop.get_all(category)
        props = []
        for prop in entries:
            string = ("🙅" if prop[2] else "") + ("📷" if prop[1] else "") + prop[0].title()
            props.append(("cat_" + category + "_" + str(prop[3]), string))
            
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(*list(InlineKeyboardButton(prop[1], callback_data=prop[0]) for prop in props))
        
        if db.User.is_keeper(call.from_user.username):
            markup.add(InlineKeyboardButton("|Добавить|", callback_data="cat_" + category + "_add"))
        markup.add(InlineKeyboardButton("|Назад|", callback_data="cat_" + category + "_back"))
        
        return markup
    
    @staticmethod
    def prop_viewer(call, prop):
        keeper = db.User.is_keeper(call.from_user.username)
        path = 'cat_' + str(prop[0]) + "_" + str(prop[4]) + "_"
        first_row = []
        if not prop[3]:
            first_row.append(('Забрать', path + "t"))
        elif prop[3] == call.from_user.username or keeper:
            first_row.append(('Вернуть', path + "r"))
        if prop[3] and prop[3] != call.from_user.username:
            first_row.append(("Обладатель", path + "h"))
        
        markup = InlineKeyboardMarkup(row_width=3)
        markup.add(*list(InlineKeyboardButton(button[0], callback_data=button[1]) for button in first_row))
        if keeper:
            markup.add(InlineKeyboardButton("Фото", callback_data=path+"pic"), InlineKeyboardButton("Удалить", callback_data=path+"d"))
        markup.add(InlineKeyboardButton("Назад", callback_data=path+"b"))
        
        return markup
        
        
    