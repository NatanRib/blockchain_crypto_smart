import datetime
import json
import hashlib
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse
import sys

#constants
valid_hash_start = '0000'

class Blockchain():
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'previous_hash': previous_hash,
            'proof': proof,
            'transactions': self.transactions
        }
        self.chain.append(block)
        self.transactions = []
        return block
    
    def get_previous_block(self):
        previous_block = self.chain[len(self.chain) - 1]
        return previous_block

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = self.get_operation_hash(new_proof, previous_proof)
            if(self.is_valid_hash(hash_operation)):
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def get_operation_hash(self, proof, previous_proof):
        hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
        return hash_operation

    def is_valid_hash(self, hash):
        return hash[:4] == valid_hash_start

    def get_block_hash(self, block):
        json_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(json_block).hexdigest()
    
    def is_valid_block_chain(self, chain):
        previous_block = chain[0]
        actual_block_index = 1
        while actual_block_index < len(chain):
            actual_block = chain[actual_block_index]
            if(actual_block['previous_hash'] != self.get_block_hash(previous_block)):
                return False
            previous_proof = previous_block['proof']
            actual_proof = actual_block['proof']
            actual_hash = self.get_operation_hash(actual_proof, previous_proof)
            if(not self.is_valid_hash(actual_hash)):
                return False
            previous_block = actual_block
            actual_block_index += 1
        return True

    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({
            sender: sender,
            receiver: receiver,
            amount: amount
        })
        return self.get_previous_block()['index'] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address).netloc
        self.nodes.add(parsed_url)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_lenght = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if(response.status_code != 200): return
            length = response.json()[length]
            chain = response.json()[chain]
            if(length > max_lenght and self.is_valid_block_chain(chain)):
                longest_chain = chain
                max_lenght = length
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

            


app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
blockchain = Blockchain()
node_address = str(uuid4()).replace('-', '')

#args
try:
    if not (sys.argv[1] == None):
        user_wallet = sys.argv[1]
    if not (sys.argv[2] == None):
        port = sys.argv[2]
except:
    user_wallet = 'John'
    port = 5000

@app.route('/mine_block', methods= ['GET', 'POST'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.get_block_hash(previous_block)
    blockchain.add_transaction(node_address, user_wallet, 1)
    block = blockchain.create_block(proof, previous_hash)
    response = {
        'message': 'Parabéns, você minerou um bloco!.',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        'transactions': block['transactions']
    }
    return jsonify(response), 200

@app.route('/get_chain', methods= ['GET'])
def get_chain():
    chain_len = len(blockchain.chain)
    response = {
        'chain': blockchain.chain,
        'length': chain_len
    }
    return jsonify(response), 200

@app.route('/is_valid', methods=['GET'])
def is_valid():
    reponse = {
        'is_valid': blockchain.is_valid_block_chain(blockchain.chain)
    }
    return jsonify(reponse), 200

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_keys):
        return 'Algum parametro da requisição esta faltando', 400
    block_index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {
        'message': f'A transação será adicionada ao bloco {block_index}'
    }
    return jsonify(response), 201

@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes_list = json['nodes']
    if nodes_list is None:
        return 'A requisição esta vazia', 400
    for node in nodes_list:
        blockchain.add_node(node)
    response = {
        'message': 'Todos os nós foram conectados a blockchain',
        'nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201

@app.route('/consensus', methods=['GET'])
def consensus():
    is_chain_updated = blockchain.replace_chain()
    response = {
        'message': 'O processo de consensu foi finalizado',
        'was_chain_updated': is_chain_updated
    }
    return jsonify(response), 200


app.run('0.0.0.0', port)