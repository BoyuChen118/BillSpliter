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
    
    # turn array of [membername, memberemail] to [membername, memberemail, displaytext, displaytextcolor]
    def attach_amount_owe(self, groupinfo):
        try:
            owes = self.db.storage.get_collection('users').find_one({'_id': self.email})['owes']
        except Exception:
            owes = []
        for i in range(len(groupinfo)):
            memberinfo = groupinfo[i]
            
            try:
                oweuser = self.db.storage.get_collection('users').find_one({'_id': memberinfo[1]})['owes']
            except Exception:
                oweuser = []
                
            email = Util().encodeEmail(memberinfo[1])
            useremail = Util().encodeEmail(self.email)
            amountowe = 0
            textcolor = ''
            text = ''
            if useremail in oweuser:  # some other user owes the logged in user
                amountowe = oweuser[useremail]
                if int(amountowe) != 0:
                    text = f'Owes you ${amountowe}'
                    textcolor = 'green'
            elif email in owes:  # logged in user owes some other user
                amountowe = owes[email]
                if int(amountowe) != 0:
                    text = f'You owe this user ${amountowe}'
                    textcolor = 'red'
            groupinfo[i].append(text)
            groupinfo[i].append(textcolor)
        return
                
            

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
            if pexpense['expensename'] == expensename:
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
        # check if everyone including payor submitted the survey
        if surveyLength == len(self.get_group_members(groupcode)):
            # update status of survey to archivable
            self.db.storage.get_collection(
            'groups').find_one_and_update({'_id': groupcode}, {'$set': {f'pendingexpenses.{pexpenseIndex}.actionrequired': 'Everyone Completed Survey (click me)'}})
            
            
        # generate transaction report based on all surveys
        expensesheet = self.calculate_expenses(self.get_pending_expenses(groupcode)[pexpenseIndex])
        self.db.storage.get_collection(
        'groups').find_one_and_update({'_id': groupcode}, {'$set': {f'pendingexpenses.{pexpenseIndex}.expensesheet': expensesheet}})
                
    # check if current user has finished the survey for expense[expenseIndex]
    def check_finished_survey(self, groupcode, expenseIndex: int):
        pexpense = self.get_pending_expenses(groupcode)[expenseIndex]
        if 'surveys' not in pexpense:
            return False
        return Util().encodeEmail(self.email) in pexpense['surveys']

    # retreive submitted surveys in the form of {username: [[itemname*quantity], amount_owe_to_payer, email]}
    def get_survey_data(self, groupcode, expensename):
        pexpenses = self.get_pending_expenses(groupcode)
        memberinfo = {member[1]:member[0] for member in self.get_group_members(groupcode)}
        surveydata = {}
        for pexpense in pexpenses:
            if pexpense['expensename'] == expensename:
                surveys = pexpense['surveys']
                expensesheet = pexpense['expensesheet']   # expensesheet are simply how much each person owes payer (people who submitted empty survey aren't in expensesheet)
                for email, data in surveys.items():
                    username = memberinfo[Util().decodeEmail(email)]
                    surveydata[username] = [[], 0, '']
                    for itemname, quantity in data['items'].items():
                        surveydata[username][0].append(f"{itemname}*{quantity}")
                    surveydata[username][2] = Util().decodeEmail(email)
                for email, amount in (dict)(expensesheet).items():
                    username = memberinfo[email]
                    if username not in surveydata:
                        surveydata = [[], 0, email]
                    surveydata[username][1] = amount
        return surveydata
                

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
                pricepershare = (totalprice / totalshares) if totalshares > int(item['itemquantity']) else float(item['itemprice'])  # only use "share" price when it's a share item otherwise just use itemprice
                for email, shares in tempsheet.items():
                    if email not in expensesheet:
                        expensesheet[email] = 0
                    expensesheet[email] += shares * pricepershare
            else: # even split
                membercount = len(surveys.items())
                for email in surveys.keys():
                    email = Util().decodeEmail(email)
                    if email not in expensesheet:
                        expensesheet[email] = 0
                    expensesheet[email] += totalprice / membercount
                    
                
        return expensesheet
    
    # triggered when payer wants to resolve the expense, the algorithm recalculates how much each person owe payer taken into account the new expense
    def resolve_expense(self, surveydata, groupcode, expensename):
        # survedata format: {username: [[itemname*quantity], amount_owe_to_payer, email]}
        # 1. check if payer owes debter if yes then subtract that amount by this expense, any negative turns into amount owed to payer by debter
        # 2. do the above step for every debter. caution: ignore amount owed to self (in other words ignore when payer == debter)
        # 3. delete the pending expense and add to ledger
        data = {v[2]:v[1] for v in surveydata.values()}
        payeremail = self.email
        payer = self.db.storage.get_collection('users').find_one({'_id':payeremail})
        for debteremail, amount in data.items():
            if debteremail != payeremail:
                # check if payer owes debter
                if 'owes' in payer and Util().encodeEmail(debteremail) in payer['owes']:
                    finalamount  = payer['owes'][Util().encodeEmail(debteremail)] - amount
                    if finalamount < 0:  # debter now owes payor, payor no longer owes debter
                        self.db.storage.get_collection('users').find_one_and_update({'_id': debteremail}, {'$set': {f'owes.{Util().encodeEmail(payeremail)}': abs(finalamount)}})
                        self.db.storage.get_collection('users').find_one_and_update({'_id': payeremail}, {'$unset': {f'owes.{Util().encodeEmail(debteremail)}': 0}})
                    else: # payer still owes debter but just a lesser amount
                        self.db.storage.get_collection('users').find_one_and_update({'_id': payeremail}, {'$set': {f'owes.{Util().encodeEmail(debteremail)}': finalamount}})
                else: # debter owes payer already or they don't have any interactions yet
                    debter = self.db.storage.get_collection('users').find_one({'_id': debteremail})
                    originalamount = 0
                    if 'owes' in debter and Util().encodeEmail(payeremail) in debter['owes']:
                        originalamount = debter['owes'][Util().encodeEmail(payeremail)]
                    print(f"original amount is {originalamount}")
                    self.db.storage.get_collection('users').find_one_and_update({'_id': debteremail}, {'$set': {f'owes.{Util().encodeEmail(payeremail)}': originalamount+amount}})
        
        # delete pending expense
        self.db.storage.get_collection(
            'groups').find_one_and_update({'_id': groupcode}, {'$pull': {f"pendingexpenses": {"expensename": expensename}}})
        
        
        


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
            if 'Wait' in p['actionrequired'] and  not auth.check_finished_survey(groupcode, i):  # incomplete survey
                p['actionrequired'] = 'Pending Survey (click me)'
                p['color'] = 'yellow'
                continue
            elif auth.check_finished_survey(groupcode, i) :  # completed survey
                if p['email'] != currentemail: # check if its other user (current user will just have wait for surveys displayed)
                    p['actionrequired'] = 'Survey Completed!'
                    p['color'] = 'green'
                    continue
                
            # pexenpse if owned by current logged in user
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
                for item in expense['items']:  # return both evenly split and unevenly split items
                        itemname = item['itemname'] if item['itemquantity'] == 1 else f"{item['itemname']} *{item['itemquantity']}  "
                        itemprice = float(item['itemprice'])
                        finalitems.append({'itemname': itemname, 'itemprice':  f' (${itemprice} ea )', 'itemquantity': int(item['itemquantity']), 'itemsplitmode': item['itemsplitmode']})
        return finalitems
