import datetime
import json
import hashlib
from flask import Flask, jsonify

class Blockchain():
    def __init__(self):
        self.chain = []
        self.create_block(proof = 1, previous_hash = '0')

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'previous_hash': previous_hash,
            'proof': proof
        }
        self.chain.append(block)
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
        return hash[:4] == '0000'

    def get_block_hash(self, block):
        json_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(json_block).hexdigest()
    
    def is_valid_block_chain(self):
        previous_block = self.chain[0]
        actual_block_index = 1
        while actual_block_index < len(self.chain):
            actual_block = self.chain[actual_block_index]
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


app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
blockchain = Blockchain()

@app.route('/mine_block', methods= ['GET', 'POST'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.get_block_hash(previous_block)
    block = blockchain.create_block(proof, previous_hash)
    response = {
        'message': 'Parabéns, você minerou um bloco!.',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }
    return jsonify(response), 200

@app.route('/get_chain', methods= ['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/is_valid', methods=['GET'])
def is_valid():
    reponse = {
        'is_valid': blockchain.is_valid_block_chain()
    }
    return jsonify(reponse), 200

app.run('0.0.0.0', 5000)