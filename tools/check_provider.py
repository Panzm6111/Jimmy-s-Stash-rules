#!/usr/bin/env python3
"""Check the PUBLIC simulated SS/VLESS fixture; never downloads a subscription."""
from collections import Counter
import sys
import uuid
from validate import load

def check(data):
    if not isinstance(data, dict) or not isinstance(data.get('proxies'), list) or not data['proxies']:
        raise ValueError('expected a nonempty proxies list')
    names=set();counts=Counter()
    for index,node in enumerate(data['proxies'],1):
        if not isinstance(node,dict):raise ValueError(f'node #{index}: mapping required')
        if not all(k in node for k in ['name','type','server','port']):raise ValueError(f'node #{index}: missing common fields')
        if node['name'] in names:raise ValueError(f'node #{index}: duplicate name')
        names.add(node['name'])
        if not isinstance(node['port'],int) or not 1<=node['port']<=65535:raise ValueError(f'node #{index}: invalid port')
        if node['type']=='ss':
            if not node.get('cipher') or not node.get('password'):raise ValueError(f'node #{index}: missing SS fields')
        elif node['type']=='vless':
            uuid.UUID(node.get('uuid',''))
            if node.get('network','tcp') not in {'tcp','ws'}:raise ValueError(f'node #{index}: transport outside this sample audit')
            if any(k in node for k in ['reality-opts','flow','grpc-opts','packet-encoding']):raise ValueError(f'node #{index}: advanced fields require native Stash verification')
        else:raise ValueError(f'node #{index}: protocol outside this sample audit')
        if node.get('skip-cert-verify'):raise ValueError(f'node #{index}: TLS verification bypass')
        counts[node['type']]+=1
    return dict(counts)

def main():
    try:counts=check(load('examples/provider-simulated.yaml'))
    except Exception as error:
        print('FAIL: simulated provider shape:',type(error).__name__)
        return 1
    print('PASS: PUBLIC simulated provider basic fields; protocol counts:',counts)
    print('NOT VERIFIED: exact Stash parser support, subscription decoding, real network access or any server credential.')
    return 0
if __name__=='__main__':sys.exit(main())
