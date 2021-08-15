import sqlite3
import datetime
class Logger():
    def __init__(self):
        
        #* Инициализация соединения с базой данных
        self.conn = sqlite3.connect("theater.db", check_same_thread=False)
        self.c = self.conn.cursor()
        
        #* Создание таблицы для лога
        self.c.execute("""
                       CREATE TABLE IF NOT EXISTS log (
                           timestamp timestamp NOT NULL,
                           severity text NOT NULL,
                           text text NOT NULL
                       )
                       """)
        self.conn.commit()
        
    #* Обобщённая запись в лог
    def _log(self, severity, text):
        print("[" + severity + "] " + text)
        while True:
            try:
                self.c.execute("INSERT INTO log VALUES(?,?,?)", (datetime.datetime.now(), severity, text))
                self.conn.commit()
            except:
                continue
            break
        
    #* Действия с пользователями
    def user(self, text):
        self._log("USER", text)
        
    #* Изменение реквезита
    def edit(self, text):
        self._log("EDIT", text)
    
    #* Передача реквизита
    def prop(self, text):
        self._log("PROP", text)
        
    #* Очистка таблицы от старых записей (больше 2 дней)
    def clear(self):
        delta = datetime.datetime.now() + datetime.timedelta(days=-2)
        
        while True:
            try:
                self.c.execute("DELETE FROM log WHERE timestamp < ?", (delta,),)
                self.conn.commit()
            except:
                continue
            break
        
    #* Подчистить таблицу и вернуть читабельный лог
    def get(self, severity=None):
        
        if not severity: self.clear()
        
        query = "SELECT * FROM log"
        if severity:
            query += " WHERE severity='{}'".format(severity)
        query += " LIMIT 96"
            
        self.c.execute(query)
        entries = self.c.fetchall()
        
        result = ""
        for entry in entries:
            result += "\n" + entry[0][5:-10] + ("|[{}]".format(entry[1]) if not severity else "|") + entry[2]
        result += "\n🠉 Log"
        result += "[{}] 🠉".format(severity) if severity else " 🠉"
        
        return result[-4096:]