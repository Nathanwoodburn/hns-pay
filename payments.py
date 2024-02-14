import json
import os
import requests
import dotenv
import accounts

dotenv.load_dotenv()

HSD_IP = os.getenv('HSD_IP')
HSD_API_KEY = os.getenv('HSD_API_KEY')
WALLET = os.getenv('WALLET')


if not os.path.exists('data/addresses.json'):
    with open('data/addresses.json', 'w') as f:
        json.dump([], f, indent=4)


def generate_payment(email, amount, data):
    # Generate a payment
    with open('data/addresses.json', 'r') as f:
        addresses = json.load(f)
    address = ''
    validAddress = False
    while not validAddress:
        address = generateAddress()
        validAddress = True
        for a in addresses:
            if a["address"] == address:
                validAddress = False

    addresses.append({
        "address": address,
        "email": email,
        "amount": amount,
        "data": data,
        "status": "Pending"
    })
    with open('data/addresses.json', 'w') as f:
        json.dump(addresses, f, indent=4)
    return address
    
    


def check_payments():
    # Get all txs
    with open('data/addresses.json', 'r') as f:
        addresses = json.load(f)
    
    # Select the wallet
    url = f"http://x:{HSD_API_KEY}@{HSD_IP}:12039"
    data = {
        "method": "selectwallet",
        "params": [WALLET]
    }
    resp = requests.post(url, json=data)
    if resp.status_code != 200:
        print(resp.text)
        return False
    # Get last 20 transactions
    data = {
        "method": "listtransactions",
        "params": ["default", 20]
    }
    
    resp = requests.post(url, json=data)
    if resp.status_code != 200:
        print(resp.text)
        return False
    txs = resp.json()
    if txs['error'] != None:
        print(txs['error'])
        return False
    for tx in txs['result']:
        if tx['confirmations'] < 1:
            continue
        for address in addresses:
            if tx['address'] == address['address']:
                if 'hashes' in address:
                    if tx['txid'] in address['hashes']:
                        continue                    
                    address['hashes'].append(tx['txid'])

                address['hashes'] = [tx['txid']]
                address['status'] = 'Confirmed'
                finalise_payment(address,tx)

    with open('data/addresses.json', 'w') as f:
        json.dump(addresses, f, indent=4)
    return True
    
                    
    
def generateAddress():
    # Generate an address
    url = f"http://x:{HSD_API_KEY}@{HSD_IP}:12039/wallet/{WALLET}/address"
    data = '{"account":"default"}'
    resp = requests.post(url, data=data)
    if resp.status_code != 200:
        print(resp.text)
        return False
    print("INDEX: ", resp.json()["index"])
    return resp.json()["address"]
    

def getUserPayments(email):
    # Get all payments for a user
    with open('data/addresses.json', 'r') as f:
        addresses = json.load(f)
    userPayments = []
    for address in addresses:
        if address['email'] == email:
            userPayments.append(address)
    return userPayments


def finalise_payment(payment,tx):
    # Send webhook
    print("Finalising payment")
    print(payment)
    print(tx)
    email = payment['email']
    payout = accounts.getAccountAddress(email)


    # Unlock wallet if password is set
    password = os.getenv('WALLET_PASS')
    if password:
        url = f"http://x:{HSD_API_KEY}@{HSD_IP}:12039/wallet/{WALLET}/unlock"
        data = {
            "passphrase": password,
        }
        resp = requests.post(url, json=data)
        if resp.status_code != 200:
            print(resp.text)

    # Send payout
    url = f"http://x:{HSD_API_KEY}@{HSD_IP}:12039"
    data = {
        "method": "sendtoaddress",
        "params": [payout, tx['amount'],"","" ,True]
    }
    resp = requests.post(url, json=data)
    if resp.status_code != 200:
        print(resp.text)
    
    txHash = resp.json()['result']
    isEqual = tx['amount'] == payment['amount']

    # Send global webhook
    globalWebhook = os.getenv('GLOBAL_WEBHOOK')
    if globalWebhook:
        data = {
            "email": email,
            "payout": payout,
            "amount": tx['amount'],
            "data": payment['data'],
            "tx": txHash,
            "isEqual": isEqual
        }
        resp = requests.post(globalWebhook, json=data)
        if resp.status_code != 200:
            print(resp.text)

    webhook = accounts.getAccountWebhook(email)
    if webhook:
        data = {
            "amount": tx['amount'],
            "data": payment['data'],
            "tx": txHash,
            "isEqual": isEqual
        }
        resp = requests.post(webhook, json=data)
        if resp.status_code != 200:
            print(resp.text)

    return True