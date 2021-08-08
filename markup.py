from os import stat
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from database import Database
db = Database

class Markup():

    _cancel = ReplyKeyboardMarkup()
    _cancel.row(KeyboardButton("Отмена"))
    @classmethod
    def cancel(cls): return cls._cancel

    _yesorno = ReplyKeyboardMarkup()
    _yesorno.row(KeyboardButton("Да"), KeyboardButton("Нет"))
    @classmethod
    def yesorno(cls): return cls._yesorno

    _back = ReplyKeyboardMarkup()
    _back.row(KeyboardButton("Назад"))
    @classmethod
    def back(cls): return cls._back
    
    @staticmethod
    def main(msg):
        markup = ReplyKeyboardMarkup()
        markup.row(KeyboardButton("Реквизит"), KeyboardButton("Пользователи"))
        if db.User.is_keeper(msg.from_user.username):
            markup.row(KeyboardButton("Лог"))
        return markup
    
    @staticmethod
    def log():
        markup = ReplyKeyboardMarkup(row_width=2)
        markup.add("Назад")
        markup.add("Общий", "Админ")
        markup.add("Передачи", "Реквизит")
        return markup
    
    @staticmethod
    def addorback(msg):
        markup = ReplyKeyboardMarkup()
        markup.row(KeyboardButton("Назад"))
        if db.User.is_keeper(msg.from_user.username):
            markup.row("Добавить")
        return markup

    class Users():
        @staticmethod
        def menu(msg):
            markup = ReplyKeyboardMarkup()
            markup.row(KeyboardButton("Назад"))
            if db.User.is_admin(msg.from_user.username):
                markup.row("Добавить пользователя")
            return markup

        @staticmethod
        def viewer(msg, user_info):
            role = user_info[2]
            markup = ReplyKeyboardMarkup(row_width=2)
            markup.add("Назад")
            if db.User.is_admin(msg.from_user.username):
                if role == "user": 
                    markup.add("Повысить", "Кикнуть")
                if role == "keeper": 
                    markup.add("Повысить", "Понизить")
                if role == "admin":
                    markup.add("Понизить")
            return markup
            
    class Prop():
        @staticmethod
        def viewer(msg, prop):
            keeper = db.User.is_keeper(msg.from_user.username)
            markup = ReplyKeyboardMarkup(row_width=2)
            first_row = ["Назад"]
            if not prop[3]:
                first_row.append('Забрать')
            elif prop[3] == msg.from_user.username or keeper:
                first_row.append('Вернуть')
            if keeper:
                first_row.extend(["Фото", "Удалить"])
            markup.add(*first_row)
            return markup
            

        
