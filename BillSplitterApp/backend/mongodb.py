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

    # get groups the user belongs to in the form of array of groupcodes
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
    
    # get groupindex based on groupcode
    def get_group_index(self, groupcode: str):
        groups = self.db.storage.get_collection(
            'users').find_one({'_id': self.email})['groups']
        for i, group in enumerate(groups):
            if groupcode == group:
                return i

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
        try:
            return self.db.storage.get_collection('users').find_one(
                {'_id': self.email})['tempexpenses'][groupcode]
        except Exception:
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
            items = self.db.storage.get_collection(
                'users').find_one({'_id': self.email})["tempexpenses"][groupcode]
            if item['itemname'] in [i['itemname'] for i in items]:
                return 'There\'s already an item of the same name'
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
    
    # submit survey to group[groupcode] and check if all groupmembers have submitted data (if true then delete from pending expenses and add to ledger)
    # example surveydata: {'selected0': [''], 'quantityselect0': ['1']}
    def submit_survey(self, expensename, groupcode, surveydata: dict):
        pendingexpenses = self.get_pending_expenses(groupcode)
        survey = {'items': {}, 'oweTotal': 0.0}
        selectedregex = re.compile(
            r'selected[0-9]+')
        itemindexes = []
        for k,v in surveydata.items():
            if re.fullmatch(selectedregex, k):
                itemindexes.append(int(k[8:]))
                
        pexpenseIndex = None    
        for index, expenses in enumerate(pendingexpenses):
            if expenses['expensename'] == expensename:
                pexpenseIndex = index
                for itemindex in itemindexes:
                    itemChose = expenses['items'][itemindex]
                    quantityChose = int(surveydata[f'quantityselect{itemindex}'])
                    survey['oweTotal'] += float(itemChose['itemprice']) * quantityChose
                    survey['items'][itemChose['itemname']] = quantityChose
                self.db.storage.get_collection(
            'groups').find_one_and_update({'_id': groupcode}, {'$set': {f"pendingexpenses.{index}.surveys.{Util().encodeEmail(self.email)}": survey}})
                
        
        surveyLength = len(self.db.storage.get_collection(
            'groups').find_one({'_id': groupcode})['pendingexpenses'][pexpenseIndex]['surveys'])
        # check if everyone except payor submitted the survey
        if surveyLength == len(self.get_group_members(groupcode))-1:
            # update status of survey to archivable
            self.db.storage.get_collection(
            'groups').find_one_and_update({'_id': groupcode}, {'$set': {f'pendingexpenses.{pexpenseIndex}.actionrequired': 'Everyone Completed Survey (click me)'}})
            # generate transaction report based on all surveys
            self.calculate_expenses(self.get_pending_expenses(groupcode)[pexpenseIndex])
                
    # check if current user has finished the survey for expense[expenseIndex]
    def check_finished_survey(self, groupcode, expenseIndex: int):
        pexpense = self.get_pending_expenses(groupcode)[expenseIndex]
        if 'surveys' not in pexpense:
            return False
        return Util().encodeEmail(self.email) in pexpense['surveys']


    # calcualte how much each member owe payor
    def calculate_expenses(self, pexpense: dict):
        # pseudo-code:
        # loop over items on the respective pendingexpense[pindex]
        # for each item, find member who mentioned it in his/her survey
        # get total number of "shares", divide total item price(price*quantity)
        # by that number and multiply each person's share to get total owed to payer
        #
        # Uneven split
        # "Share" price is calculated differently depending on if the item is deemed a shared item or
        # non share item.  non share item price is simply just item price while shared item price is 
        # calculated with a more complicated algorithm
        #
        # Even split
        # amount owe simply calculated by totalprice / number of members
        expensesheet = {} # {email: amoutowe}
        surveys = (dict)(pexpense['surveys'])
        for item in pexpense['items']:
            totalprice = float(item['itemprice']) * int(item['itemquantity'])
            if int(item['itemsplitmode']) == 1:  # uneven split
                totalshares = 0
                itemname = item['itemname']
                tempsheet = {} # {email: shares of item} tally how many shares of the current item each member claims
                for email, surveyitems in surveys.items():
                    if itemname in surveyitems['items']:
                        email = Util().decodeEmail(email)
                        tempsheet[email] = surveyitems['items'][itemname]
                        totalshares += surveyitems['items'][itemname]
                totalshares = 1 if not totalshares else totalshares  # avoid divide by 0 error
                pricepershare = (totalprice / totalshares) if totalshares >= int(item['itemquantity']) else float(item['itemprice'])  # only use "share" price when it's a share item otherwise just use itemprice
                for email, shares in tempsheet.items():
                    if email not in expensesheet:
                        expensesheet[email] = 0
                    expensesheet[email] += shares * pricepershare
            else: # even split
                membercount = len(surveys.items())+1
                for email in surveys.keys():
                    email = Util().decodeEmail(email)
                    if email not in expensesheet:
                        expensesheet[email] = 0
                    expensesheet[email] += totalprice / membercount
                    
                
        print(expensesheet)
                    
        


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
    def process_pendingexpenses(self, groupcode, members, auth: Authenticator):
        members = {m[1]: m[0] for m in members}  # members will be {email:name}
        currentemail = auth.email
        pendingexpenses = auth.get_pending_expenses(groupcode)
        for i, p in enumerate(pendingexpenses):
            p['name'] = members[p['email']]
            if p['email'] != currentemail:
                if 'Wait' in p['actionrequired'] and  not auth.check_finished_survey(groupcode, i):  # incomplete survey
                    p['actionrequired'] = 'Pending Survey (click me)'
                    p['color'] = 'yellow'
                elif auth.check_finished_survey(groupcode, i):  # completed survey
                    p['actionrequired'] = 'Survey Completed!'
                    p['color'] = 'green'
            else:  # pexenpse if owned by current logged in user
                if 'Everyone' in p['actionrequired']:
                    p['color'] = 'lightblue'
                
                    
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
    
    # retrieve items from pending expense with name but splitmode isn't 0
    def get_items(self, expenses, name):  
        finalitems = []
        for expense in expenses:
            if expense['expensename'] == name:
                for item in expense['items']:
                    if item['itemsplitmode'] == 1: # only survey uneven split items
                        itemname = item['itemname'] if item['itemquantity'] == 1 else f"{item['itemname']} *{item['itemquantity']}  "
                        itemprice = float(item['itemprice'])
                        finalitems.append({'itemname': itemname, 'itemprice':  f' (${itemprice} ea )', 'itemquantity': int(item['itemquantity'])})
        return finalitems
