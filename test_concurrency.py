import asyncio
import uuid
import httpx

BASE_URL = "http://localhost:8000/api/v1"
CONCURRENT_USERS = 50
INITIAL_STOCK = 1


async def create_user_and_login(client: httpx.AsyncClient, user_idx: int) -> str:
    """Registers a new user and returns their JWT bearer token."""
    email = f"loadtest_user_{user_idx}_{uuid.uuid4().hex[:6]}@example.com"
    password = "SecurePassword123!"

    # 1. Register
    reg_resp = await client.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": password},
    )
    assert reg_resp.status_code == 201, f"User registration failed: {reg_resp.text}"

    # 2. Login
    login_resp = await client.post(
        f"{BASE_URL}/auth/login",
        data={"username": email, "password": password},
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    return login_resp.json()["access_token"]


async def setup_test_product(token: str) -> int:
    """Creates a high-contention item with exact total_stock = 1."""
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        resp = await client.post(
            f"{BASE_URL}/products",
            json={
                "name": f"Flash Sale Item ({uuid.uuid4().hex[:4]})",
                "price": 99.99,
                "total_stock": INITIAL_STOCK,
            },
        )
        assert resp.status_code == 201, f"Product creation failed: {resp.text}"
        product_id = resp.json()["id"]
        print(f"[*] Created target product (ID: {product_id}) with total_stock: {INITIAL_STOCK}")
        return product_id


async def prepare_user_cart(token: str, product_id: int):
    """Adds 1 unit of the item to the user's cart (zero hold intent)."""
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        resp = await client.post(
            f"{BASE_URL}/cart/items",
            json={"product_id": product_id, "quantity": 1},
        )
        assert resp.status_code == 200, f"Add to cart failed: {resp.text}"


async def checkout_attempt(token: str, user_idx: int) -> dict:
    """Fires checkout request to grab the atomic reservation lock."""
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
        resp = await client.post(f"{BASE_URL}/orders/checkout")
        return {
            "user_idx": user_idx,
            "status_code": resp.status_code,
            "body": resp.json() if resp.status_code in (201, 409, 400) else resp.text,
        }


async def main():
    print(f"\n=======================================================")
    print(f" CONCURRENCY TEST: {CONCURRENT_USERS} USERS COMPETING FOR {INITIAL_STOCK} UNIT")
    print(f"=======================================================\n")

    # Step 1: Create admin/primary user to seed the product
    async with httpx.AsyncClient(timeout=10.0) as client:
        admin_token = await create_user_and_login(client, 0)
    product_id = await setup_test_product(admin_token)

    # Step 2: Register & authenticate N concurrent shoppers
    print(f"[*] Registering and populating carts for {CONCURRENT_USERS} users...")
    user_tokens = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for idx in range(1, CONCURRENT_USERS + 1):
            token = await create_user_and_login(client, idx)
            user_tokens.append(token)

    # Prepare each user's cart in parallel
    await asyncio.gather(
        *(prepare_user_cart(token, product_id) for token in user_tokens)
    )
    print(f"[+] All {CONCURRENT_USERS} carts prepped and ready.")

    # Step 3: Launch simultaneous checkout bombardment
    print(f"\n[>>>] Triggering simultaneous checkout for all {CONCURRENT_USERS} users...")
    checkout_tasks = [
        checkout_attempt(token, idx) for idx, token in enumerate(user_tokens, start=1)
    ]
    results = await asyncio.gather(*checkout_tasks)

    # Step 4: Analyze checkout outcomes
    successes = [r for r in results if r["status_code"] == 201]
    conflicts = [r for r in results if r["status_code"] == 409]
    errors = [r for r in results if r["status_code"] not in (201, 409)]

    print(f"\n----------------- CHECKOUT RESULTS -----------------")
    print(f"Successful Reservations (HTTP 201) : {len(successes)}")
    print(f"Stock Rejections (HTTP 409)        : {len(conflicts)}")
    print(f"Unexpected Errors                  : {len(errors)}")

    if successes:
        winner = successes[0]
        print(f"[+] Winning User: User #{winner['user_idx']} (Order ID: {winner['body']['id']})")

    # Step 5: Verify product state in DB
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{BASE_URL}/products/{product_id}")
        prod_data = resp.json()
        print(f"\n---------------- PRODUCT FINAL STATE ---------------")
        print(f"Total Stock     : {prod_data['total_stock']}")
        print(f"Reserved Stock  : {prod_data['reserved_stock']}")
        print(f"Available Stock : {prod_data['available_stock']}")

    # Step 6: Assert invariants
    assert len(successes) == INITIAL_STOCK, (
        f"CRITICAL OVERSELL BUG! Expected exactly {INITIAL_STOCK} success, "
        f"but got {len(successes)}!"
    )
    assert len(conflicts) == (CONCURRENT_USERS - INITIAL_STOCK), (
        f"Expected {CONCURRENT_USERS - INITIAL_STOCK} 409 conflicts."
    )
    assert prod_data["reserved_stock"] == INITIAL_STOCK, "Reserved stock count mismatch!"
    assert prod_data["available_stock"] == 0, "Available stock should be 0!"

    print(f"\n[SUCCESS] Concurrency test passed: ZERO OVERSELLING DETECTED!\n")


if __name__ == "__main__":
    asyncio.run(main())