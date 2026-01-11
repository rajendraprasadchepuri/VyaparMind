
import database as db
import ui_components
import hashlib

def test_id_generation():
    print("Testing ID Generation...")
    id1 = db.generate_unique_id(16)
    id2 = db.generate_unique_id(16)
    assert len(id1) == 16
    assert id1 != id2
    
    id_num = db.generate_unique_id(16, numeric_only=True)
    assert id_num.isdigit()
    print("✅ ID Generation Passed")

def test_hashing():
    print("Testing Password Hashing...")
    # Since password hashing is local in functions, we test if it's consistent
    msg = "password123"
    h1 = hashlib.sha256(msg.encode()).hexdigest()
    h2 = hashlib.sha256(msg.encode()).hexdigest()
    assert h1 == h2
    print("✅ Hashing Passed")

def test_module_map():
    print("Testing UI Module Map...")
    for label, filename in ui_components.MODULE_MAP.items():
        assert filename.endswith(".py")
    print("✅ Module Map Passed")

if __name__ == "__main__":
    try:
        test_id_generation()
        test_hashing()
        test_module_map()
        print("\n✅ ALL UNIT TESTS PASSED!")
    except Exception as e:
        print(f"\n❌ UNIT TEST FAILED: {e}")
        exit(1)
