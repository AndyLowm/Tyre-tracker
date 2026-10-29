from app.services.tyre_service import calc_new_cost_price

def test_equal_quantities_gives_midpoint():
    cp = {"old_stock": 10, "new_stock": 10,
          "old_cost": 50.0, "new_cost": 60.0, "total": 20}
    assert calc_new_cost_price(cp) == 55.0


def test_rounds_to_two_decimals():
    # (3*10 + 4*11) / 7 = 10.5714... -> 10.57
    cp = {"old_stock": 3, "new_stock": 4,
          "old_cost": 10.0, "new_cost": 11.0, "total": 7}
    assert calc_new_cost_price(cp) == 10.57

def test_zero_total_keeps_old_cost():
    cp = {"old_stock": 0, "new_stock": 0,
          "old_cost": 50.0, "new_cost": 60.0, "total": 0}
    assert calc_new_cost_price(cp) == 50.0    

def test_weighted_towards_larger_quantity():
    # 30 tyres at 50 and 10 at 60: (1500 + 600) / 40 = 52.5
    cp = {"old_stock": 30, "new_stock": 10,
          "old_cost": 50.0, "new_cost": 60.0, "total": 40}
    assert calc_new_cost_price(cp) == 52.5