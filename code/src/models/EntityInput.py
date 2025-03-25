from pydantic import BaseModel

class EntityInput(BaseModel):
    transaction_id: str  # Transaction ID provided by the user
    sender: str  # Sender name provided by the user
    receiver: str  # Receiver name provided by the user
    amount: float  # Amount associated with the transaction
    currency: str  # Currency associated with the transaction
    transaction_details: str  # Additional notes provided by the user