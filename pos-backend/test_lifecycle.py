import asyncio
import uuid
import httpx

BASE_URL = "http://localhost:8000/api/v1"


async def setup_session(client: httpx.AsyncClient, name: str) -> str:
    """Helper to register and login a test user."""
    email = f"{name}_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "TestPassword123!"
    await client.post(f"{BASE_URL}/auth/register", json={"email": email, "password": pwd})
    res = await client.post(f"{BASE_URL}/auth/login", data={"username": email, "password": pwd})
    return res.json()["access_token"]


async def create_product(client: httpx.AsyncClient, token: str, stock: int) -> int:
    res = await client.post(
        f"{BASE_URL}/products",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": f"Item-{uuid.uuid4().hex[:4]}", "price": 50.00, "total_stock": stock},
    )
    return res.json()["id"]


async def add_to_cart_and_checkout(client: httpx.AsyncClient, token: str, product_id: int) -> int:
    headers = {"Authorization": f"Bearer {token}"}
    await client.post(f"{BASE_URL}/cart/items", headers=headers, json={"product_id": product_id, "quantity": 1})
    res = await client.post(f"{BASE_URL}/orders/checkout", headers=headers)
    assert res.status_code == 201, f"Checkout failed: {res.text}"
    return res.json()["id"]


async def get_product_stock(client: httpx.AsyncClient, product_id: int) -> dict:
    res = await client.get(f"{BASE_URL}/products/{product_id}")
    return res.json()


async def run_lifecycle_tests():
    print("\n=======================================================")
    print(" STARTING POS LIFECYCLE & PAYMENT VALIDATION")
    print("=======================================================\n")

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Setup admin & product
        admin_token = await setup_session(client, "admin")
        prod_id = await create_product(client, admin_token, stock=10)

        # -----------------------------------------------------------------
        # TEST 1: Payment Success & Stock Settlement
        # -----------------------------------------------------------------
        print("[TEST 1] Testing Payment SUCCESS flow...")
        u1_token = await setup_session(client, "user1")
        order1_id = await add_to_cart_and_checkout(client, u1_token, prod_id)

        # Submit SUCCESS payment with Idempotency Key
        idem_key_1 = str(uuid.uuid4())
        pay_res = await client.post(
            f"{BASE_URL}/orders/{order1_id}/pay",
            headers={"Authorization": f"Bearer {u1_token}", "Idempotency-Key": idem_key_1},
            json={"simulate_outcome": "SUCCESS"},
        )
        assert pay_res.status_code == 200, f"Payment failed: {pay_res.text}"
        data = pay_res.json()
        assert data["order_status"] == "PAID", f"Expected PAID, got {data['order_status']}"

        # Verify stock committed permanently (total drops from 10 to 9, reserved drops from 1 to 0)
        stock = await get_product_stock(client, prod_id)
        assert stock["total_stock"] == 9 and stock["reserved_stock"] == 0 and stock["available_stock"] == 9
        print("  --> PASSED: Payment SUCCESS committed stock permanently (Total: 9, Reserved: 0).")

        # -----------------------------------------------------------------
        # TEST 2: Idempotency Key Duplicate Prevention
        # -----------------------------------------------------------------
        print("\n[TEST 2] Testing Payment IDEMPOTENCY duplicate submission...")
        dup_res = await client.post(
            f"{BASE_URL}/orders/{order1_id}/pay",
            headers={"Authorization": f"Bearer {u1_token}", "Idempotency-Key": idem_key_1},
            json={"simulate_outcome": "SUCCESS"},
        )
        assert dup_res.status_code == 200
        assert "Duplicate request detected" in dup_res.json()["message"]
        
        # Verify no double-deduction happened
        stock = await get_product_stock(client, prod_id)
        assert stock["total_stock"] == 9 and stock["reserved_stock"] == 0
        print("  --> PASSED: Duplicate payment request caught and safely ignored.")

        # -----------------------------------------------------------------
        # TEST 3: Payment Failure & Immediate Stock Restoration
        # -----------------------------------------------------------------
        print("\n[TEST 3] Testing Payment FAILURE flow...")
        u2_token = await setup_session(client, "user2")
        order2_id = await add_to_cart_and_checkout(client, u2_token, prod_id)

        pay_res_fail = await client.post(
            f"{BASE_URL}/orders/{order2_id}/pay",
            headers={"Authorization": f"Bearer {u2_token}", "Idempotency-Key": str(uuid.uuid4())},
            json={"simulate_outcome": "FAILURE"},
        )
        assert pay_res_fail.status_code == 200
        assert pay_res_fail.json()["order_status"] == "FAILED"

        # Verify stock restored to available
        stock = await get_product_stock(client, prod_id)
        assert stock["total_stock"] == 9 and stock["reserved_stock"] == 0 and stock["available_stock"] == 9
        print("  --> PASSED: Payment FAILURE restored stock back to available pool.")

        # -----------------------------------------------------------------
        # TEST 4: Manual Order Cancellation
        # -----------------------------------------------------------------
        print("\n[TEST 4] Testing Manual Order CANCELLATION flow...")
        u3_token = await setup_session(client, "user3")
        order3_id = await add_to_cart_and_checkout(client, u3_token, prod_id)

        # Cancel order
        cancel_res = await client.post(
            f"{BASE_URL}/orders/{order3_id}/cancel",
            headers={"Authorization": f"Bearer {u3_token}"},
        )
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "CANCELLED"

        stock = await get_product_stock(client, prod_id)
        assert stock["total_stock"] == 9 and stock["reserved_stock"] == 0 and stock["available_stock"] == 9
        print("  --> PASSED: Manual cancellation cleanly released reserved hold.")

        # -----------------------------------------------------------------
        # TEST 5: Payment TIMEOUT Simulation
        # -----------------------------------------------------------------
        print("\n[TEST 5] Testing Payment TIMEOUT flow...")
        u4_token = await setup_session(client, "user4")
        order4_id = await add_to_cart_and_checkout(client, u4_token, prod_id)

        timeout_res = await client.post(
            f"{BASE_URL}/orders/{order4_id}/pay",
            headers={"Authorization": f"Bearer {u4_token}", "Idempotency-Key": str(uuid.uuid4())},
            json={"simulate_outcome": "TIMEOUT"},
        )
        assert timeout_res.status_code == 200
        assert timeout_res.json()["payment"]["status"] == "TIMEOUT"

        # Stock must still remain reserved pending resolution or 5-min expiry
        stock = await get_product_stock(client, prod_id)
        assert stock["reserved_stock"] == 1 and stock["available_stock"] == 8
        print("  --> PASSED: Gateway TIMEOUT kept reservation locked awaiting resolution.")

    print("\n=======================================================")
    print(" ALL LIFECYCLE & STATE TRANSITION TESTS PASSED!")
    print("=======================================================\n")


if __name__ == "__main__":
    asyncio.run(run_lifecycle_tests())