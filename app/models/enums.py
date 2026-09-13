from enum import Enum


class CartStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CONVERTED = "CONVERTED"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    RESERVED = "RESERVED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"


class PaymentStatus(str, Enum):
    INITIATED = "INITIATED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class MockPaymentOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    TIMEOUT = "TIMEOUT"