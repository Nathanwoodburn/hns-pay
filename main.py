from flask import Flask, make_response, redirect, request, jsonify, render_template, send_from_directory
import os
import dotenv
import requests
import datetime
import json
import payments
import accounts
import threading

app = Flask(__name__)
dotenv.load_dotenv()

# Exchange cache
exchange = {
    'timestamp': 0,
    'rate': 0
}


#Assets routes
@app.route('/assets/<path:path>')
def send_report(path):
    return send_from_directory('templates/assets', path)

@app.route('/sitemap')
@app.route('/sitemap.xml')
def sitemap():
    # Remove all .html from sitemap
    with open('templates/sitemap.xml') as file:
        sitemap = file.read()

    sitemap = sitemap.replace('.html', '')
    return make_response(sitemap, 200, {'Content-Type': 'application/xml'})

@app.route('/favicon.png')
def faviconPNG():
    return send_from_directory('templates/assets/img', 'favicon.png')

@app.route('/.well-known/wallets/<path:path>')
def wallet(path):
    return send_from_directory('templates/.well-known/wallets', path, mimetype='text/plain')


#region Account
@app.route('/register', methods=['POST'])
def register():
    data = request.form
    email = data['email']
    password = data['password']
    if not email or not password:
        return render_template('register.html', error='Email and password are required')
    if not accounts.createAccount(email, password):
        return render_template('register.html', error='Account already exists')
    
    cookie = accounts.createCookie(email)
    response = make_response(redirect('/account'))
    response.set_cookie('session', cookie)
    return response

@app.route('/login', methods=['POST'])
def login():
    data = request.form
    email = data['email']
    password = data['password']
    if not email or not password:
        return render_template('login.html', error='Email and password are required')
    if not accounts.login(email, password):
        return render_template('login.html', error='Invalid email or password')

    cookie = accounts.createCookie(email)
    response = make_response(redirect('/account'))
    response.set_cookie('session', cookie)
    return response

@app.route('/account')
def account():
    cookie = request.cookies.get('session')
    if not cookie:
        return redirect('/login')
    if not accounts.getCookie(cookie):
        return redirect('/login')
    account = accounts.getCookie(cookie)
    address = accounts.getAccountAddress(account)
    name = accounts.getAccountDisplayName(account)
    link = accounts.getAccountLink(account)
    webhook = accounts.getAccountWebhook(account)


    userPayments = payments.getUserPayments(account)
    userPayments = [payment for payment in userPayments if payment['status'] == 'Confirmed']
    paymentHTML = '<ul class="list-group" style="max-width: 700px;margin: auto;">'
    for payment in userPayments:
        paymentHTML += f'<li class="list-group-item"><span>{payment["amount"]} HNS'
        if payment['data']:
            paymentHTML += f' - {payment["data"]}'
        paymentHTML += '</span></li>'

    paymentHTML += '</ul>'


    return render_template('account.html', account=account, address=address, link=link, name=name, webhook=webhook, payments=paymentHTML)

@app.route('/account/edit', methods=['POST'])
def payout():
    cookie = request.cookies.get('session')
    if not cookie:
        return redirect('/login')
    if not accounts.getCookie(cookie):
        return redirect('/login')
    account = accounts.getCookie(cookie)
    data = request.form
    address = data['payout']
    link = data['link']
    name = data['name']
    accounts.setAccountAddress(account, address)
    accounts.setAccountLink(account, link)
    accounts.setAccountDisplayName(account, name)

    return redirect('/account')

@app.route('/account/webhook', methods=['POST'])
def webhook():
    cookie = request.cookies.get('session')
    if not cookie:
        return redirect('/login')
    if not accounts.getCookie(cookie):
        return redirect('/login')
    account = accounts.getCookie(cookie)
    data = request.form
    url = data['url']
    accounts.setAccountWebhook(account, url)
    return redirect('/account')
#endregion

# Payment routes
@app.route('/p/<path:path>')
def payment(path):
    year = datetime.datetime.now().year
    account = accounts.getAccountFromLink(path)
    if not account:
        return redirect('/?error=Invalid%20link')
    
    display_name = accounts.getAccountDisplayName(account)
    amount = request.args.get('amount')
    data = request.args.get('data')
    redirectLink = request.args.get('redirect')
    if not data:
        data = ''

    if not amount:
        return render_template('payment.html',year=year,account=account,name=display_name,readonly=False,data=data)
    
    address = payments.generate_payment(account, amount, data)
    if not redirectLink:
        redirectLink = ""
    else:
        redirectLink = f'<a class="btn btn-primary" role="button" href="{redirectLink}">Continue</a>'
    return render_template('payment2.html',year=year,account=account,name=display_name,amount=amount,data=data,address=address,redirect=redirectLink)

@app.route('/p/<path:path>', methods=['POST'])
def payment_post(path):
    year = datetime.datetime.now().year
    account = accounts.getAccountFromLink(path)
    if not account:
        return redirect('/?error=Invalid%20link')
    
    display_name = accounts.getAccountDisplayName(account)

    amount = request.form['amount']
    data = request.form['data']
    if not data:
        data = ''
    print(data)
    address = payments.generate_payment(account, amount, data)
    return render_template('payment2.html',year=year,account=account,name=display_name,amount=amount,data=data,address=address)

# Main routes
@app.route('/')
def index():
    year = datetime.datetime.now().year
    return render_template('index.html',year=year)

@app.route('/<path:path>')
def catch_all(path):
    year = datetime.datetime.now().year
    # If file exists, load it
    if os.path.isfile('templates/' + path):
        return render_template(path, year=year)
    
    # Try with .html
    if os.path.isfile('templates/' + path + '.html'):
        return render_template(path + '.html', year=year)

    return redirect('/')

# 404 catch all
@app.errorhandler(404)
def not_found(e):
    return redirect('/')

def check_payments():
    payments.check_payments()

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')