from os import stat
import sqlite3

class Database():
        
    @staticmethod
    def _change(*args, **kwargs):
        
        conn = sqlite3.connect("theater.db")
        c = conn.cursor()
        
        c.execute(*args, **kwargs)

        conn.commit()

        conn.close()
        
        
    @staticmethod
    def _query(*args, **kwargs):
        
        conn = sqlite3.connect("theater.db")
        c = conn.cursor()
        
        c.execute(*args, **kwargs)
        result = c.fetchall()
        conn.close()
        return result
    
    @staticmethod
    def has_admins():
        result = Database._query("SELECT COUNT(*) from holders WHERE role='admin'")
        return result != [(0,)]

    class User():
        
        @staticmethod
        def decrement(username):
            Database._change("UPDATE holders SET props=(props-1) WHERE username=?", (username,))
            
        @staticmethod
        def increment(username):
            Database._change("UPDATE holders SET props=(props+1) WHERE username=?", (username,))

        @staticmethod
        def get_keepers_ids():
            result = Database._query("SELECT id FROM holders WHERE role='admin' OR role='keeper'")
            return [entry[0] for entry in result]
        
        @staticmethod
        def is_admin(username):
            try:
                result = Database._query("SELECT role FROM holders WHERE username='{}'".format(username))[0][0]
                if result == "admin": return True
            except: pass
            return False

        @staticmethod
        def is_keeper(username):
            try:
                result = Database._query("SELECT role FROM holders WHERE username=?", (username,))[0][0]
                if result in ['admin', 'keeper']: return True
            except: pass
            return False
            
        @staticmethod
        def get_pretty_user_list():
            conn = sqlite3.connect("theater.db")
            c = conn.cursor()

            def get_pretty_list(role):
                entries = c.execute("SELECT username,props FROM holders WHERE role='{}' ORDER BY props DESC".format(role)).fetchall()
                string = ""
                if len(entries) != 0:
                    if role == "admin": string += "<i>Администраторы</i>:\n"
                    elif role == "keeper": string += "\n<i>Хранители</i>:\n"
                    elif role == "user": string += "\n<i>Пользователи:</i>\n"
                    for n, entry in enumerate(entries):
                        string += str(n+1) + ". /<b><u>" + entry[0] + "</u></b>" + ("[{}]".format(str(entry[1])) if entry[1] else "") + "\n"
                return string

            result = get_pretty_list("admin") + get_pretty_list("keeper") + get_pretty_list("user")
            conn.close()
            return result
            
        
        @staticmethod
        def get_username_by_id(user_id):
            user_info = Database._query("SELECT username FROM holders WHERE id={}".format(user_id))
            try:
                return user_info[0][0]
            except IndexError:
                return None
        @staticmethod
        def get_id_by_username(username):
            result = Database._query("SELECT id FROM holders WHERE username=?", (username,))
            return result
        @staticmethod
        def get_user_ids(role):
            result = Database._query("SELECT id FROM holders WHERE role='{}'".format(role))
            result = [entry[0] for entry in  result]
            return result

        def get_entry_by_username(username):
            user_info = Database._query("SELECT * FROM holders WHERE username='{}'".format(username))
            try:
                return user_info[0]
            except IndexError:
                return None

        @staticmethod
        def add(msg):
            Database._change("INSERT INTO holders VALUES(?,?,?,?);", (msg.from_user.username, msg.from_user.id, "user", 0))
        @classmethod
        def update_username(cls, user_id, username):
            Database._change("UPDATE props SET holder=? WHERE holder=?", (username, cls.get_username_by_id(user_id)))
            Database._change("UPDATE holders SET username='{}' WHERE id={}".format(username, user_id))
        
        @staticmethod
        def kick(username):
            Database._change("DELETE FROM holders WHERE username='{}'".format(username))
        
        @staticmethod
        def promote(user_info):
            promotion = "keeper"
            username, role = user_info[0], user_info[2]
            if role == "keeper": promotion = "admin"
            Database._change("UPDATE holders SET role='{}' WHERE username='{}'".format(promotion, username))
            return promotion

        @staticmethod
        def demote(user_info):
            demotion = "user"
            username, role = user_info[0], user_info[2]
            if role == "admin": demotion = "keeper"
            Database._change("UPDATE holders SET role='{}' WHERE username='{}'".format(demotion, username))
            return demotion

    class Prop():
        @staticmethod
        def add(name, category, photo, holder):
            Database._change("INSERT INTO props VALUES(?,?,?,?)", (name, category, photo, holder))

        @staticmethod
        def get_categories():
            result = Database._query("SELECT DISTINCT category FROM props")
            result = [category[0] for category in result]
            return result

        @staticmethod
        def get_all(category):
            result = Database._query("SELECT * FROM props WHERE category=?", (category,))
            return result
        
        @staticmethod
        def get_user(username):
            result = Database._query("SELECT * FROM props WHERE holder=?", (username,))
            return result

        @staticmethod
        def get(name):
            result = Database._query("SELECT * FROM props WHERE name=?", (name,))[0]
            return result

        @staticmethod
        def chown(name, holder):
            Database._change("UPDATE props SET holder=? WHERE name=?", (holder, name))
            
        @staticmethod
        def chpic(name, photo_id):
            Database._change("UPDATE props SET photo=? WHERE name=?", (photo_id, name))
        
        @staticmethod
        def delete(name):
            Database._change("DELETE FROM props WHERE name=?", (name,))