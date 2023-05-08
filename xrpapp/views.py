from django.shortcuts import render
import asyncio
import requests
import datetime
import math
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
#crypto
import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from decimal import Decimal
from typing import Union
#XRPL
from xrpl.account import (does_account_exist, get_account_info,
                          get_account_payment_transactions, get_balance,
                          get_next_valid_seq_number)
from xrpl.ledger import get_latest_validated_ledger_sequence
from xrpl.clients import JsonRpcClient
from xrpl.core import keypairs
from xrpl.ledger import get_fee
from xrpl.models import (AccountInfo, AccountLines,
                         Payment,XRP, AccountCurrencies, AccountDelete, 
                         AccountObjects, AccountOffers, BookOffers,
                         CheckCancel, CheckCash, CheckCreate, EscrowCancel,
                         EscrowCreate, EscrowFinish, GatewayBalances,
                         IssuedCurrency, IssuedCurrencyAmount, OfferCancel,
                         OfferCreate, TrustSet)
from xrpl.transaction import (safe_sign_transaction,safe_sign_and_autofill_transaction,
                              send_reliable_submission)
from xrpl.utils import drops_to_xrp, ripple_time_to_datetime, xrp_to_drops
#from Misc import hex_to_symbol, symbol_to_hex
from xrpl.core import keypairs
from xrpl.wallet import generate_faucet_wallet, Wallet
import requests
from django.http import JsonResponse
from django.conf import settings
from xrpl.models.transactions import Payment
from xrpl.utils import xrp_to_drops



url = settings.BASE_URL
key = 'caJwPutlYQeEHGMte2avOzEZvg7grq2y'
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

    def add_transaction(self, confirmation_sender_address, confirmation_recipient_address,confirmation_amount,confirmation_currency1, confirmation_currency2, confirmation_amount1,confirmation_transamount,confirmation_signature): #New
        
        self.transactions.append({'sender_address': confirmation_sender_address,
                                  'recipient_address': confirmation_recipient_address,
                                  'amount': confirmation_amount,
                                  'time': str(datetime.datetime.now()),
                                  'currency1' : confirmation_currency1,
                                  'currency2' : confirmation_currency2,
                                 # 'rate' : rate,
                                  'amount1': confirmation_amount1, 
                                  'transamount' :confirmation_transamount,
                                  'signature' :confirmation_signature                                                           
                                })
        previous_block = self.get_last_block()
        return previous_block['index'] + 1    

# Creating our Blockchain
blockchain = Blockchain()
# Creating an address for the node running our server
node_address = str(uuid4()).replace('-', '')


class Transaction:

    def __init__(self, sender_address, recipient_address, amount, currency1, currency2, amount1,transamount,signature):
        self.sender_address = sender_address
       # self.sender_private_key = sender_private_key
        self.recipient_address = recipient_address
        self.amount = amount
        self.currency1=currency1
        self.currency2=currency2
        self.amount1=amount1
        self.transamount=transamount
        self.signature=signature
       

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
       

client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")

def index(request):
    if request.method=="POST":
        sender_address=request.POST.get('sender_address')
        recipient_address=request.POST.get('recipient_address')
        amount=str(request.POST.get('amount'))
        currency1=request.POST.get('currency1')
        currency2=request.POST.get('currency2')
        res = requests.get(f'{url}/convert?from={currency1}&to={currency2}&amount={amount}&apikey={key}')
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
        # seed = keypairs.generate_seed()
        # public,private = keypairs.derive_keypair(seed)
        print(wallet_info)
        test_wallet = generate_faucet_wallet(client)
        print(test_wallet)
        test_account = test_wallet.classic_address
        transfer_rate = 0.1
        transamount = int(amount1 * transfer_rate + amount1)
        acct_info = AccountInfo(
                     account=test_account,
                     ledger_index="validated",
                     strict=True,
                     )
        response = client.request(acct_info)
        result = response.result
        print("response.status: ", response.status)
        print(json.dumps(response.result, indent=4, sort_keys=True))
        current_validated_ledger = get_latest_validated_ledger_sequence(client)
        test_wallet.sequence = get_next_valid_seq_number(test_wallet.classic_address, client)
        my_tx_payment = Payment(
                        account=test_account,
                        amount=str(transamount),
                        destination=recipient_address
                        )
        print(my_tx_payment)
        # sign the transaction
        my_tx_payment_signed = safe_sign_and_autofill_transaction(my_tx_payment,test_wallet,client)
        print("sign",my_tx_payment_signed.get_hash())
        signature=my_tx_payment_signed.get_hash()
        print("fee",my_tx_payment_signed.fee)
        # submit the transaction
        tx_response = send_reliable_submission(my_tx_payment_signed, client)
        print(tx_response)
        # look up account info
        # send_token_tx = xrpl.models.transactions.Payment(
        #                 account=test_account,
        #                 destination="rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe",
        #                 amount=xrpl.models.amounts.issued_currency_amount.IssuedCurrencyAmount(
        #                 currency=currency2,
        #                 issuer="rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe",
        #                 value=amount1
        #                 ),                 
        #                 send_max = xrpl.models.amounts.issued_currency_amount.IssuedCurrencyAmount(
        #                 currency=currency_code,
        #                 issuer="rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe",
        #                 value=(amount1 * transfer_rate)
        #                 ))
        # print(send_token_tx)                
        context={}
        context={'public':test_account,
                'private': recipient_address,
                'seed':seed, 
                'amount':amount,
                'currency1':currency1,
                'currency2':currency2,
                'amount1':amount1,
                'dropstoxrp':transfer_rate,
                'transamount':transamount,
                'signature':signature
                }
        # balance={}
        # balance=xrptransactions.xrp_balance(wallet_addr=wallet.classic_address) 
        # print(balance)       
        # account_info={}
        # acct_info = AccountInfo(
        #         account=wallet.classic_address,
        #         ledger_index="current",
        #         queue=True,
        #         strict=True,
        #     )
        # response = client.request(acct_info)
        # result = response.result
        # print(json.dumps(result['account_data'], indent=4, sort_keys=True))
        # print(acct_info)
        
        # print(account_info)            
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


def escrow(request):
    if request.method=="POST":
        sender_address=request.POST.get('sender_address')
        recipient_adress=request.POST.get('receiver_address')
        amount=request.POST.get('amount')
        claimdate=datetime.now()
        expiredate=request.POST.get('expiredate')
        
           
        test_wallet = generate_faucet_wallet(client)
        test_account = test_wallet.classic_address
        sender_seed=test_wallet.seed
        recipient_address=request.POST.get('receiver_address')
        acc_info = AccountInfo(account=test_account, ledger_index="validated")
        my_payment=Payment(
                        account=test_account,
                        amount=amount,
                        destination=recipient_adress
                        )
        print(my_payment)
        my_payment_signed = safe_sign_and_autofill_transaction(my_payment,test_wallet,client)
        print("sign",my_payment_signed.get_hash())
        signature=my_payment_signed.get_hash()
        print("fee",my_payment_signed.fee)
        # submit the transaction
        tx_response = send_reliable_submission(my_payment_signed, client)
        response = client.request(acc_info).result
        test_wallet.sequence = get_next_valid_seq_number(test_wallet.classic_address, client)
        sender_wallet = Wallet(seed=sender_seed, sequence=test_wallet.sequence) 
        # cancelafter=datetime.datetime.now()+datetime.timedelta(days=2)
        # cancelafter1=cancelafter.microsecond
        finishafter=datetime.datetime.now()+datetime.timedelta(days=2)
        finishafter1=finishafter.microsecond
        escrowt=EscrowCreate(account=test_account, amount=xrp_to_drops(100), destination="rfuegFTmpDVTdz2teroxrh7qkWfk4wJGEA", finish_after=finishafter1,condition="")
        print(escrowt)
        my_payment1_signed = safe_sign_and_autofill_transaction(escrowt,sender_wallet,client)
        print("sign",my_payment1_signed.get_hash())
        signature=my_payment1_signed.get_hash()
        print("fee",my_payment1_signed.fee)
        #tx_response = send_reliable_submission(my_payment1_signed, client)
        context={'sender_address':sender_address,
                # 'sende_seed':sender_seed,
                'recipient_address':recipient_adress,
                'claimdate': claimdate,
                'expiredate':expiredate}
        return render(request,'view_escrowtransaction.html',context)
    return render(request,'escrow_transaction.html')

def escrowtransaction(request):
    if request.method=="GET":
        sender_address=request.GET.get('sender_address')
        print(sender_address)
        sender_seed= request.GET.get('sender_seed')
        print(sender_seed)
        recipient_address= request.GET.get('recipient_address')
        claimdate= request.GET.get('claimdate')
        expiredate=request.GET.get('expiredate')
        return render(request,'view_escrowtransaction.html')
    else:
        return render(request,'view_escrowtransaction.html')
    return render(request,'view_escrowtransaction.html')    



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
    transamount=request.GET.get('transamount')
    signature=request.GET.get('signature')
    print(sender_address)
    print(recipient_address)
    print(amount)
    print(currency1)
    print(currency2)
    print(amount1)

    transaction = Transaction(sender_address, recipient_address, amount, currency1, currency2, amount1,transamount,signature)
    print(transaction)
    # response = {'transaction': transaction.to_dict(), 'signature': sender_address }
    response={'sender_address':sender_address,
               'recipient_address':recipient_address,
               'amount':amount,
               'currency1':currency1,
               'currency2':currency2,
               'amount1':amount1,
               'transamount':transamount,
               }
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
        confirmation_transamount=request.POST.get('confirmation_transamount')
        confirmation_signature=request.POST.get('confirmation_signature')
        transaction= blockchain.add_transaction(confirmation_sender_address=confirmation_sender_address,confirmation_recipient_address=confirmation_recipient_address,confirmation_amount=confirmation_amount,confirmation_currency1=confirmation_currency1,confirmation_currency2=confirmation_currency2,confirmation_amount1=confirmation_amount1,confirmation_transamount=confirmation_transamount,confirmation_signature=confirmation_signature)
        print("hello",transaction)
        print(index)
        print(confirmation_sender_address,confirmation_recipient_address ,confirmation_amount,confirmation_currency1, confirmation_currency2, confirmation_amount1)
        res= {'confirmation_sender_address':confirmation_sender_address,
              'confirmation_recipient_address':confirmation_recipient_address,
              'confirmation_amount':confirmation_amount,
              'confirmation_currency1':confirmation_currency1,
              'confirmation_currency2':confirmation_currency2,
              'confirmation_amount1':confirmation_amount1,
              'confirmation_transamount':confirmation_transamount,
              'confirmation_signature':confirmation_signature}
        
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


def create_escrow(self,sender_addr: str, sender_seed: str, amount: Union[int, float, Decimal], receiver_addr: str, condition: Union[str, None], claim_date: Union[int, None], expiry_date: Union[int, None]):
        """create an Escrow\n
        You must use one `claim_date` or `expiry_date` unless this will fail"""
        print(1)
        acc_info = AccountInfo(account=sender_addr, ledger_index="validated")
        response = self.client.request(acc_info).result
        sequence = response["account_data"]["Sequence"]
        sender_wallet = Wallet(seed=sender_seed, sequence=sequence)

        create_txn = EscrowCreate(account=sender_addr, amount=xrp_to_drops(amount), destination=receiver_addr, finish_after=claim_date, cancel_after=expiry_date, condition=condition)
        stxn = safe_sign_and_autofill_transaction(create_txn, sender_wallet, self.client)
        stxn_response = send_reliable_submission(stxn, self.client)
        stxn_result = stxn_response.result
        return stxn_result["meta"]["TransactionResult"]

def schedule_xrp(self, sender_addr: str, sender_seed: str, amount: Union[int, float, Decimal], receiver_addr: str, claim_date: int, expiry_date: Union[int, None]) -> str:
        """schedule an Xrp payment
        \n expiry date must be greater than claim date"""
        acc_info = AccountInfo(account=sender_addr, ledger_index="validated")
        response = self.client.request(acc_info).result
        sequence = response["account_data"]["Sequence"]
        sender_wallet = Wallet(seed=sender_seed, sequence=sequence)

        create_txn = EscrowCreate(account=sender_addr, amount=xrp_to_drops(amount), destination=receiver_addr, finish_after=claim_date, cancel_after=expiry_date)
        stxn = safe_sign_and_autofill_transaction(create_txn, sender_wallet, self.client)
        stxn_response = send_reliable_submission(stxn, self.client)
        stxn_result = stxn_response.result
        return stxn_result["meta"]["TransactionResult"]

def account_escrows(self, wallet_addr: str, limit: int = None) -> dict:
        """returns all account escrows, used for returning scheduled payments"""
        escrow_dict = {}
        sent = []
        received = []
        req = AccountObjects(account=wallet_addr, ledger_index="validated", type="escrow", limit=limit)
        response = self.client.request(req)
        result = response.result

        escrows = result["account_objects"]
        for escrow in escrows:
            escrow_data = {}
            if isinstance(escrow["Amount"], str):
                escrow_data["escrow_id"] = escrow["index"]
                escrow_data["sender"] = escrow["Account"]
                escrow_data["receiver"] = escrow["Destination"]
                escrow_data["amount"] = str(drops_to_xrp(escrow["Amount"]))
                if "PreviousTxnID" in escrow:
                    escrow_data["prex_txn_id"] = escrow["PreviousTxnID"] # needed to cancel or complete the escrow
                if "FinishAfter" in escrow:
                    escrow_data["redeem_date"] = str(ripple_time_to_datetime(escrow["FinishAfter"]))
                if "CancelAfter" in escrow:
                    escrow_data["expiry_date"] = str(ripple_time_to_datetime(escrow["CancelAfter"]))
                if "Condition" in escrow:
                    escrow_data["condition"] = escrow["Condition"]

                if escrow_data["sender"] == wallet_addr:
                    sent.append(escrow_data)
                else:
                    received.append(escrow_data)
        escrow_dict["sent"] = sent
        escrow_dict["received"] = received
        return escrow_dict

def cancel_escrow(self, sender_addr: str, sender_seed: str, escrow_creator: str, escrow_seq: str) -> str:
        """cancel an escrow"""
        acc_info = AccountInfo(account=sender_addr, ledger_index="validated")
        response = self.client.request(acc_info).result
        sequence = response["account_data"]["Sequence"]
        sender_wallet = Wallet(seed=sender_seed, sequence=sequence)

        cancel_txn = EscrowCancel(account=sender_addr, owner=escrow_creator, offer_sequence=escrow_seq)
        stxn = safe_sign_and_autofill_transaction(cancel_txn, sender_wallet, self.client)
        stxn_response = send_reliable_submission(stxn, self.client)
        stxn_result = stxn_response.result
        return stxn_result["meta"]["TransactionResult"]

def finish_escrow(self, sender_addr: str, sender_seed: str, escrow_creator: str, escrow_seq: str, condition: Union[str, None], fulfillment: Union[str, None]):
        """complete an escrow"""
        acc_info = AccountInfo(account=sender_addr, ledger_index="validated")
        response = self.client.request(acc_info).result
        sequence = response["account_data"]["Sequence"]
        sender_wallet = Wallet(seed=sender_seed, sequence=sequence)

        finish_txn = EscrowFinish(account=sender_addr, owner=escrow_creator, offer_sequence=escrow_seq, condition=condition, fulfillment=fulfillment)
        stxn = safe_sign_and_autofill_transaction(finish_txn, sender_wallet, self.client)
        stxn_response = send_reliable_submission(stxn, self.client)
        stxn_result = stxn_response.result
        return stxn_result["meta"]["TransactionResult"]

def senderaddress(request):
    if request.method=='POST':
        sender_address=request.POST.get('sender_address')
        amount=request.POST.get('amount')
        print(1)
        test_wallet = generate_faucet_wallet(client)
        print(test_wallet)
        sender_account = test_wallet.classic_address 
        print(sender_account)
        sender_seed=test_wallet.seed
        print(sender_seed)
        public,private = keypairs.derive_keypair(sender_seed)
        context={}
        context={
                'sender_account':sender_account,
                'sender_seed':sender_seed,
                'public':public,
                'private':private,
                'amount': amount
            }
        print(context)    
        return(request,'sendxrp.html',context)
    else:
        return render(request, 'senderaddress.html')    
   

def sendxrp(request):
    
        test_wallet=generate_faucet_wallet(client)
        test_account=test_wallet.classic_address
        test_seed=test_wallet.seed
        acct_info = AccountInfo(
                     account=test_account,
                     ledger_index="validated",
                     strict=True,
                     )
        response = client.request(acct_info)
        result = response.result
        print("response.status: ", response.status)
        print(json.dumps(response.result, indent=4, sort_keys=True))
        xrpsend = Payment(
            account=test_account,
            destination="",
            amount=xrp_to_drops(10)
            )
        print(xrpsend)    
        my_xrpsend_payment_signed = safe_sign_and_autofill_transaction(xrpsend,test_wallet,client)
        print(my_xrpsend_payment_signed)
        print("sign",my_xrpsend_payment_signed.get_hash())
        signature=my_xrpsend_payment_signed.get_hash()
        print("fee",my_xrpsend_payment_signed.fee)
        # submit the transaction
        xrpsend_response = send_reliable_submission(my_xrpsend_payment_signed, client)    

        print(xrpsend_response)    
        context={
                'sender_address':test_account,
                'sender_seed':test_seed,
                'amount':10
                }
        return render(request, 'sendxrp.html',context)
    # else:
    #     return render(request, 'sendxrp.html')


    #     #tx_info = send_xrp(sender_addr=test_account, sender_seed=test_seed, receiver_addr="rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe", amount=10)
      



