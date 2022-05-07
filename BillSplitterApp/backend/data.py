
import re
import random
import string


class item:
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

    # serialize the object to a json
    def toJson(self):
        return {'itemname': self.name, 'itemprice': self.price, 'itemquantity': int(self.quantity)}
    
class expense:
    def __init__(self, expensename):
        self.expensename = expensename
        self.items = []  # holdes a list of items
    def toJson(self):
        jsonobj = {'expensename': self.expensename, 'items': [i.toJson() for i in self.items]}
        return jsonobj

# class tempexpense(expense):
#     def __init__(self, expensename, groupcode):
#         expense.__init__(expensename)
#         self.groupcode = groupcode


# example usage   

# e = expense("test")
# e.items.append(item('bruh', 5, 2))
# e.items.append(item('bruh2', 1, 1))
# e.items.append(item('bruh3', 2, 1))
# print(e.toJson())
