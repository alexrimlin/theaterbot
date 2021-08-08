
#* Форматирование категорий
def categories(categories):
    string = "<i>Категории</i>:"
    for n, cat in enumerate(categories):
        string += "\n/<b><u>ID" + str(n) + "</u></b>" + ". " + cat.title()
    return string

#* Форматирование списка реквизитов в категории
def props(props):
    string = "<i>" + props[0][0].title() + "</i>:\n"
    for n, prop in enumerate(props):
        string += "<u><b>/ID" + str(n) + "</b></u>" + (".📷" if prop[2] else ". ") + prop[1].title() + ("[/{}]".format(prop[3]) if prop[3] else "") + "\n"
    return string

#* Форматирование списка реквизита в меню игрока
def user_props(props):
    string = "\n<i>Реквизит[" + str(len(props)) + "]</i>:"
    for n, prop in enumerate(props):
        string += "\n/<b><u>ID" + str(n) + "</u></b>" + (".📷" if prop[2] else ". ") + prop[1].title()
    return string
    
#* Форматирование единичного реквизита
def prop(prop):
    string = "<u><b>" + prop[1].title() + "</b></u>\n"
    string += "<i>Категория</i>: " + prop[0].title()
    if prop[3]:
        string += "\n<i>Обладатель</i>: /<b>" + prop[3] + "</b>"
    return string
