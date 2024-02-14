import json
import os
import requests
import bcrypt
import random

if not os.path.exists('data/accounts.json'):
    with open('data/accounts.json', 'w') as f:
        json.dump({}, f, indent=4)

cookies = {}


def createAccount(email,password):
    # Create an account
    if getAccount(email):
       return False
    accounts = getAccounts()
    accounts[email] = {
        "email": email,
        "password": hashPassword(password)
    }
    with open('data/accounts.json', 'w') as f:
        json.dump(accounts, f, indent=4)
    return True
    
def getAccountFromLink(link):
    # Get an account from a link
    with open('data/accounts.json', 'r') as f:
        accounts = json.load(f)
    for email in accounts:
        if 'link' in accounts[email] and accounts[email]['link'] == link:
            return email
    return False


def getAccount(email):
    # Get an account
    with open('data/accounts.json', 'r') as f:
        accounts = json.load(f)
    if email in accounts:
        return accounts[email]
    else:
        return False
    
def getAccountAddress(email):
    # Get an account address
    account = getAccount(email)
    if not account:
        return False
    if 'address' in account:
        return account['address']
    else:
        return ''
    
def getAccountLink(email):
    # Get an account link
    account = getAccount(email)
    if not account:
        return False
    if 'link' in account:
        return account['link']
    else:
        return ''
    
def getAccountDisplayName(email):
    # Get an account display name
    account = getAccount(email)
    if not account:
        return False
    if 'displayName' in account:
        return account['displayName']
    else:
        return ''
    
def getAccountWebhook(email):
    # Get an account webhook
    account = getAccount(email)
    if not account:
        return False
    if 'webhook' in account:
        return account['webhook']
    else:
        return ''

def setAccountAddress(email,address):
    # Set an account address
    accounts = getAccounts()
    accounts[email]['address'] = address
    with open('data/accounts.json', 'w') as f:
        json.dump(accounts, f, indent=4)
    return True

def setAccountLink(email,link):
    # Set an account link
    accounts = getAccounts()
    accounts[email]['link'] = link
    with open('data/accounts.json', 'w') as f:
        json.dump(accounts, f, indent=4)
    return True

def setAccountDisplayName(email,displayName):
    # Set an account display name
    accounts = getAccounts()
    accounts[email]['displayName'] = displayName
    with open('data/accounts.json', 'w') as f:
        json.dump(accounts, f, indent=4)
    return True
    
def setAccountWebhook(email,webhook):
    # Set an account webhook
    accounts = getAccounts()
    accounts[email]['webhook'] = webhook
    with open('data/accounts.json', 'w') as f:
        json.dump(accounts, f, indent=4)
    return True

def login(email,password):
    # Login
    account = getAccount(email)
    if not account:
        return False
    if checkPassword(email, password):
        return True
    else:
        return False
    
def getAccounts():
    # Get all accounts
    with open('data/accounts.json', 'r') as f:
        accounts = json.load(f)
    return accounts

def createCookie(email):
    global cookies
    # Create a cookie
    cookie = str(random.randint(0,2**64))
    cookies[cookie] = email
    return cookie

def getCookie(cookie):
    # Get a cookie
    if cookie in cookies:
        return cookies[cookie]
    else:
        return False


def hashPassword(password):
    # Hash a password
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def checkPassword(email,password):
    # Check a password
    account = getAccount(email)
    if not account:
        return False
    if bcrypt.checkpw(password.encode('utf-8'), account['password'].encode('utf-8')):
        return True
    else:
        return False