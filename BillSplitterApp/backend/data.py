import re
import random
import string


class item:  # use for temporary expense
    def __init__(self, name, price, quantity, splitmode):
        self.name = name
        self.price = price
        self.quantity = quantity
        self.splitmode = splitmode

    # serialize the object to a json
    def toJson(self):
        return {'itemname': self.name, 'itemprice': self.price, 'itemquantity': int(self.quantity), 'itemsplitmode': int(self.splitmode)}
    
class PendingExpense:
    def convert_items(self):
        for item in self.items:
            totalprice = float(item['itemprice']) * int(item['itemquantity'])
            item = {'name': item['itemname'], 'totalprice': totalprice, 'splitmode': item['itemsplitmode']}
    def __init__(self, expensename, email, items):
        self.expensename = expensename
        self.items = items  # holdes a list of items
        self.email = email
        self.convert_items()
    def toJson(self):
        jsonobj = {'expensename': self.expensename, 'email': self.email, 'actionrequired': "Waiting For Others",  'items': self.items}
        return jsonobj


# example usage   

# e = expense("test")
# e.items.append(item('bruh', 5, 2))
# e.items.append(item('bruh2', 1, 1))
# e.items.append(item('bruh3', 2, 1))
# print(e.toJson())
