from dataclasses import dataclass

@dataclass
class StrategyVault:
    address:str
    id_active: bool
    creator: str
    deposit_token_address: str
    token_addresses_to_buy: list[str]
    tokens_to_buy_decimals: list[int]
    buy_amounts: list[int]
    depositor_addresses: list[str]
    buy_frequency_timestamp: int
    last_update_timestamp = int

    

