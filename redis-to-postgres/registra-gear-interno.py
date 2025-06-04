def push_stack(record):
    execute('RPUSH', 'minha_pilha', record['value'])

GB('KeysReader', 
   desc='Listen for pessoa:* changes'
).foreach(push_stack).register('pessoa:*')