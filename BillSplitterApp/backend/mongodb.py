from cmath import e
from pymongo import MongoClient
from BillSplitter.strings import mongo_secret
import pymongo
import re
import random
import string
import BillSplitterApp.backend.data as datastructs

# all backend stuffs handled here


class database:
    def __init__(self) -> None:
        self.storage = None

    def connect_db(self):
        client = pymongo.MongoClient(mongo_secret)
        self.storage = client['BillSplitter']

    def insert_data(self, collectionName, data):
        self.storage.get_collection(collectionName).insert_one(data)


class Authenticator:
    def __init__(self) -> None:
        self.db = database()
        self.db.connect_db()
        self.email = None

    def sign_up(self, email, p, confirmp, nickname):
        try:
            emailregex = re.compile(
                r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
            if not re.fullmatch(emailregex, email):
                return (False, 'Invalid email')
            elif p != confirmp:
                return (False, 'Confirm passwords doesn\'t match')
            elif len(nickname) == 0:
                return (False, 'Name can\'t be empty')
            self.db.insert_data(
                'users', {'_id': email, 'password': p, 'nickname': nickname, 'groups': [], 'tempexpenses': {}})  # temp expenses can potentially become official expense once user submit
            self.email = email
            return (True, None)
        except Exception:
            return (False, 'Account with this email already exists')

    def login(self, email, p):
        doc = self.db.storage.get_collection(
            'users').find_one({'_id': email, 'password': p})
        if not doc or len(doc) == 0:
            return False
        self.email = email
        return True

    # get groups the user belongs to
    def get_groups(self):
        ret = []
        groupcodes = self.db.storage.get_collection(
            'users').find_one({'_id': self.email})['groups']
        for groupcode in groupcodes:
            ret.append(self.db.storage.get_collection(
                'groups').find_one({'_id': groupcode})['name'])
        return ret

    def get_group_count(self):
        return len(self.get_groups)

    # retrieve groups[groupindex]
    def get_group_code(self, groupindex: int):
        return self.db.storage.get_collection('users').find_one({'_id': self.email})['groups'][groupindex]

    # retrieve all member names and emails of groups[groupindex]
    def get_group_members(self, groupcode: str):
        memberemails = self.db.storage.get_collection(
            'groups').find_one({'_id': groupcode})['members']
        memberinfo = []  # in the form of [membername, memberemail]
        for memberemail in memberemails:
            memberinfo.append([self.db.storage.get_collection(
                'users').find_one({'_id': memberemail})['nickname'], memberemail])
        return memberinfo

    # get the display name of the user

    def get_name(self):
        doc = self.db.storage.get_collection(
            'users').find_one({'_id': self.email})
        return doc['nickname']

    # generate a 8 digit code and create a group with that code
    # It'll add the GROUP CODE (not group name) to the user's groups array
    def create_group(self, groupname):
        randomcode = ''.join(random.choice(
            string.ascii_uppercase + string.digits) for _ in range(8))
        self.db.insert_data(
            'groups', {'_id': randomcode, 'name': groupname, 'members': [], 'ledger': []})
        self.join_group(randomcode)

    def join_group(self, groupcode):
        useradded = self.db.storage.get_collection('users').find_one(
            {'_id': self.email, "groups": {'$in': [groupcode]}})
        groupadded = self.db.storage.get_collection('groups').find_one(
            {'_id': groupcode, "members": {'$in': [self.email]}})
        if useradded or groupadded:
            return "You're already part of this group"
        else:
            self.db.storage.get_collection(  # add new group code to groups
                'users').find_one_and_update({'_id': self.email}, {'$push': {"groups": groupcode}})
            # add member to group members field
            self.db.storage.get_collection(
                'groups').find_one_and_update({'_id': groupcode}, {'$push': {"members": self.email}})

    # retrieve temporary expenses for the user for group with groupcode
    def get_tempexpenses(self, groupcode: str):
        expensesmap = self.db.storage.get_collection('users').find_one(
            {'_id': self.email})['tempexpenses']
        if groupcode in expensesmap:
            return expensesmap[groupcode]
        else:
            return {}

    # handle when user submit an item
    def submit_tempexpenses(self, groupcode: str, item: dict):
        if len(self.get_tempexpenses(groupcode)) == 0:  # temp expenses has been submitted before
            self.db.storage.get_collection(
                'users').find_one_and_update({'_id': self.email}, {'$set': {f"tempexpenses.{groupcode}":
                                                                            []
                                                                            }})
        try:
            float(item['itemprice'])
            self.db.storage.get_collection(
                'users').find_one_and_update({'_id': self.email}, {'$push': {f"tempexpenses.{groupcode}": item}})
        except Exception:
            return 'Item price must be a positive number'

    # handle user making change to temp expense
    def update_tempexpenses(self, groupcode: str, newitem: dict, itemindex: str):
        itemindex = int(itemindex)
        newitem['itemprice'] = newitem['itemprice'].strip('$')
        self.db.storage.get_collection(
            'users').find_one_and_update({'_id': self.email}, {'$set': {f"tempexpenses.{groupcode}.{itemindex}":
                                                                        newitem
                                                                        }})

    # handle user deleting item
    def delete_tempexpense(self, groupcode: str, itemindex: str):
        itemindex = int(itemindex)
        self.db.storage.get_collection('users').find_one_and_update(
            {'_id': self.email}, {'$unset': {f"tempexpenses.{groupcode}.{itemindex}": 1}})
        self.db.storage.get_collection('users').find_one_and_update(
            {'_id': self.email}, {'$pull': {f"tempexpenses.{groupcode}": None}})

    def get_tempexpense_length(self, groupcode: str):
        try:
            expenses = self.db.storage.get_collection('users').find_one(
                {'_id': self.email})['tempexpenses'][groupcode]
        except Exception:
            return 0
        return len(expenses) if expenses else 0

    # promote a temp expense to a pending expense.  Submit it to group and simultaneously send survey to all involving members
    def pend_expense(self, groupcode: str, expensename: str):
        expenses = self.get_tempexpenses(groupcode)
        pexpenses = self.get_pending_expenses(groupcode)
        for pexpense in pexpenses:
            if pexpense['expensename'] == expensename and pexpense['email'] == self.email:
                return 'An expense of the same name already exists'
        if len(expenses) == 0:
            return 'Expenses form can\'t be empty'
        elif len(expensename) == 0:
            return 'Expense name can\'t empty'
        self.db.storage.get_collection(
            'groups').find_one_and_update({'_id': groupcode}, {'$push': {f"pendingexpenses": datastructs.PendingExpense(
                expensename, self.email, expenses).toJson()}})

    def get_pending_expenses(self, groupcode: str):
        try:
            ret = self.db.storage.get_collection(
                'groups').find_one({'_id': groupcode})['pendingexpenses']
            return ret
        except Exception:
            return []


class PageGenerator:
    def __init__(self, authenticator: Authenticator):
        self.auth = authenticator

    def generatepages(self, page, groupindex):
        pages = [False for i in range(5)]
        if page == 'home':
            pages[0] = True
        elif page == 'about':
            pages[1] = True
        elif page == 'profile':
            pages[2] = True
        elif page == 'contact':
            pages[3] = True
        else:   # if the page active is a groups page
            pages[4] = self.auth.get_group_code(groupindex)

        return pages


class Util:
    # extract the array index to delete from form data
    def extractDelete(self, data: dict):
        matchregex = re.compile(
            r'deleteitem[0-9]+')
        for k, v in data.items():
            if re.fullmatch(matchregex, k):
                return int(k[10:])
        return -1

    # add name to each pendingexpenses for display
    def switch_email_to_name(self, pendingexpenses, members):
        members = {v[1]: v[0] for v in members}  # members will be {email:name}
        for p in pendingexpenses:
            p['name'] = members[p['email']]
        return pendingexpenses

    # encode email to replace '.' with '@' in order to avoid problem with mongodb

    def encodeEmail(self, email: str):
        return email.replace('.', '@')

    # decode email replace all '@' except second to last one with '.'
    def decodeEmail(self, email: str):
        allindexes = []
        email = list(email)
        for index in range(len(email)):
            if email[index] == '@':
                allindexes.append(index)
        allindexes.pop(-2)
        for index in allindexes:
            email[index] = '.'
        return "".join(email)
