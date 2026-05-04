import json
import os
import time
from datetime import datetime

# Fayl yolları
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")

class MiniStore:
    def __init__(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        self.current_user = None
        self.setup_default_data()

    def setup_default_data(self):
        # Default məhsullar
        if not os.path.exists(PRODUCTS_FILE):
            products = {
                "Geyimlər": [
                    {"id": 1, "name": "T-Shirt", "price": 12.50},
                    {"id": 2, "name": "Hoodie", "price": 45.00},
                    {"id": 3, "name": "Jeans", "price": 60.00}
                ],
                "Elektronika": [
                    {"id": 1, "name": "Qulaqlıq", "price": 35.00},
                    {"id": 2, "name": "Powerbank", "price": 25.00},
                    {"id": 3, "name": "Siçan", "price": 15.00}
                ],
                "Kitablar": [
                    {"id": 1, "name": "Algorithms 101", "price": 20.00},
                    {"id": 2, "name": "Clean Code", "price": 55.00},
                    {"id": 3, "name": "Python Basics", "price": 30.00}
                ]
            }
            with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
                json.dump(products, f, indent=4)

        # Default istifadəçi
        if not os.path.exists(USERS_FILE):
            users = [{
                "username": "student1",
                "password": "1234",
                "balance": 100.0,
                "failed_attempts": 0,
                "lock_until": None
            }]
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(users, f, indent=4)

    # --- KÖMƏKÇİ FUNKSİYALAR ---
    def load_json(self, filename, default=[]):
        if not os.path.exists(filename): return default
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return default

    def save_json(self, filename, data):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def log_event(self, message):
        log_file = os.path.join(DATA_DIR, f"history_{self.current_user['username']}.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

    # --- LOGİN SİSTEMİ ---
    def login(self):
        users = self.load_json(USERS_FILE)
        
        while True:
            username = input("İstifadəçi adı: ")
            password = input("Şifrə: ")

            user = next((u for u in users if u['username'] == username), None)
            
            if not user:
                print("İstifadəçi tapılmadı!")
                continue

            # Cooldown yoxlanışı
            if user['lock_until'] and time.time() < user['lock_until']:
                wait_time = int(user['lock_until'] - time.time())
                print(f"Hesab bloklanıb. {wait_time} saniyə gözləyin.")
                continue

            if user['password'] == password:
                user['failed_attempts'] = 0
                user['lock_until'] = None
                self.save_json(USERS_FILE, users)
                self.current_user = user
                self.log_event("LOGIN_SUCCESS")
                print(f"\nXoş gəldiniz, {username}!")
                return True
            else:
                user['failed_attempts'] += 1
                print(f"Səhv şifrə! Cəhd: {user['failed_attempts']}/3")
                
                if user['failed_attempts'] >= 3:
                    print("3 dəfə səhv daxil edildi. 10 saniyə gözləyin...")
                    user['lock_until'] = time.time() + 10
                    user['failed_attempts'] = 0
                    for i in range(10, 0, -1):
                        print(f"{i}...", end="\r")
                        time.sleep(1)
                
                self.save_json(USERS_FILE, users)
                self.log_event(f"LOGIN_FAIL (wrong password)")

    # --- MAĞAZA FUNKSİYALARI ---
    def show_categories(self):
        products_data = self.load_json(PRODUCTS_FILE)
        categories = list(products_data.keys())
        
        print("\n--- Kateqoriyalar ---")
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat}")
        print("0. Geri")
        
        choice = input("Seçim edin: ")
        if choice == '0' or not choice.isdigit() or int(choice) > len(categories):
            return

        cat_name = categories[int(choice)-1]
        self.show_products(cat_name, products_data[cat_name])

    def show_products(self, cat_name, products):
        print(f"\n--- {cat_name} ---")
        for p in products:
            print(f"[{p['id']}] {p['name']} - {p['price']} AZN")
        
        prod_id = input("\nMəhsul ID daxil et (və ya 'X' geri): ").upper()
        if prod_id == 'X': return
        
        product = next((p for p in products if str(p['id']) == prod_id), None)
        if product:
            qty = input(f"{product['name']} üçün miqdar: ")
            if not qty.isdigit() or int(qty) <= 0:
                print("Xəta: Miqdar müsbət tam ədəd olmalıdır!")
                return
            
            qty = int(qty)
            print(f"\nSeçildi: {product['name']} x{qty}")
            action = input("[B] Səbətə əlavə et | [F] Favoritlərə əlavə et | [X] Ləğv et: ").upper()
            
            if action == 'B':
                self.add_to_basket(cat_name, product, qty)
            elif action == 'F':
                self.add_to_favorites(cat_name, product)

    def add_to_basket(self, cat, prod, qty):
        file = os.path.join(DATA_DIR, f"basket_{self.current_user['username']}.json")
        basket = self.load_json(file)
        basket.append({
            "category": cat,
            "product": prod['name'],
            "unit": prod['price'],
            "qty": qty,
            "line_total": prod['price'] * qty
        })
        self.save_json(file, basket)
        self.log_event(f"BASKET_ADD ({cat}/{prod['name']} x{qty})")
        print("Səbətə əlavə olundu!")

    def show_basket(self):
        file = os.path.join(DATA_DIR, f"basket_{self.current_user['username']}.json")
        while True:
            basket = self.load_json(file)
            total = sum(item['line_total'] for item in basket)
            
            print("\n--- Səbətim ---")
            for i, item in enumerate(basket):
                print(f"{i}. {item['product']} | {item['qty']} ədəd | Cəm: {item['line_total']} AZN")
            print(f"\nÜmumi Məbləğ: {total} AZN")
            print("-" * 20)
            print("Əmrlər: list | qty <id> <yeni_say> | remove <id> | clear | checkout | back")
            
            cmd = input("> ").lower().split()
            if not cmd: continue
            
            if cmd[0] == 'back': break
            elif cmd[0] == 'list': continue
            elif cmd[0] == 'clear':
                self.save_json(file, [])
            elif cmd[0] == 'remove' and len(cmd) > 1:
                idx = int(cmd[1])
                if 0 <= idx < len(basket): basket.pop(idx)
                self.save_json(file, basket)
            elif cmd[0] == 'checkout':
                self.checkout(basket, total, file)
                break

    def checkout(self, basket, total, basket_file):
        if not basket:
            print("Səbət boşdur!")
            return

        users = self.load_json(USERS_FILE)
        user_idx = next(i for i, u in enumerate(users) if u['username'] == self.current_user['username'])
        
        if users[user_idx]['balance'] >= total:
            old_balance = users[user_idx]['balance']
            users[user_idx]['balance'] -= total
            self.current_user['balance'] = users[user_idx]['balance']
            self.save_json(USERS_FILE, users)
            
            # Alış tarixçəsi
            p_file = os.path.join(DATA_DIR, f"purchases_{self.current_user['username']}.json")
            purchases = self.load_json(p_file)
            purchases.append({
                "ts": datetime.now().isoformat(),
                "items": basket,
                "total": total
            })
            self.save_json(p_file, purchases)
            self.save_json(basket_file, []) # Səbəti təmizlə
            
            self.log_event(f"CHECKOUT_SUCCESS total={total} | balance: {old_balance} -> {users[user_idx]['balance']}")
            print(f"Alış uğurludur! Yeni balans: {users[user_idx]['balance']} AZN")
        else:
            self.log_event("CHECKOUT_FAIL (insufficient balance)")
            print("Xəta: Balans kifayət deyil!")

    def settings(self):
        print("\n--- Şifrə Dəyişmə ---")
        old_pass = input("Köhnə şifrə: ")
        if old_pass != self.current_user['password']:
            print("Köhnə şifrə yanlışdır!")
            return
        
        new_pass = input("Yeni şifrə (min 4 simvol): ")
        if len(new_pass) < 4:
            print("Şifrə çox qısadır!")
            return
        
        users = self.load_json(USERS_FILE)
        for u in users:
            if u['username'] == self.current_user['username']:
                u['password'] = new_pass
        self.save_json(USERS_FILE, users)
        self.current_user['password'] = new_pass
        self.log_event("PASSWORD_CHANGED")
        print("Şifrə uğurla dəyişdirildi.")

    def run(self):
        if self.login():
            while True:
                print(f"\nBalans: {self.current_user['balance']} AZN")
                print("1) Kateqoriyalar\n2) Səbətim\n3) Favoritlərim\n4) Tarixçə\n5) Settings\n6) Balans\n0) Çıxış")
                choice = input("Seçim: ")
                
                if choice == '1': self.show_categories()
                elif choice == '2': self.show_basket()
                elif choice == '4':
                    log_file = os.path.join(DATA_DIR, f"history_{self.current_user['username']}.log")
                    if os.path.exists(log_file):
                        with open(log_file, "r") as f:
                            lines = f.readlines()
                            print("\n--- Son 20 hərəkət ---")
                            for line in lines[-20:]: print(line.strip())
                elif choice == '5': self.settings()
                elif choice == '6': print(f"Balansınız: {self.current_user['balance']} AZN")
                elif choice == '0': break

if __name__ == "__main__":
    store = MiniStore()
    store.run()
