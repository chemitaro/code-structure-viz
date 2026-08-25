from external.gateway import Gateway

from domain.order import Order


class OrderService:
    async def submit(self, order: Order, gateway: Gateway) -> Order:
        return order
