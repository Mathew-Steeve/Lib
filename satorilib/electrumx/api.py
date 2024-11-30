from typing import Union, Dict
import time
import logging

logging.basicConfig(level=logging.INFO)


class ElectrumxApi():
    def __init__(self, send: callable, subscribe: callable):
        self.send = send
        self.subscribe = subscribe

    @staticmethod
    def interpret(decoded: dict) -> Union[dict, None]:
        if decoded is None:
            return None
        if isinstance(decoded, str):
            return {'result': decoded}
        if 'result' in decoded.keys():
            return decoded.get('result')
        if 'error' in decoded.keys():
            return decoded.get('error')
        else:
            return decoded

    def sendRequest(self, method: str, *params) -> Union[dict, None]:
        try:
            return ElectrumxApi.interpret(self.send(method, *params))
        except Exception as e:
            logging.error(f"Error during {method}: {str(e)}")

    def sendSubscriptionRequest(
        self,
        method: str,
        *params,
        callback: Union[callable, None] = None
    ) -> Union[dict, None]:
        try:
            return ElectrumxApi.interpret(
                self.subscribe(method, *params, callback=callback))
        except Exception as e:
            logging.error(f"Error during {method}: {str(e)}")

    # endpoints ###############################################################

    def subscribeToHeaders(
        self,
        callback: Union[callable, None] = None
    ) -> dict:
        '''
        {
            'jsonrpc': '2.0',
            'method': 'blockchain.headers.subscribe',
            'params': [{
                'hex': '000000305c02f283351ee21f614f6621b1df70340838d210200177d2758c0a0000000000f6f7897033a4a1732d44026f33538e1db2ba501d34864230e70d46c583648921b5693667a64b341b66481000af2e219103036af7213d29d250a8c198a777bdcb8759b1b8d04a870b99259ae4502e106fdc6bc0a3',
                'height': 1067110}]
        }
        '''
        return self.sendSubscriptionRequest('blockchain.headers.subscribe', callback=callback) or {}

    def subscribeScripthash(
        self,
        scripthash: str,
        callback: Union[callable, None] = None
    ) -> dict:
        '''
        Subscribe to the scripthash and start listening for updates.
        {
            'jsonrpc': '2.0',
            'method': 'blockchain.scripthash.subscribe',
            'params': [
                '130946f0c05cd0d3de7e1b8d59273999e0d6964be497ca5e57ffc07e5e9afdae',
                '5e5bce190932eb2b780574b4004ecdb9dfd8049400424701765e1858f6a817df'
            ]
        }
        '''
        return self.sendSubscriptionRequest(
            'blockchain.scripthash.subscribe',
            scripthash,
            callback=callback) or {}

    def getBalance(self, scripthash: str, targetAsset: str = 'SATORI') -> dict:
        '''
        {
            'jsonrpc': '2.0',
            'result': {'confirmed': 0, 'unconfirmed': 0},
            'id': 1719672672565
        }
        '''
        return self.sendRequest(
            'blockchain.scripthash.get_asset_balance',
            scripthash,
            targetAsset) or {}

    def getAllBalances(self, scripthash: str) -> dict:
        '''
        Zeroth — Today at 11:16 AM
        Just in case you want to update your python,
        this way does work and sums the totals for you:
            const isAddressUsedQuery = {
                jsonrpc: '2.0',
                method: 'blockchain.scripthash.get_balance',
                params: [scriptHash, true],
                id: 3,
            };
        Result:
            {"jsonrpc":"2.0","id":3,"result":{
                "rvn":{"confirmed":200000000,"unconfirmed":0},
                "LOLLIPOP":{"confirmed":100000000,"unconfirmed":0},
                "SATORI":{"confirmed":155659082600,"unconfirmed":0}}}
        '''
        return self.sendRequest(
            'blockchain.scripthash.get_asset_balance',
            scripthash,
            True) or {}

    def getTransactionHistory(self, scripthash: str) -> list:
        '''
        b.send("blockchain.scripthash.get_history",
               script_hash('REsQeZT8KD8mFfcD4ZQQWis4Ju9eYjgxtT'))
        b'{
            "jsonrpc":"2.0",
            "result":[{
                "tx_hash":"a015f44b866565c832022cab0dec94ce0b8e568dbe7c88dce179f9616f7db7e3",
                "height":2292586}],
            "id":1656046324946
        }\n'
        '''
        return self.sendRequest('blockchain.scripthash.get_history', scripthash) or []

    def getTransaction(self, txHash: str, throttle: int = 0.34):
        time.sleep(throttle)
        return self.sendRequest('blockchain.transaction.get', txHash, True)

    def getCurrency(self, scripthash: str) -> int:
        '''
        >>> b.send("blockchain.scripthash.get_balance", script_hash('REsQeZT8KD8mFfcD4ZQQWis4Ju9eYjgxtT'))
        b'{"jsonrpc":"2.0","result":{"confirmed":18193623332178,"unconfirmed":0},"id":1656046285682}\n'
        '''
        result = self.sendRequest(
            'blockchain.scripthash.get_balance',
            scripthash)
        return (result or {}).get('confirmed', 0) + (result or {}).get('unconfirmed', 0)

    def getBanner(self) -> dict:
        return self.sendRequest('server.banner')

    def getUnspentCurrency(self, scripthash: str) -> list:
        return self.sendRequest(
            'blockchain.scripthash.listunspent', scripthash)

    def getUnspentAssets(self, scripthash: str, targetAsset: str = 'SATORI') -> list:
        '''
        {
            'jsonrpc': '2.0',
            'result': [{
                'tx_hash': 'bea0e23c0aa8a4f1e1bb8cda0c6f487a3c0c0e7a54c47b6e1883036898bdc101',
                'tx_pos': 0,
                'height': 868584,
                'asset': 'KINKAJOU/DUMMY',
                'value': 100000000}],
            'id': 1719672839478
        }
        '''
        return self.sendRequest(
            'blockchain.scripthash.listunspent',
            scripthash,
            targetAsset)

    def getStats(self, targetAsset: str = 'SATORI'):
        return self.sendRequest('blockchain.asset.get_meta', targetAsset)

    def getAssetBalanceForHolder(self, scripthash: str, throttle: int = 1):
        time.sleep(throttle)
        return self.sendRequest('blockchain.scripthash.get_asset_balance', True, scripthash).get('confirmed', {}).get('SATORI', 0)

    def getAssetHolders(self, targetAddress: Union[str, None] = None, targetAsset: str = 'SATORI') -> Union[Dict[str, int], bool]:
        addresses = {}
        last_addresses = None
        i = 0
        while last_addresses != addresses:
            last_addresses = addresses
            response = self.sendRequest(
                'blockchain.asset.list_addresses_by_asset',
                targetAsset,
                False,
                1000,
                i)
            if targetAddress is not None and targetAddress in response.keys():
                return {targetAddress: response[targetAddress]}
            addresses = {**addresses, **response}
            if len(response) < 1000:
                break
            i += 1000
            time.sleep(1)  # Throttle to avoid hitting server limits
        return addresses

    def broadcast(self, tx: str) -> str:
        return self.sendRequest('blockchain.transaction.broadcast', tx)