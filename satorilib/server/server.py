'''
Here's plan for the server - python server, you checkin with it,
it returns a key you use to make a websocket connection with the pubsub server.
'''
from typing import Union
import json
import requests
from satorilib import logging
from satorilib.api.wallet import Wallet
from functools import partial


class SatoriServerClient(object):
    def __init__(
        self,
        wallet: Wallet,
        url: str = None,
        *args, **kwargs
    ):
        super(SatoriServerClient, self).__init__(*args, **kwargs)
        self.wallet = wallet
        self.url = url or 'https://satorinet.io'

    def _getChallenge(self):
        return requests.get(self.url + '/time').text

    def _makeAuthenticatedCall(
        self,
        function: callable,
        endpoint: str,
        json: Union[str, None] = None,
        challenge: str = None,
        useWallet: Wallet = None,
    ):
        if json is not None:
            logging.info(
                'outgoing Satori server message:',
                json[0:40], f'{"..." if len(json) > 40 else ""}',
                print=True)
        r = function(
            self.url + endpoint,
            headers=(useWallet or self.wallet).authPayload(
                asDict=True,
                challenge=challenge or self._getChallenge()),
            json=json)
        r.raise_for_status()
        logging.info(
            'incoming Satori server message:',
            r.text[0:40], f'{"..." if len(r.text) > 40 else ""}',
            print=True)
        return r

    def _makeUnauthenticatedCall(
        self,
        function: callable,
        endpoint: str,
        headers: Union[dict, None] = None,
        payload: Union[str, bytes, None] = None,
    ):
        logging.info(
            'outgoing Satori server message to ',
            endpoint,
            print=True)
        data = None
        json = None
        if isinstance(payload, bytes):
            headers = headers or {'Content-Type': 'application/octet-stream'}
            data = payload
        elif isinstance(payload, str):
            headers = headers or {'Content-Type': 'application/json'}
            json = payload
        else:
            headers = headers or {}
        r = function(
            self.url + endpoint,
            headers=headers,
            json=json,
            data=data)
        r.raise_for_status()
        logging.info(
            'incoming Satori server message:',
            r.text[0:40], f'{"..." if len(r.text) > 40 else ""}',
            print=True)
        return r

    def registerWallet(self):
        return self._makeAuthenticatedCall(
            function=requests.post,
            endpoint='/register/wallet',
            json=self.wallet.registerPayload())

    def registerStream(self, stream: dict, payload: str = None):
        ''' publish stream {'source': 'test', 'name': 'stream1', 'target': 'target'}'''
        return self._makeAuthenticatedCall(
            function=requests.post,
            endpoint='/register/stream',
            json=payload or json.dumps(stream))

    def registerSubscription(self, subscription: dict, payload: str = None):
        ''' subscribe to stream '''
        return self._makeAuthenticatedCall(
            function=requests.post,
            endpoint='/register/subscription',
            json=payload or json.dumps(subscription))

    def registerPin(self, pin: dict, payload: str = None):
        ''' 
        report a pin to the server.
        example: {
            'author': {'pubkey': '22a85fb71485c6d7c62a3784c5549bd3849d0afa3ee44ce3f9ea5541e4c56402d8'}, 
            'stream': {'source': 'satori', 'pubkey': '22a85fb71485c6d7c62a3784c5549bd3849d0afa3ee44ce3f9ea5541e4c56402d8', 'stream': 'stream1', 'target': 'target', 'cadence': None, 'offset': None, 'datatype': None, 'url': None, 'description': 'raw data'},, 
            'ipns': 'ipns', 
            'ipfs': 'ipfs', 
            'disk': 1, 
            'count': 27},
        '''
        return self._makeAuthenticatedCall(
            function=requests.post,
            endpoint='/register/pin',
            json=payload or json.dumps(pin))

    def requestPrimary(self):
        ''' subscribe to primary data stream and and publish prediction '''
        return self._makeAuthenticatedCall(
            function=requests.get,
            endpoint='/request/primary')

    def getStreams(self, stream: dict, payload: str = None):
        ''' subscribe to primary data stream and and publish prediction '''
        return self._makeAuthenticatedCall(
            function=requests.post,
            endpoint='/get/streams',
            json=payload or json.dumps(stream))

    def myStreams(self):
        ''' subscribe to primary data stream and and publish prediction '''
        return self._makeAuthenticatedCall(
            function=requests.post,
            endpoint='/my/streams',
            json='{}')

    def removeStream(self, stream: dict = None, payload: str = None):
        ''' removes a stream from the server '''
        if payload is None and stream is None:
            raise ValueError('stream or payload must be provided')
        return self._makeAuthenticatedCall(
            function=requests.post,
            endpoint='/remove/stream',
            json=payload or json.dumps(stream or {}))

    def checkin(self) -> dict:
        challenge = self._getChallenge()
        return self._makeAuthenticatedCall(
            function=requests.post,
            endpoint='/checkin',
            json=self.wallet.registerPayload(challenge=challenge),
            challenge=challenge).json()

    def requestSimplePartial(self, network: str):
        ''' sends a satori partial transaction to the server '''
        return self._makeUnauthenticatedCall(
            function=requests.get,
            endpoint=f'/simple_partial/request/{network}').json()

    def broadcastSimplePartial(
        self,
        tx: bytes,
        feeSatsReserved: float,
        reportedFeeSats: float,
        network: str
    ):
        ''' sends a satori partial transaction to the server '''
        return self._makeUnauthenticatedCall(
            function=requests.post,
            endpoint=f'/simple_partial/broadcast/{network}/{feeSatsReserved}/{reportedFeeSats}',
            payload=tx)

    def removeWalletAlias(self):
        ''' removes the wallet alias from the server '''
        return self._makeAuthenticatedCall(
            function=requests.get,
            endpoint='/remove_wallet_alias')

    def updateWalletAlias(self, alias: str):
        ''' removes the wallet alias from the server '''
        return self._makeAuthenticatedCall(
            function=requests.get,
            endpoint='/update_wallet_alias/' + alias)

    def getWalletAlias(self):
        ''' removes the wallet alias from the server '''
        return self._makeAuthenticatedCall(
            function=requests.get,
            endpoint='/get_wallet_alias').text

    def submitMaifestVote(self, wallet: Wallet, votes: dict[str, int]):
        return self._makeAuthenticatedCall(
            function=requests.post,
            endpoint='/vote_on/manifest',
            useWallet=wallet,
            json=json.dumps(votes or {})).text

    def submitStreamVote(self, wallet: Wallet, votes: dict[str, int]):
        return self._makeAuthenticatedCall(
            function=requests.post,
            endpoint='/vote_on/stream',
            useWallet=wallet,
            json=json.dumps(votes or {})).text
