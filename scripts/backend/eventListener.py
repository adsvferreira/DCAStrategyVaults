from brownie import web3
from strategy_fetcher import vaults_factory_contract


class EventListener:
    def __init__(self):
        self.block_number = vaults_factory_contract.tx.block_number

    # returns the new vaults addresses
    def event_listener_vaults_update(self) -> list[str]:
        event_filter = vaults_factory_contract.events.VaultCreated.createFilter(fromBlock=self.block_number)
        entries = event_filter.get_all_entries()
        self.block_number = web3.eth.blockNumber

        return [entry.args.vaultAddress for entry in entries]
