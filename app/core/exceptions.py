class SCMException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
    
class ProductNotFoundError(SCMException):
    def __init__(self, product_id: int):
        super().__init__(message=f"Product with id {product_id} not found.", status_code=404)

class InsufficientStockError(SCMException):
    def __init__(self, product_id: int):
        super().__init__(message=f"Insufficient stock for product id {product_id}.", status_code=400)
