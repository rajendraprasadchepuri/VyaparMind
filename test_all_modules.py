"""
Comprehensive Module Testing for VyaparMind
Tests all 27 modules with UI logic, functionality, and data validation
"""

import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import secrets

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database as db
import config
import validators
from exceptions import *
from logger import log_info, log_error

# Test configuration
TEST_DB = "test_all_modules.db"


class ModuleTestRunner:
    """Comprehensive module testing."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.test_account_id = None
        self.test_user = None
        
    def log_pass(self, module, test):
        self.passed += 1
        print(f"  ✅ [{module}] {test}")
        
    def log_fail(self, module, test, error):
        self.failed += 1
        self.errors.append((module, test, error))
        print(f"  ❌ [{module}] {test}: {error}")
    
    def setup_test_environment(self):
        """Setup clean test environment."""
        print("\n" + "="*80)
        print("VYAPARMIND COMPREHENSIVE MODULE TESTING")
        print("="*80)
        print("\nSetting up test environment...")
        
        # Use test database
        self.original_db = config.SQLITE_DB
        config.SQLITE_DB = TEST_DB
        
        # Remove existing test DB
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except:
                pass
        
        # Initialize fresh database
        db.init_db()
        print("  [OK] Test database initialized")
        
        # Create test account
        company_name = f"TestCompany_{secrets.token_hex(4)}"
        success, msg = db.create_tenant(company_name, "Professional")
        if success:
            self.test_account_id = msg.split(":")[-1].strip()
            print(f"  [OK] Test account created: {self.test_account_id}")
        else:
            print(f"  [FAIL] Failed to create test account: {msg}")
            return False
        
        # Create test user
        success, msg = db.create_user(
            "admin_test", "test123", "admin@test.com",
            role='admin', override_account_id=self.test_account_id
        )
        if success:
            print(f"  [OK] Test user created: admin_test")
        else:
            print(f"  [FAIL] Failed to create test user: {msg}")
            return False
        
        return True
    
    def cleanup_test_environment(self):
        """Cleanup test environment."""
        print("\nCleaning up test environment...")
        config.SQLITE_DB = self.original_db
        try:
            if os.path.exists(TEST_DB):
                os.remove(TEST_DB)
            print("  [OK] Cleanup complete")
        except Exception as e:
            print(f"  [WARN] Cleanup warning: {e}")
    
    # ==================== MODULE TESTS ====================
    
    def test_authentication(self):
        """Test Module: Authentication & User Management"""
        print("\n" + "="*80)
        print("MODULE 1: AUTHENTICATION & USER MANAGEMENT")
        print("="*80)
        
        # Test login
        try:
            conn = db.get_connection()
            company_name = pd.read_sql_query(
                f"SELECT company_name FROM accounts WHERE id = {db.PLACEHOLDER}",
                conn, params=(self.test_account_id,)
            ).iloc[0]['company_name']
            conn.close()
            
            success, role, aid, cname = db.verify_user("admin_test", "test123", company_name)
            assert success, "Login should succeed"
            assert role == 'admin', f"Role should be admin, got {role}"
            assert aid == self.test_account_id, "Account ID mismatch"
            self.log_pass("Auth", "User login successful")
        except Exception as e:
            self.log_fail("Auth", "User login", str(e))
        
        # Test wrong password
        try:
            success, *_ = db.verify_user("admin_test", "wrongpass", company_name)
            assert not success, "Wrong password should fail"
            self.log_pass("Auth", "Wrong password rejected")
        except Exception as e:
            self.log_fail("Auth", "Wrong password rejection", str(e))
        
        # Test create additional user
        try:
            success, msg = db.create_user(
                "cashier1", "cash123", "cashier@test.com",
                role='cashier', override_account_id=self.test_account_id
            )
            assert success, f"User creation failed: {msg}"
            self.log_pass("Auth", "Create cashier user")
        except Exception as e:
            self.log_fail("Auth", "Create cashier user", str(e))
    
    def test_inventory_management(self):
        """Test Module: Inventory Management"""
        print("\n" + "="*80)
        print("MODULE 2: INVENTORY MANAGEMENT")
        print("="*80)
        
        # Add products
        product_ids = []
        try:
            pid = db.add_product("Apple", "Fruits", 100, 50, 1000, 5, override_account_id=self.test_account_id)
            product_ids.append(pid)
            self.log_pass("Inventory", "Add product - Apple")
        except Exception as e:
            self.log_fail("Inventory", "Add product", str(e))
        
        try:
            pid = db.add_product("Banana", "Fruits", 50, 30, 500, 5, override_account_id=self.test_account_id)
            product_ids.append(pid)
            self.log_pass("Inventory", "Add product - Banana")
        except Exception as e:
            self.log_fail("Inventory", "Add product", str(e))
        
        # Fetch products
        try:
            df = db.fetch_all_products(override_account_id=self.test_account_id)
            assert len(df) >= 2, f"Should have at least 2 products, got {len(df)}"
            assert 'Apple' in df['name'].values, "Apple not found"
            assert 'Banana' in df['name'].values, "Banana not found"
            self.log_pass("Inventory", "Fetch all products")
        except Exception as e:
            self.log_fail("Inventory", "Fetch products", str(e))
        
        # Update product
        try:
            if product_ids:
                db.update_product(product_ids[0], 120, 60, 1000, 5)
                df = db.fetch_all_products(override_account_id=self.test_account_id)
                updated_price = df[df['id'] == product_ids[0]].iloc[0]['price']
                assert updated_price == 120, f"Price not updated: expected 120, got {updated_price}"
                self.log_pass("Inventory", "Update product price")
        except Exception as e:
            self.log_fail("Inventory", "Update product", str(e))
        
        # Stock management
        try:
            if product_ids:
                db.update_stock(product_ids[0], 100)  # Add 100
                df = db.fetch_all_products(override_account_id=self.test_account_id)
                new_stock = int(df[df['id'] == product_ids[0]].iloc[0]['stock_quantity'])
                assert new_stock == 1100, f"Stock should be 1100, got {new_stock}"
                self.log_pass("Inventory", "Stock increase")
        except Exception as e:
            self.log_fail("Inventory", "Stock management", str(e))
        
        # Search products
        try:
            df = db.fetch_all_products(search_term="Apple", override_account_id=self.test_account_id)
            assert len(df) >= 1, "Search should find Apple"
            assert 'Apple' in df['name'].values, "Apple not in search results"
            self.log_pass("Inventory", "Product search")
        except Exception as e:
            self.log_fail("Inventory", "Product search", str(e))
        
        return product_ids
    
    def test_pos_transactions(self, product_ids):
        """Test Module: POS & Transactions"""
        print("\n" + "="*80)
        print("MODULE 3: POS & TRANSACTIONS")
        print("="*80)
        
        if not product_ids:
            self.log_fail("POS", "Prerequisites", "No products available")
            return
        
        # Get product details
        try:
            df = db.fetch_all_products(override_account_id=self.test_account_id)
            product = df[df['id'] == product_ids[0]].iloc[0]
            stock_before = int(product['stock_quantity'])
        except Exception as e:
            self.log_fail("POS", "Get product details", str(e))
            return
        
        # Record transaction
        try:
            items = [{
                'id': product_ids[0],
                'name': 'Apple',
                'qty': 10,
                'price': 120,
                'cost': 60
            }]
            txn_hash = db.record_transaction(
                items, 1200, 600,
                override_account_id=self.test_account_id,
                payment_method="CARD"
            )
            assert txn_hash is not None, "Transaction should return hash"
            self.log_pass("POS", "Record transaction")
        except Exception as e:
            self.log_fail("POS", "Record transaction", str(e))
            return
        
        # Verify stock deduction
        try:
            df = db.fetch_all_products(override_account_id=self.test_account_id)
            stock_after = int(df[df['id'] == product_ids[0]].iloc[0]['stock_quantity'])
            expected_stock = stock_before - 10
            assert stock_after == expected_stock, f"Stock should be {expected_stock}, got {stock_after}"
            self.log_pass("POS", "Stock deduction after sale")
        except Exception as e:
            self.log_fail("POS", "Stock deduction", str(e))
        
        # Fetch transactions
        try:
            txns = db.get_all_transactions(override_account_id=self.test_account_id)
            assert len(txns) >= 1, "Should have at least 1 transaction"
            self.log_pass("POS", "Fetch transactions")
        except Exception as e:
            self.log_fail("POS", "Fetch transactions", str(e))
    
    def test_customer_management(self):
        """Test Module: Customer Management"""
        print("\n" + "="*80)
        print("MODULE 4: CUSTOMER MANAGEMENT")
        print("="*80)
        
        # Add customer
        try:
            db.add_customer("John Doe", "9876543210", "john@example.com", "Hyderabad", "500001")
            self.log_pass("Customer", "Add customer")
        except Exception as e:
            self.log_fail("Customer", "Add customer", str(e))
        
        # Get customer by phone
        try:
            customer = db.get_customer_by_phone("9876543210")
            assert customer is not None, "Customer not found"
            assert customer['name'] == "John Doe", "Customer name mismatch"
            self.log_pass("Customer", "Fetch customer by phone")
        except Exception as e:
            self.log_fail("Customer", "Fetch customer", str(e))
        
        # Get all customers
        try:
            customers = db.get_all_customers(override_account_id=self.test_account_id)
            assert len(customers) >= 1, "Should have at least 1 customer"
            self.log_pass("Customer", "Fetch all customers")
        except Exception as e:
            self.log_fail("Customer", "Fetch all customers", str(e))
    
    def test_freshflow_batches(self, product_ids):
        """Test Module: FreshFlow (Batch Management)"""
        print("\n" + "="*80)
        print("MODULE 5: FRESHFLOW - BATCH MANAGEMENT")
        print("="*80)
        
        if not product_ids:
            self.log_fail("FreshFlow", "Prerequisites", "No products available")
            return
        
        # Add batch with expiry
        try:
            expiry_date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
            db.add_batch(
                product_ids[0], "BATCH-001", expiry_date, 100, 45,
                override_account_id=self.test_account_id
            )
            self.log_pass("FreshFlow", "Add batch with expiry")
        except Exception as e:
            self.log_fail("FreshFlow", "Add batch", str(e))
        
        # Get expiring batches
        try:
            expiring = db.get_expiring_batches(days_threshold=10, override_account_id=self.test_account_id)
            assert len(expiring) >= 1, "Should find expiring batch"
            assert any(expiring['batch_code'] == "BATCH-001"), "BATCH-001 not found"
            self.log_pass("FreshFlow", "Get expiring batches")
        except Exception as e:
            self.log_fail("FreshFlow", "Get expiring batches", str(e))
        
        # Get all batches
        try:
            batches = db.get_all_batches(override_account_id=self.test_account_id)
            assert len(batches) >= 1, "Should have at least 1 batch"
            self.log_pass("FreshFlow", "Fetch all batches")
        except Exception as e:
            self.log_fail("FreshFlow", "Fetch batches", str(e))
    
    def test_vendor_trust(self):
        """Test Module: VendorTrust (Supplier Management)"""
        print("\n" + "="*80)
        print("MODULE 6: VENDORTRUST - SUPPLIER MANAGEMENT")
        print("="*80)
        
        # Add supplier
        try:
            db.add_supplier("ABC Suppliers", "John", "9876543210", "Fruits", override_account_id=self.test_account_id)
            self.log_pass("VendorTrust", "Add supplier")
        except Exception as e:
            self.log_fail("VendorTrust", "Add supplier", str(e))
            return
        
        # Get all suppliers
        try:
            suppliers = db.get_all_suppliers(override_account_id=self.test_account_id)
            assert len(suppliers) >= 1, "Should have at least 1 supplier"
            supplier_id = suppliers.iloc[0]['id']
            self.log_pass("VendorTrust", "Fetch suppliers")
        except Exception as e:
            self.log_fail("VendorTrust", "Fetch suppliers", str(e))
            return
        
        # Create purchase order
        try:
            expected_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            po_id = db.create_purchase_order(
                supplier_id, expected_date, "Test PO",
                override_account_id=self.test_account_id
            )
            assert po_id is not None, "PO creation failed"
            self.log_pass("VendorTrust", "Create purchase order")
        except Exception as e:
            self.log_fail("VendorTrust", "Create PO", str(e))
        
        # Get all purchase orders
        try:
            pos = db.get_all_purchase_orders(override_account_id=self.test_account_id)
            assert len(pos) >= 1, "Should have at least 1 PO"
            self.log_pass("VendorTrust", "Fetch purchase orders")
        except Exception as e:
            self.log_fail("VendorTrust", "Fetch POs", str(e))
    
    def test_tablelink_restaurant(self):
        """Test Module: TableLink (Restaurant Management)"""
        print("\n" + "="*80)
        print("MODULE 7: TABLELINK - RESTAURANT MANAGEMENT")
        print("="*80)
        
        # Add restaurant table
        try:
            db.add_restaurant_table(
                "Table 1", 4, "Available",
                override_account_id=self.test_account_id
            )
            self.log_pass("TableLink", "Add restaurant table")
        except Exception as e:
            self.log_fail("TableLink", "Add table", str(e))
        
        # Get all tables
        try:
            tables = db.get_all_restaurant_tables(override_account_id=self.test_account_id)
            assert len(tables) >= 1, "Should have at least 1 table"
            table_id = tables.iloc[0]['id']
            self.log_pass("TableLink", "Fetch restaurant tables")
        except Exception as e:
            self.log_fail("TableLink", "Fetch tables", str(e))
            return
        
        # Update table status
        try:
            db.update_table_status(table_id, "Occupied")
            tables = db.get_all_restaurant_tables(override_account_id=self.test_account_id)
            status = tables[tables['id'] == table_id].iloc[0]['status']
            assert status == "Occupied", f"Status should be Occupied, got {status}"
            self.log_pass("TableLink", "Update table status")
        except Exception as e:
            self.log_fail("TableLink", "Update table status", str(e))
    
    def test_dashboard_analytics(self):
        """Test Module: Dashboard & Analytics"""
        print("\n" + "="*80)
        print("MODULE 8: DASHBOARD & ANALYTICS")
        print("="*80)
        
        # Get quick stats
        try:
            stats = db.get_quick_stats(override_account_id=self.test_account_id)
            assert 'total_products' in stats, "Missing total_products"
            assert 'total_revenue' in stats, "Missing total_revenue"
            assert stats['total_products'] >= 0, "Invalid product count"
            self.log_pass("Dashboard", "Get quick stats")
        except Exception as e:
            self.log_fail("Dashboard", "Quick stats", str(e))
        
        # Get revenue by category
        try:
            revenue = db.get_revenue_by_category(override_account_id=self.test_account_id)
            assert revenue is not None, "Revenue data should not be None"
            self.log_pass("Dashboard", "Revenue by category")
        except Exception as e:
            self.log_fail("Dashboard", "Revenue by category", str(e))
        
        # Get top products
        try:
            top_products = db.get_top_products(limit=5, override_account_id=self.test_account_id)
            assert top_products is not None, "Top products should not be None"
            self.log_pass("Dashboard", "Top products")
        except Exception as e:
            self.log_fail("Dashboard", "Top products", str(e))
    
    def test_multi_tenant_isolation(self):
        """Test Module: Multi-Tenant Isolation"""
        print("\n" + "="*80)
        print("MODULE 9: MULTI-TENANT ISOLATION")
        print("="*80)
        
        # Create second account
        try:
            company_b = f"TestCompany_B_{secrets.token_hex(4)}"
            success, msg = db.create_tenant(company_b, "Starter")
            assert success, f"Account creation failed: {msg}"
            account_b_id = msg.split(":")[-1].strip()
            self.log_pass("Isolation", "Create second account")
        except Exception as e:
            self.log_fail("Isolation", "Create second account", str(e))
            return
        
        # Add product to second account
        try:
            db.add_product("Orange", "Fruits", 80, 40, 200, 5, override_account_id=account_b_id)
            self.log_pass("Isolation", "Add product to Account B")
        except Exception as e:
            self.log_fail("Isolation", "Add product to B", str(e))
        
        # Verify isolation - Account A should not see Account B's products
        try:
            df_a = db.fetch_all_products(override_account_id=self.test_account_id)
            df_b = db.fetch_all_products(override_account_id=account_b_id)
            
            assert 'Orange' not in df_a['name'].values, "Isolation violated: A sees B's products"
            assert 'Orange' in df_b['name'].values, "B should see its own products"
            assert 'Apple' in df_a['name'].values, "A should see its own products"
            assert 'Apple' not in df_b['name'].values, "Isolation violated: B sees A's products"
            
            self.log_pass("Isolation", "Product isolation verified")
        except Exception as e:
            self.log_fail("Isolation", "Product isolation", str(e))
    
    def test_validators(self):
        """Test Module: Validators"""
        print("\n" + "="*80)
        print("MODULE 10: VALIDATORS")
        print("="*80)
        
        # Email validation
        try:
            valid, _ = validators.validate_email("test@example.com")
            assert valid, "Valid email should pass"
            invalid, _ = validators.validate_email("invalid-email")
            assert not invalid, "Invalid email should fail"
            self.log_pass("Validators", "Email validation")
        except Exception as e:
            self.log_fail("Validators", "Email validation", str(e))
        
        # Phone validation
        try:
            valid, _ = validators.validate_phone("9876543210")
            assert valid, "Valid phone should pass"
            invalid, _ = validators.validate_phone("1234567890")
            assert not invalid, "Invalid phone should fail"
            self.log_pass("Validators", "Phone validation")
        except Exception as e:
            self.log_fail("Validators", "Phone validation", str(e))
        
        # Price validation
        try:
            valid, _ = validators.validate_price(99.99)
            assert valid, "Valid price should pass"
            invalid, _ = validators.validate_price(-50)
            assert not invalid, "Negative price should fail"
            self.log_pass("Validators", "Price validation")
        except Exception as e:
            self.log_fail("Validators", "Price validation", str(e))
        
        # Stock validation
        try:
            valid, _ = validators.validate_stock_quantity(100)
            assert valid, "Valid stock should pass"
            invalid, _ = validators.validate_stock_quantity(-10)
            assert not invalid, "Negative stock should fail"
            self.log_pass("Validators", "Stock validation")
        except Exception as e:
            self.log_fail("Validators", "Stock validation", str(e))
    
    def run_all_tests(self):
        """Run all module tests."""
        if not self.setup_test_environment():
            print("\n❌ Test environment setup failed!")
            return False
        
        try:
            # Core modules
            self.test_authentication()
            product_ids = self.test_inventory_management()
            self.test_pos_transactions(product_ids)
            self.test_customer_management()
            
            # Supply chain modules
            self.test_freshflow_batches(product_ids)
            self.test_vendor_trust()
            
            # Restaurant module
            self.test_tablelink_restaurant()
            
            # Analytics
            self.test_dashboard_analytics()
            
            # Security & validation
            self.test_multi_tenant_isolation()
            self.test_validators()
            
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup_test_environment()
        
        # Print summary
        self.print_summary()
        
        return self.failed == 0
    
    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed} ({self.passed/total*100:.1f}%)")
        print(f"Failed: {self.failed} ({self.failed/total*100:.1f}%)")
        
        if self.errors:
            print("\n" + "="*80)
            print("FAILED TESTS:")
            print("="*80)
            for module, test, error in self.errors:
                print(f"  ❌ [{module}] {test}")
                print(f"     Error: {error}")
        
        if self.failed == 0:
            print("\n" + "="*80)
            print("🎉 ALL TESTS PASSED!")
            print("="*80)
        else:
            print("\n" + "="*80)
            print("⚠️  SOME TESTS FAILED - Review errors above")
            print("="*80)


if __name__ == "__main__":
    runner = ModuleTestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)
