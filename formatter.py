from database import Database as db


def user_props(props):
    string = "\n<i>Реквизит[" + str(len(props)) + "]</i>:"
    for n, prop in enumerate(props):
        string += "\n/<b><u>ID" + str(n) + "</u></b>" + (".📷" if prop[2] else ". ") + prop[1].title()
    return string
    
def prop(prop):
    string = "<u><b>" + prop[1].title() + "</b></u>\n"
    string += "<i>Категория</i>: " + db.Prop.get_category_name(prop[0]).title()
    if prop[3]:
        string += "\n<i>Обладатель</i>: @<b>" + prop[3] + "</b>"
    
    return string

def user(user_info, props):
    
    string = "@{} – ".format(user_info[0])
    if user_info[2] == "user": string += "Пользователь"
    elif user_info[2] == "keeper": string += "Хранитель"
    elif user_info[2] == "admin": string += "Админинстратор"
    
    if user_info[3]: 
        string += user_props(props)
    return string

def title(string):
    padding = " " * (( 40 - len(string) ) // 2)
    string = "*" + padding + "<b><u>" + string.upper() + "</u></b>" + padding + "*"
    return string