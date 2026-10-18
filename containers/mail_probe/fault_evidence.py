def verify_fault_events(before, after, *, accepted, required=()):
    counters = set(before) | set(after) | {'smtp_accepted'} | set(required)
    delta = {name: after.get(name, 0) - before.get(name, 0) for name in counters}
    assert all(value >= 0 for value in delta.values()), delta
    assert delta['smtp_accepted'] == accepted, delta
    assert all(delta[name] >= 1 for name in required), delta
    return delta
