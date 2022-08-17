from django.shortcuts import render
import requests
import datetime
import hashlib
from decimal import Decimal
import json
from uuid import uuid4
import socket
from urllib.parse import urlparse
from django.http import JsonResponse, HttpResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

from collections import OrderedDict

import binascii

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from xrpl.clients import JsonRpcClient
from xrpl.core import keypairs
from xrpl.wallet import generate_faucet_wallet, Wallet
import requests
from django.http import JsonResponse
from django.conf import settings

url = settings.BASE_URL
key = 'vj54zTtJiZiTDPaUFB1yi9qMrUNGIF0Y'
class Blockchain:

    def __init__(self):

        self.chain = []
        self.transactions = [] 
        self.create_block(nonce = 1, previous_hash = '0')
        self.nodes = set()

    def create_block(self, nonce, previous_hash):
        block = {'index': len(self.chain),
                 'timestamp': str(datetime.datetime.now()),
                 'nonce': nonce,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions #New
                }
        self.transactions = [] #New
        self.chain.append(block)
        return block

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def proof_of_work(self,previous_nonce):
        new_nonce = 1
        check_nonce = False
        while check_nonce is False:
            hash_operation = hashlib.sha256(str(new_nonce**2 - previous_nonce**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_nonce = True
            else:
                new_nonce += 1
        return new_nonce  

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_nonce = previous_block['nonce']
            nonce = block['nonce']
            hash_operation = hashlib.sha256(str(nonce**2 - previous_nonce**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    def add_node(self, address): #New
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def get_last_block(self):
        return self.chain[-1]    

    def replace_chain(self): #New
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://127.0.0.1:8000/fullchain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

    def add_transaction(self, confirmation_sender_address, confirmation_recipient_address,confirmation_amount,confirmation_currency1, confirmation_currency2, confirmation_amount1): #New
        
        self.transactions.append({'sender_address': confirmation_sender_address,
                                  'recipient_address': confirmation_recipient_address,
                                  'amount': confirmation_amount,
                                  'time': str(datetime.datetime.now()),
                                  'currency1' : confirmation_currency1,
                                  'currency2' : confirmation_currency2,
                                 # 'rate' : rate,
                                  'amount1': confirmation_amount1                                                                   
                                })
        previous_block = self.get_last_block()
        return previous_block['index'] + 1    

# Creating our Blockchain
blockchain = Blockchain()
# Creating an address for the node running our server
node_address = str(uuid4()).replace('-', '')


class Transaction:

    def __init__(self, sender_address, recipient_address, amount, currency1, currency2, amount1):
        self.sender_address = sender_address
       # self.sender_private_key = sender_private_key
        self.recipient_address = recipient_address
        self.amount = amount
        self.currency1=currency1
        self.currency2=currency2
        self.amount1=amount1
       

    def __getattr__(self, attr):
        return self.data[attr]

    def to_dict(self):
        return OrderedDict({'sender_address': self.sender_address,
                            'recipient_address': self.recipient_address,
                            'amount': self.amount,
                            'currency1': self.currency1,
                            'currency2':self.currency2,
                            'amount1':self.amount1})

    def sign_transaction(self):
        """
        Sign transaction with private key
        """
        private_key = RSA.importKey(binascii.unhexlify(self.sender_private_key))
        signer = PKCS1_v1_5.new(private_key)
        h = SHA.new(str(self.to_dict()).encode('utf8'))
        return binascii.hexlify(signer.sign(h)).decode('ascii')
        # cold_wallet = generate_faucet_wallet(client, debug=True)
        # hot_wallet = generate_faucet_wallet(client, debug=True)


        # # Configure issuer (cold address) settings -------------------------------------
        # cold_settings_tx = xrpl.models.transactions.AccountSet(
        #     account=cold_wallet.classic_address,
        #     transfer_rate=0,
        #     tick_size=5,
        #     domain=bytes.hex("example.com".encode("ASCII")),
        #     set_flag=xrpl.models.transactions.AccountSetFlag.ASF_DEFAULT_RIPPLE,
        # )
        # cst_prepared = xrpl.transaction.safe_sign_and_autofill_transaction(
        #     transaction=cold_settings_tx,
        #     wallet=cold_wallet,
        #     client=client,
        # )
        # print("Sending cold address AccountSet transaction...")
        # response = xrpl.transaction.send_reliable_submission(cst_prepared, client)
        # print(response)


        # # Configure hot address settings -----------------------------------------------
        # hot_settings_tx = xrpl.models.transactions.AccountSet(
        #     account=hot_wallet.classic_address,
        #     set_flag=xrpl.models.transactions.AccountSetFlag.ASF_REQUIRE_AUTH,
        # )
        # hst_prepared = xrpl.transaction.safe_sign_and_autofill_transaction(
        #     transaction=hot_settings_tx,
        #     wallet=hot_wallet,
        #     client=client,
        # )
        # print("Sending hot address AccountSet transaction...")
        # response = xrpl.transaction.send_reliable_submission(hst_prepared, client)
        # print(response)


        # # Create trust line from hot to cold address -----------------------------------
        # currency_code = "FOO"
        # trust_set_tx = xrpl.models.transactions.TrustSet(
        #     account=hot_wallet.classic_address,
        #     limit_amount=xrpl.models.amounts.issued_currency_amount.IssuedCurrencyAmount(
        #         currency=currency_code,
        #         issuer=cold_wallet.classic_address,
        #         value="10000000000", # Large limit, arbitrarily chosen
        #     )
        # )
        # ts_prepared = xrpl.transaction.safe_sign_and_autofill_transaction(
        #     transaction=trust_set_tx,
        #     wallet=hot_wallet,
        #     client=client,
        # )
        # print("Creating trust line from hot address to issuer...")
        # response = xrpl.transaction.send_reliable_submission(ts_prepared, client)
        # print(response)


        # # Send token -------------------------------------------------------------------
        # issue_quantity = "3840"
        # send_token_tx = xrpl.models.transactions.Payment(
        #     account=cold_wallet.classic_address,
        #     destination=hot_wallet.classic_address,
        #     amount=xrpl.models.amounts.issued_currency_amount.IssuedCurrencyAmount(
        #         currency=currency_code,
        #         issuer=cold_wallet.classic_address,
        #         value=issue_quantity
        #     )
        # )
        # pay_prepared = xrpl.transaction.safe_sign_and_autofill_transaction(
        #     transaction=send_token_tx,
        #     wallet=cold_wallet,
        #     client=client,
        # )
        # print(f"Sending {issue_quantity} {currency_code} to {hot_wallet.classic_address}...")
        # response = xrpl.transaction.send_reliable_submission(pay_prepared, client)
        # print(response)


        # # Check balances ---------------------------------------------------------------
        # print("Getting hot address balances...")
        # response = client.request(xrpl.models.requests.AccountLines(
        #     account=hot_wallet.classic_address,
        #     ledger_index="validated",
        # ))
        # print(response)

        # print("Getting cold address balances...")
        # response = client.request(xrpl.models.requests.GatewayBalances(
        #     account=cold_wallet.classic_address,
        #     ledger_index="validated",
        #     hotwallet=[hot_wallet.classic_address]
        # ))
        # print(response)

client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")

def index(request):
    if request.method=="POST":
        sender_address=request.POST.get('sender_address')
        amount=request.POST.get('amount')
        currency1=request.POST.get('currency1')
        currency2=request.POST.get('currency2')
        res = requests.get(f'{url}/convert?from={currency1}&to={currency2}&amount={amount}&apikey={key}')
        print(res)
        status_code = res.status_code
        print(status_code)
        data = res.json()
        print(data)
        rate = data['info']['quote']
        amount1 = data['result']
        wallet_info = {}
        wallet = Wallet.create()
        seed = wallet.seed
        public, private = keypairs.derive_keypair(seed)
        #wallet_info["name"] = name
        wallet_info["classic_address"] = wallet.classic_address
        wallet_info["private_key"] = private
        wallet_info["public_key"] = public
        wallet_info["seed"] = seed
        seed = keypairs.generate_seed()
        public,private = keypairs.derive_keypair(seed)
        test_account = keypairs.derive_classic_address(public)
        context={}
        context={'public':public,
                'private': private,
                'seed':seed, 
                'amount':amount,
                'currency1':currency1,
                'currency2':currency2,
                'amount1':amount1}
        print('name',name)        
        print('classic_address',wallet.classic_address)
        print('public',public)  
        print('private',private)   
        print('seed',seed)    
        return render(request,'make_transactions.html',context)
    else:
        return render(request, 'index.html')


def maketransactions(request):

    return render(request, 'make_transactions.html')


def viewtransactions(request):
    return render(request,'view_transactions.html')


def newwallet(request):
    if request.method=="POST":
        sender_address=request.POST(sender_address)
        amount=request.POST(amount)
        currency1=request.POST(currency1)
        currency2=request.POST(currency2)
        res = requests.get(f'{url}/convert?from={currency1}&to={currency2}&amount={amount}&apikey={key}')
        print(res)
        status_code = res.status_code
        print(status_code)
        data = res.json()
        print(data)
        rate = data['info']['quote']
        amount1 = data['result']
        wallet_info = {}
        wallet = Wallet.create()
        seed = wallet.seed
        public, private = keypairs.derive_keypair(seed)
        wallet_info["name"] = name
        wallet_info["classic_address"] = wallet.classic_address
        wallet_info["private_key"] = private
        wallet_info["public_key"] = public
        wallet_info["seed"] = seed
        seed = keypairs.generate_seed()
        public,private = keypairs.derive_keypair(seed)
        test_account = keypairs.derive_classic_address(public)
        context={}
        context={'public':public,
                'private': private,
                'seed':seed, 
                'amount':amount,
                'currency1':currency1,
                'currency2':currency2,
                'amoun1':amount1}
        print('name',name)
        print('classic_address',wallet.classic_address)
        print('public',public)  
        print('private',private)   
        print('seed',seed)    
        return render(request,'make_transactions.html',context)
        

	

def generatetransactions(request):
    
    sender_address = request.GET.get('sender_address')
    #sender_private_key = request.POST.get('sender_private_key')
    recipient_address = request.GET.get('recipient_address')
    amount = request.GET.get('amount')
    currency1 = request.GET.get('currency1')
    currency2 = request.GET.get('currency2')
    amount1= request.GET.get('amount1')
    print(sender_address)
    print(recipient_address)
    print(amount)
    print(currency1)
    print(currency2)
    print(amount1)

    transaction = Transaction(sender_address, recipient_address, amount, currency1, currency2, amount1)
    print(transaction)
    # response = {'transaction': transaction.to_dict(), 'signature': sender_address }
    response={'sender_address':sender_address,
               'recipient_address':recipient_address,
               'amount':amount,
               'currency1':currency1,
               'currency2':currency2,
               'amount1':amount1}
    print("a",response)
    return JsonResponse(response)
        
        
      
   
def newtransaction(request):
    if request.method=="POST":
        confirmation_sender_address = request.POST.get('confirmation_sender_address')
        confirmation_recipient_address = request.POST.get('confirmation_recipient_address')
        confirmation_amount = request.POST.get('confirmation_amount')
        confirmation_currency1 = request.POST.get('confirmation_currency1')
        confirmation_currency2 = request.POST.get('confirmation_currency2')
        confirmation_amount1=request.POST.get('confirmation_amount1')
        transaction= blockchain.add_transaction(confirmation_sender_address=confirmation_sender_address,confirmation_recipient_address=confirmation_recipient_address,confirmation_amount=confirmation_amount,confirmation_currency1=confirmation_currency1,confirmation_currency2=confirmation_currency2,confirmation_amount1=confirmation_amount1)
        print("hello",transaction)
        print(index)
        print(confirmation_sender_address,confirmation_recipient_address ,confirmation_amount,confirmation_currency1, confirmation_currency2, confirmation_amount1)
        res= {'confirmation_sender_address':confirmation_sender_address,
                     'confirmation_recipient_address':confirmation_recipient_address,
                     'confirmation_amount':confirmation_amount,
                     'confirmation_currency1':confirmation_currency1,
                     'confirmation_currency2':confirmation_currency2,
                     'confirmation_amount1':confirmation_amount1}
        
        return JsonResponse(res)
        

def getransactions(request):
    #Get transactions from transactions pool
    transactions = blockchain.transactions

    response = {'transactions': transactions}
    return JsonResponse(response)

def fullchain(request):
    response = {
        'chain': blockchain.chain,
        #'transactions': blockchain.transactions,
        'length': len(blockchain.chain),
     }
    print(response)
    return JsonResponse(response)    


def mine(request):
    if request.method == 'GET':
        previous_block = blockchain.get_last_block()
        previous_nonce = previous_block['nonce']
        nonce = blockchain.proof_of_work(previous_nonce)
        previous_hash = blockchain.hash(previous_block)
        #blockchain.add_transaction(sender = root_node, receiver = node_address, amount = 1.15, time=str(datetime.datetime.now()), currency1="USD", currency2="VND")
        block = blockchain.create_block(nonce, previous_hash)
        res = {'message': 'Congratulations, you just mined a block!',
                    'index': block['index'],
                    'timestamp': block['timestamp'],
                    'nonce': block['nonce'],
                    'previous_hash': block['previous_hash'],
                    'transactions': block['transactions']}
        return JsonResponse(res)   


